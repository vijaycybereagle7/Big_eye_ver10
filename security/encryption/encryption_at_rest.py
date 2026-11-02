"""
Encryption at Rest Implementation
Uses AES-256 encryption for data storage
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import json
from typing import Any, Optional


class DataEncryptionAtRest:
    """Handles encryption and decryption of data at rest"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption handler
        
        Args:
            master_key: Master encryption key. If None, generates from environment
        """
        self.backend = default_backend()
        
        if master_key:
            self.master_key = master_key.encode()
        else:
            # Generate from environment or use secure default
            key_env = os.environ.get('ENCRYPTION_MASTER_KEY')
            if key_env:
                self.master_key = key_env.encode()
            else:
                # In production, this should be from HSM or secure key management
                self.master_key = os.urandom(32)
        
        self.salt_length = 16
        self.key_length = 32  # AES-256
    
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derive encryption key from password and salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(password)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt data using AES-256
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Base64 encoded encrypted data with salt and IV
        """
        # Generate random salt and IV
        salt = os.urandom(self.salt_length)
        iv = os.urandom(16)
        
        # Derive key
        key = self._derive_key(self.master_key, salt)
        
        # Encrypt data
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Pad data to multiple of 16 bytes
        padded_data = self._pad(data.encode())
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine salt, iv, and ciphertext
        encrypted_package = salt + iv + ciphertext
        
        # Return base64 encoded
        return base64.b64encode(encrypted_package).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt AES-256 encrypted data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted plain text
        """
        try:
            # Decode base64
            encrypted_package = base64.b64decode(encrypted_data.encode())
            
            # Extract salt, iv, and ciphertext
            salt = encrypted_package[:self.salt_length]
            iv = encrypted_package[self.salt_length:self.salt_length + 16]
            ciphertext = encrypted_package[self.salt_length + 16:]
            
            # Derive key
            key = self._derive_key(self.master_key, salt)
            
            # Decrypt
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            data = self._unpad(padded_data)
            return data.decode()
            
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def _pad(self, data: bytes) -> bytes:
        """Add PKCS7 padding"""
        pad_length = 16 - (len(data) % 16)
        return data + bytes([pad_length] * pad_length)
    
    def _unpad(self, data: bytes) -> bytes:
        """Remove PKCS7 padding"""
        pad_length = data[-1]
        if pad_length > 16 or pad_length == 0:
            raise ValueError("Invalid padding")
        return data[:-pad_length]
    
    def encrypt_file(self, file_path: str) -> str:
        """
        Encrypt file contents
        
        Args:
            file_path: Path to file to encrypt
            
        Returns:
            Encrypted data as string
        """
        with open(file_path, 'r') as f:
            data = f.read()
        return self.encrypt(data)
    
    def decrypt_to_file(self, encrypted_data: str, output_path: str):
        """
        Decrypt data to file
        
        Args:
            encrypted_data: Encrypted data string
            output_path: Path to write decrypted data
        """
        decrypted = self.decrypt(encrypted_data)
        with open(output_path, 'w') as f:
            f.write(decrypted)
    
    def encrypt_database_field(self, value: Any) -> dict:
        """
        Encrypt database field value
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted package dictionary
        """
        data_str = json.dumps(value)
        encrypted = self.encrypt(data_str)
        return {
            'encrypted': True,
            'data': encrypted,
            'algorithm': 'AES-256-CBC',
            'key_derivation': 'PBKDF2-SHA256'
        }
    
    def decrypt_database_field(self, encrypted_package: dict) -> Any:
        """
        Decrypt database field value
        
        Args:
            encrypted_package: Encrypted package from database
            
        Returns:
            Decrypted value
        """
        if not encrypted_package.get('encrypted', False):
            return encrypted_package['data']
        
        decrypted_str = self.decrypt(encrypted_package['data'])
        return json.loads(decrypted_str)


class FieldLevelEncryption:
    """Field-level encryption for sensitive database columns"""
    
    def __init__(self, encryption_handler: DataEncryptionAtRest):
        self.encryption = encryption_handler
        
        # Define sensitive fields that need encryption
        self.sensitive_fields = {
            'users': ['email', 'phone', 'ssn', 'credit_card'],
            'orders': ['shipping_address', 'billing_address'],
            'payments': ['card_number', 'cvv', 'bank_account']
        }
    
    def should_encrypt_field(self, table: str, field: str) -> bool:
        """Check if field should be encrypted"""
        return field in self.sensitive_fields.get(table, [])
    
    def encrypt_insert_data(self, table: str, data: dict) -> dict:
        """Encrypt sensitive fields before database insert"""
        encrypted_data = data.copy()
        
        for field, value in data.items():
            if self.should_encrypt_field(table, field) and value:
                encrypted_data[field] = self.encryption.encrypt_database_field(value)
        
        return encrypted_data
    
    def decrypt_select_data(self, table: str, data: dict) -> dict:
        """Decrypt sensitive fields after database select"""
        decrypted_data = data.copy()
        
        for field, value in data.items():
            if isinstance(value, dict) and value.get('encrypted'):
                decrypted_data[field] = self.encryption.decrypt_database_field(value)
        
        return decrypted_data
