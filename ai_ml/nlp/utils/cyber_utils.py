"""
Utility functions for Cyber NLP Processor
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
import ipaddress
from collections import defaultdict


def validate_ip_address(ip: str) -> Tuple[bool, str]:
    """Validate IP address format and type"""
    try:
        addr = ipaddress.ip_address(ip)
        return True, str(addr.version)
    except ValueError:
        return False, "Invalid IP address"


def validate_domain(domain: str) -> Tuple[bool, Dict[str, Any]]:
    """Validate domain name format and extract information"""
    if not domain or len(domain) > 253:
        return False, {"error": "Domain too long or empty"}
    
    # Basic domain pattern validation
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not re.match(domain_pattern, domain):
        return False, {"error": "Invalid domain format"}
    
    # Parse domain parts
    parts = domain.split('.')
    if len(parts) < 2:
        return False, {"error": "Domain must have at least 2 parts"}
    
    domain_info = {
        "tld": parts[-1],
        "sld": parts[-2] if len(parts) >= 2 else "",
        "subdomain": ".".join(parts[:-2]) if len(parts) > 2 else "",
        "is_subdomain": len(parts) > 2,
        "parts_count": len(parts)
    }
    
    return True, domain_info


def validate_hash(hash_value: str, hash_type: str = "auto") -> Tuple[bool, Dict[str, Any]]:
    """Validate hash format based on type"""
    hash_value = hash_value.strip()
    
    if hash_type == "auto":
        if len(hash_value) == 32:
            hash_type = "md5"
        elif len(hash_value) == 40:
            hash_type = "sha1"
        elif len(hash_value) == 64:
            hash_type = "sha256"
        else:
            return False, {"error": "Unknown hash type"}
    
    patterns = {
        "md5": r'^[a-fA-F0-9]{32}$',
        "sha1": r'^[a-fA-F0-9]{40}$',
        "sha256": r'^[a-fA-F0-9]{64}$'
    }
    
    if hash_type not in patterns:
        return False, {"error": f"Unsupported hash type: {hash_type}"}
    
    if not re.match(patterns[hash_type], hash_value):
        return False, {"error": f"Invalid {hash_type} format"}
    
    return True, {"hash_type": hash_type, "length": len(hash_value)}


def validate_url(url: str) -> Tuple[bool, Dict[str, Any]]:
    """Validate URL format and extract information"""
    try:
        parsed = urlparse(url)
        
        if not parsed.scheme or not parsed.netloc:
            return False, {"error": "Invalid URL format"}
        
        url_info = {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "is_secure": parsed.scheme == "https",
            "has_query": bool(parsed.query),
            "has_fragment": bool(parsed.fragment)
        }
        
        # Validate domain part
        is_valid_domain, domain_info = validate_domain(parsed.netloc)
        if not is_valid_domain:
            url_info["domain_validation_error"] = domain_info.get("error", "Unknown error")
        
        url_info["domain_info"] = domain_info
        
        return True, url_info
        
    except Exception as e:
        return False, {"error": f"URL parsing failed: {str(e)}"}


def normalize_ioc(ioc_type: str, value: str) -> Optional[str]:
    """Normalize IOC values for consistency"""
    if not value:
        return None
    
    value = value.strip()
    
    if ioc_type in ["ipv4", "ipv6"]:
        # Normalize IP addresses
        try:
            ip = ipaddress.ip_address(value)
            return str(ip)
        except ValueError:
            return None
    
    elif ioc_type == "domain":
        # Normalize domains (lowercase, remove trailing dots)
        domain = value.lower().rstrip('.')
        # Remove protocols if present
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        return domain
    
    elif ioc_type == "url":
        # Normalize URLs
        parsed = urlparse(value)
        if parsed.netloc:
            return value.lower().rstrip('/')
        return None
    
    elif ioc_type in ["md5", "sha1", "sha256"]:
        # Normalize hashes (lowercase)
        return value.lower()
    
    elif ioc_type == "email":
        # Normalize emails (lowercase)
        return value.lower()
    
    else:
        # Return as-is for other types
        return value


def calculate_ioc_confidence(ioc_type: str, value: str, context: str = "") -> float:
    """Calculate confidence score for IOC detection"""
    base_confidence = 0.8
    
    # Increase confidence based on validation
    if ioc_type in ["ipv4", "ipv6", "md5", "sha1", "sha256", "email"]:
        is_valid, _ = {
            "ipv4": validate_ip_address(value),
            "ipv6": validate_ip_address(value),
            "md5": validate_hash(value, "md5"),
            "sha1": validate_hash(value, "sha1"),
            "sha256": validate_hash(value, "sha256"),
            "email": (re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value) is not None, {})
        }.get(ioc_type, (False, {}))
        
        if is_valid:
            base_confidence = 0.95
    
    # Adjust based on context
    security_keywords = [
        "malware", "threat", "attack", "suspicious", "malicious",
        "phishing", "spam", "botnet", "c2", "command", "control"
    ]
    
    context_lower = context.lower()
    keyword_matches = sum(1 for keyword in security_keywords if keyword in context_lower)
    
    confidence_adjustment = min(0.1 * keyword_matches, 0.2)
    
    final_confidence = min(base_confidence + confidence_adjustment, 1.0)
    
    return final_confidence


def extract_context_snippet(text: str, start: int, end: int, context_size: int = 100) -> str:
    """Extract context snippet around matched text"""
    text_start = max(0, start - context_size)
    text_end = min(len(text), end + context_size)
    
    snippet = text[text_start:text_end].strip()
    
    # Clean up whitespace
    snippet = re.sub(r'\s+', ' ', snippet)
    
    return snippet


def format_threat_intelligence_output(threat_intel: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Format threat intelligence output according to configuration"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_iocs": len(threat_intel.get("indicators", [])),
            "languages_detected": [threat_intel.get("language", "unknown")],
            "sentiment_score": threat_intel.get("sentiment_score", 0.0)
        }
    }
    
    if config.get("include_iocs", True):
        output["indicators"] = threat_intel.get("indicators", [])
    
    if config.get("include_entities", True):
        output["entities"] = threat_intel.get("entities", {})
    
    if config.get("include_threat_actors", True):
        output["threat_actors"] = threat_intel.get("threat_actors", [])
    
    if config.get("include_malware", True):
        output["malware_families"] = threat_intel.get("malware_families", [])
    
    if config.get("include_analysis_details", True):
        output["analysis_details"] = {
            "language": threat_intel.get("language"),
            "sentiment": threat_intel.get("sentiment_score"),
            "entity_counts": {
                entity_type: len(entities) 
                for entity_type, entities in threat_intel.get("entities", {}).items()
            }
        }
    
    return output


def create_ioc_summary(iocs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create summary of extracted IOCs"""
    if not iocs:
        return {"total_iocs": 0}
    
    # Count by type
    type_counts = defaultdict(int)
    source_counts = defaultdict(int)
    
    confidence_scores = []
    validation_results = []
    
    for ioc in iocs:
        ioc_type = ioc.get("type", "unknown")
        source = ioc.get("source", "unknown")
        confidence = ioc.get("confidence", 0.0)
        
        type_counts[ioc_type] += 1
        source_counts[source] += 1
        confidence_scores.append(confidence)
        
        # Validate IOC
        validation_result = {"type": ioc_type, "value": ioc.get("value", "")}
        
        if ioc_type in ["ipv4", "ipv6"]:
            is_valid, _ = validate_ip_address(ioc.get("value", ""))
            validation_result["valid"] = is_valid
        elif ioc_type == "domain":
            is_valid, _ = validate_domain(ioc.get("value", ""))
            validation_result["valid"] = is_valid
        elif ioc_type in ["md5", "sha1", "sha256"]:
            is_valid, _ = validate_hash(ioc.get("value", ""), ioc_type)
            validation_result["valid"] = is_valid
        else:
            validation_result["valid"] = True  # Assume valid for unknown types
        
        validation_results.append(validation_result)
    
    summary = {
        "total_iocs": len(iocs),
        "by_type": dict(type_counts),
        "by_source": dict(source_counts),
        "confidence_stats": {
            "min": min(confidence_scores),
            "max": max(confidence_scores),
            "avg": sum(confidence_scores) / len(confidence_scores)
        },
        "validation_results": {
            "valid": sum(1 for r in validation_results if r.get("valid", False)),
            "invalid": sum(1 for r in validation_results if not r.get("valid", False))
        },
        "top_types": sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    }
    
    return summary


