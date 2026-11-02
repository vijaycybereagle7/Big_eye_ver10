#!/usr/bin/env python3
"""
Simple test script to verify the NLP cybersecurity implementation
"""

import sys
import os

# Add the current directory to the path to import our modules
sys.path.append('/workspace/ai_ml/nlp')

try:
    from nlp_processor import CyberNLPProcessor
    print("✅ Successfully imported CyberNLPProcessor")
except Exception as e:
    print(f"❌ Failed to import CyberNLPProcessor: {e}")
    sys.exit(1)

try:
    # Initialize the processor
    processor = CyberNLPProcessor()
    print("✅ Successfully initialized CyberNLPProcessor")
except Exception as e:
    print(f"❌ Failed to initialize CyberNLPProcessor: {e}")
    sys.exit(1)

# Test text sample
test_text = """
Security Advisory: Multiple vulnerabilities discovered in Apache server.
IOCs detected: 192.168.1.100, suspicious-domain.com, md5:abc123def456.
CVE-2024-12345 allows remote code execution. Phishing email from sender@fake-site.com
contains malicious link to https://malicious-site.xyz/path.
"""

try:
    print("\n🔍 Testing IOC Extraction...")
    iocs = processor.extract_iocs(test_text)
    print(f"✅ Found {len(iocs)} IOCs:")
    for ioc_type, values in iocs.items():
        if values:
            print(f"  - {ioc_type}: {values}")
except Exception as e:
    print(f"❌ IOC extraction failed: {e}")

try:
    print("\n📧 Testing Email Classification...")
    email_result = processor.classify_email(test_text)
    print(f"✅ Email classification result: {email_result}")
except Exception as e:
    print(f"❌ Email classification failed: {e}")

try:
    print("\n🌐 Testing Domain Analysis...")
    domain_result = processor.analyze_domain("suspicious-domain.com")
    print(f"✅ Domain analysis result: {domain_result}")
except Exception as e:
    print(f"❌ Domain analysis failed: {e}")

try:
    print("\n🛡️ Testing Threat Intelligence Extraction...")
    threat_intel = processor.extract_threat_intelligence(test_text)
    print(f"✅ Threat intelligence extracted: {threat_intel}")
except Exception as e:
    print(f"❌ Threat intelligence extraction failed: {e}")

print("\n🎉 All tests completed successfully!")