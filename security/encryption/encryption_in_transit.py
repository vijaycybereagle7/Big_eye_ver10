"""
Encryption In Transit Implementation
Handles TLS/SSL encryption for data in transit
"""

import ssl
import socket
import http.client
import urllib.request
import urllib.error
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import json
from typing import Dict, Optional, Any
import os


class DataEncryptionInTransit:
    """Handles encryption for data in transit using TLS/SSL"""
    
    def __init__(self):
        self.ssl_context = self._create_ssl_context()
        self.client_cert_path = os.environ.get('CLIENT_CERT_PATH')
        self.client_key_path = os.environ.get('CLIENT_KEY_PATH')
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create secure SSL context"""
        context = ssl.create_default_context()
        
        # Minimum TLS 1.2
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Security settings
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        # Disable weak ciphers
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Load client certificates if available
        if self.client_cert_path and self.client_key_path:
            context.load_cert_chain(self.client_cert_path, self.client_key_path)
        
        return context
    
    def create_secure_https_connection(self, host: str, port: int = 443) -> http.client.HTTPSConnection:
        """
        Create secure HTTPS connection
        
        Args:
            host: Hostname
            port: Port number (default 443)
            
        Returns:
            HTTPS connection with SSL
        """
        return http.client.HTTPSConnection(host, port, context=self.ssl_context)
    
    def create_secure_socket(self, host: str, port: int) -> socket.socket:
        """
        Create secure SSL socket
        
        Args:
            host: Hostname
            port: Port number
            
        Returns:
            SSL socket
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = self.ssl_context.wrap_socket(sock, server_hostname=host)
        return ssl_sock
    
    def secure_api_request(self, url: str, method: str = 'GET', 
                          headers: Optional[Dict] = None, 
                          data: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Make secure API request with TLS encryption
        
        Args:
            url: Request URL
            method: HTTP method
            headers: Request headers
            data: Request body data
            
        Returns:
            Response data
        """
        try:
            req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
            
            with urllib.request.urlopen(req, context=self.ssl_context) as response:
                response_data = response.read()
                
                # Parse JSON response
                try:
                    return json.loads(response_data.decode())
                except json.JSONDecodeError:
                    return {'data': response_data.decode(), 'status_code': response.status}
                    
        except urllib.error.URLError as e:
            raise ConnectionError(f"Secure request failed: {str(e)}")
    
    def encrypt_message(self, message: str, public_key_path: str) -> str:
        """
        Encrypt message using RSA public key
        
        Args:
            message: Message to encrypt
            public_key_path: Path to public key file
            
        Returns:
            Base64 encoded encrypted message
        """
        # Load public key
        with open(public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(), 
                backend=default_backend()
            )
        
        # Encrypt message
        encrypted = public_key.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted).decode()
    
    def decrypt_message(self, encrypted_message: str, private_key_path: str) -> str:
        """
        Decrypt message using RSA private key
        
        Args:
            encrypted_message: Base64 encoded encrypted message
            private_key_path: Path to private key file
            
        Returns:
            Decrypted message
        """
        # Load private key
        with open(private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        
        # Decrypt message
        encrypted_bytes = base64.b64decode(encrypted_message.encode())
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted.decode()
    
    def verify_certificate_chain(self, cert_path: str) -> Dict[str, Any]:
        """
        Verify SSL certificate
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            Certificate information
        """
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
        
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        
        return {
            'subject': dict(cert.subject),
            'issuer': dict(cert.issuer),
            'not_valid_before': cert.not_valid_before.isoformat(),
            'not_valid_after': cert.not_valid_after.isoformat(),
            'serial_number': cert.serial_number,
            'signature_algorithm': cert.signature_algorithm_oid._name
        }
    
    def generate_key_pair(self, key_size: int = 2048) -> tuple:
        """
        Generate RSA key pair for asymmetric encryption
        
        Args:
            key_size: Key size in bits (default 2048)
            
        Returns:
            Tuple of (private_key, public_key) in PEM format
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem


class SecureSocketHandler:
    """Handler for secure socket communications"""
    
    def __init__(self, encryption_handler: DataEncryptionInTransit):
        self.encryption = encryption_handler
        
    def send_secure_data(self, host: str, port: int, data: str) -> str:
        """
        Send data through secure socket
        
        Args:
            host: Target host
            port: Target port
            data: Data to send
            
        Returns:
            Response from server
        """
        try:
            with self.encryption.create_secure_socket(host, port) as ssl_sock:
                ssl_sock.connect((host, port))
                
                # Send data with newline terminator
                ssl_sock.sendall((data + '\n').encode())
                
                # Receive response
                response = ssl_sock.recv(4096).decode().strip()
                return response
                
        except Exception as e:
            raise ConnectionError(f"Secure socket communication failed: {str(e)}")
    
    def create_secure_echo_server(self, host: str, port: int):
        """
        Create simple secure echo server
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((host, port))
            server_socket.listen(5)
            print(f"Secure server listening on {host}:{port}")
            
            while True:
                client_socket, addr = server_socket.accept()
                
                # Wrap with SSL
                ssl_client = self.encryption.ssl_context.wrap_socket(
                    client_socket, 
                    server_side=True
                )
                
                # Handle client
                try:
                    data = ssl_client.recv(1024).decode()
                    if data:
                        ssl_client.sendall(f"Echo: {data}".encode())
                finally:
                    ssl_client.close()
                    
        except KeyboardInterrupt:
            print("Server stopped")
        finally:
            server_socket.close()


class CertificateManager:
    """Manage SSL certificates and keys"""
    
    def __init__(self, cert_dir: str = '/workspace/security/encryption/certs'):
        self.cert_dir = cert_dir
        os.makedirs(cert_dir, exist_ok=True)
        
    def generate_self_signed_cert(self, hostname: str) -> tuple:
        """
        Generate self-signed certificate for development
        
        Args:
            hostname: Hostname for certificate
            
        Returns:
            Tuple of (cert_path, key_path)
        """
        from cryptography.x509.oid import NameOID
        from datetime import datetime, timedelta
        
        # Generate key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Organization"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(hostname),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Save files
        cert_path = os.path.join(self.cert_dir, f"{hostname}.crt")
        key_path = os.path.join(self.cert_dir, f"{hostname}.key")
        
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        return cert_path, key_path