def export_to_json(data: Any, filename: str, indent: int = 2) -> bool:
    """Export data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=indent, default=str)
        return True
    except Exception as e:
        logging.error(f"Failed to export to JSON: {e}")
        return False


def export_to_csv(data: List[Dict[str, Any]], filename: str) -> bool:
    """Export data to CSV file"""
    try:
        import pandas as pd
        
        if not data:
            return False
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        return True
    except Exception as e:
        logging.error(f"Failed to export to CSV: {e}")
        return False


def setup_logging(log_level: str = "INFO", log_format: str = None) -> logging.Logger:
    """Setup logging configuration"""
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('cyber_nlp.log')
        ]
    )
    
    return logging.getLogger(__name__)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Jaccard similarity"""
    if not text1 or not text2:
        return 0.0
    
    # Simple word-based similarity
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def batch_process_texts(texts: List[str], processor_func, batch_size: int = 100) -> List[Any]:
    """Process multiple texts in batches to avoid memory issues"""
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_results = [processor_func(text) for text in batch]
        results.extend(batch_results)
        
        # Log progress
        if (i + batch_size) % 1000 == 0:
            logging.info(f"Processed {i + batch_size} texts")
    
    return results


def deduplicate_iocs(iocs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate IOCs based on type and value"""
    seen = set()
    unique_iocs = []
    
    for ioc in iocs:
        key = (ioc.get("type"), normalize_ioc(ioc.get("type", ""), ioc.get("value", "")))
        if key not in seen:
            seen.add(key)
            unique_iocs.append(ioc)
    
    return unique_iocs


def generate_report(results: Dict[str, Any], report_type: str = "summary") -> str:
    """Generate human-readable report from analysis results"""
    report = []
    report.append(f"=== {report_type.title()} Report ===")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")
    
    if "ioc_summary" in results:
        ioc_summary = results["ioc_summary"]
        report.append("IOC Extraction Summary:")
        report.append(f"  Total IOCs: {ioc_summary.get('total_iocs', 0)}")
        
        if "by_type" in ioc_summary:
            report.append("  By Type:")
            for ioc_type, count in ioc_summary["by_type"].items():
                report.append(f"    {ioc_type}: {count}")
        report.append("")
    
    if "email_analysis" in results:
        email_result = results["email_analysis"]
        report.append("Email Analysis:")
        report.append(f"  Classification: {email_result.get('classification', 'unknown')}")
        report.append(f"  Confidence: {email_result.get('confidence', 0.0):.2f}")
        
        if "phishing_indicators" in email_result:
            indicators = email_result["phishing_indicators"]
            if indicators:
                report.append("  Phishing Indicators:")
                for indicator in indicators:
                    report.append(f"    - {indicator}")
        report.append("")
    
    if "threat_intelligence" in results:
        threat_intel = results["threat_intelligence"]
        report.append("Threat Intelligence:")
        report.append(f"  Language: {threat_intel.get('language', 'unknown')}")
        report.append(f"  Sentiment Score: {threat_intel.get('sentiment_score', 0.0):.2f}")
        
        if "threat_actors" in threat_intel and threat_intel["threat_actors"]:
            report.append("  Threat Actors:")
            for actor in threat_intel["threat_actors"]:
                report.append(f"    - {actor}")
        
        if "malware_families" in threat_intel and threat_intel["malware_families"]:
            report.append("  Malware Families:")
            for malware in threat_intel["malware_families"]:
                report.append(f"    - {malware}")
        report.append("")
    
    return "\n".join(report)
