"""Utility functions for the cybersecurity validation API."""

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import ipaddress
import urllib.parse
import logging

logger = logging.getLogger(__name__)


def validate_email_format(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_domain_format(domain: str) -> bool:
    """Validate domain format."""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.?$'
    return bool(re.match(pattern, domain.lower()))


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format (IPv4 and IPv6)."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_url_format(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_domain(domain: str) -> str:
    """Normalize domain name."""
    domain = domain.lower().strip()
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain.rstrip('.')


def extract_domain_from_email(email: str) -> Optional[str]:
    """Extract domain from email address."""
    if '@' in email:
        return normalize_domain(email.split('@')[1])
    return None


def calculate_hash(value: str, algorithm: str = 'sha256') -> str:
    """Calculate hash of a value."""
    hasher = hashlib.new(algorithm)
    hasher.update(value.encode('utf-8'))
    return hasher.hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Strip leading/trailing underscores and dots
    return sanitized.strip('_.')


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize object to JSON with default handling."""
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')
    
    return json.dumps(obj, default=json_serializer, **kwargs)


def parse_user_agent(user_agent: str) -> Dict[str, Any]:
    """Parse user agent string to extract browser and system information."""
    # This is a simplified parser - in production, use a proper user agent parser
    result = {
        'browser': 'Unknown',
        'version': 'Unknown',
        'os': 'Unknown',
        'is_mobile': False,
        'is_bot': False
    }
    
    user_agent_lower = user_agent.lower()
    
    # Detect bot
    bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
    if any(indicator in user_agent_lower for indicator in bot_indicators):
        result['is_bot'] = True
    
    # Detect mobile
    mobile_indicators = ['mobile', 'android', 'iphone', 'ipad']
    if any(indicator in user_agent_lower for indicator in mobile_indicators):
        result['is_mobile'] = True
    
    # Detect browser (simplified)
    if 'chrome' in user_agent_lower:
        result['browser'] = 'Chrome'
    elif 'firefox' in user_agent_lower:
        result['browser'] = 'Firefox'
    elif 'safari' in user_agent_lower:
        result['browser'] = 'Safari'
    elif 'edge' in user_agent_lower:
        result['browser'] = 'Edge'
    
    return result


def calculate_confidence_score(factors: Dict[str, float]) -> float:
    """Calculate confidence score from multiple factors."""
    if not factors:
        return 0.5
    
    # Weight the factors
    weights = {
        'syntax': 0.2,
        'domain': 0.3,
        'dns': 0.3,
        'reputation': 0.2
    }
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for factor, score in factors.items():
        weight = weights.get(factor, 0.1)
        weighted_sum += score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.5


def extract_ip_ranges(ip_list: List[str]) -> List[Dict[str, Union[str, int]]]:
    """Extract and group IP addresses into networks."""
    networks = {}
    
    for ip in ip_list:
        try:
            network = ipaddress.ip_network(ip, strict=False)
            network_str = str(network)
            
            if network_str not in networks:
                networks[network_str] = {
                    'network': network_str,
                    'count': 0,
                    'ips': []
                }
            
            networks[network_str]['count'] += 1
            networks[network_str]['ips'].append(ip)
            
        except ValueError as e:
            logger.warning(f"Invalid IP address: {ip} - {e}")
    
    return list(networks.values())


def generate_cache_key(prefix: str, *args) -> str:
    """Generate cache key from prefix and arguments."""
    key_parts = [prefix]
    for arg in args:
        key_parts.append(str(arg))
    
    key_string = ':'.join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def time_based_key(time_value: datetime, prefix: str) -> str:
    """Generate time-based cache key."""
    time_key = time_value.strftime('%Y-%m-%d-%H')
    return generate_cache_key(prefix, time_key)


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to specified length with optional suffix."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception:
        return None


def extract_tld(domain: str) -> Optional[str]:
    """Extract top-level domain from domain."""
    try:
        parts = domain.lower().split('.')
        if len(parts) >= 2:
            return parts[-1]
        return None
    except Exception:
        return None


def is_private_ip(ip: str) -> bool:
    """Check if IP address is private/internal."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False


def get_timezone_aware_datetime(dt: datetime = None) -> datetime:
    """Get timezone-aware datetime."""
    if dt is None:
        dt = datetime.utcnow()
    
    # Make datetime timezone aware (UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    
    return dt


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_api_key_format(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key:
        return False
    
    # Check length
    if len(api_key) < 10 or len(api_key) > 128:
        return False
    
    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
        return False
    
    return True


def mask_sensitive_data(data: str, mask_char: str = '*', keep_start: int = 4, keep_end: int = 4) -> str:
    """Mask sensitive data like API keys, passwords, etc."""
    if len(data) <= keep_start + keep_end:
        return mask_char * len(data)
    
    masked = data[:keep_start] + mask_char * (len(data) - keep_start - keep_end) + data[-keep_end:]
    return masked


def rate_limit_key(api_key: str, endpoint: str, window_start: str) -> str:
    """Generate rate limiting key."""
    return generate_cache_key("rate_limit", api_key, endpoint, window_start)


def get_client_ip(request) -> str:
    """Extract client IP from request."""
    # Check for forwarded headers first (for load balancers, proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


def batch_process(items: List[Any], batch_size: int = 100) -> List[List[Any]]:
    """Split list into batches of specified size."""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries into one."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def safe_int(value: Any, default: int = 0, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """Safely convert value to integer with bounds checking."""
    try:
        result = int(value)
        
        if min_val is not None and result < min_val:
            result = min_val
        elif max_val is not None and result > max_val:
            result = max_val
        
        return result
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0, min_val: Optional[float] = None, max_val: Optional[float] = None) -> float:
    """Safely convert value to float with bounds checking."""
    try:
        result = float(value)
        
        if min_val is not None and result < min_val:
            result = min_val
        elif max_val is not None and result > max_val:
            result = max_val
        
        return result
    except (ValueError, TypeError):
        return default