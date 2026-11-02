#!/usr/bin/env python3
"""Test script for Vercel Cybersecurity API."""

import requests
import json
import time
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8000"  # Change to your Vercel URL in production
API_KEY = "vercel-api-key-123"  # Update this to match your configured API key

# Test endpoints
ENDPOINTS = {
    "health": "/health",
    "root": "/",
    "validate_email": "/api/v1/validate/email",
    "validate_domain": "/api/v1/validate/domain",
    "validate_ip": "/api/v1/validate/ip",
    "validate_url": "/api/v1/validate/url",
    "reputation_ip": "/api/v1/reputation/ip/8.8.8.8",
    "threats_stats": "/api/v1/threats/stats",
}


def make_request(url: str, method: str = "GET", data: Optional[dict] = None) -> requests.Response:
    """Make API request with authentication."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def test_endpoint(name: str, url: str, method: str = "GET", data: Optional[dict] = None) -> bool:
    """Test a single endpoint."""
    print(f"\n🧪 Testing {name}...")
    print(f"   URL: {url}")
    print(f"   Method: {method}")
    
    start_time = time.time()
    response = make_request(url, method, data)
    end_time = time.time()
    
    if response is None:
        return False
    
    print(f"   Status: {response.status_code}")
    print(f"   Response Time: {(end_time - start_time)*1000:.2f}ms")
    
    try:
        response_data = response.json()
        if response.status_code == 200:
            print(f"   ✅ Success")
            if "success" in response_data:
                print(f"   Success Field: {response_data['success']}")
            return True
        else:
            print(f"   ❌ Error: {response_data.get('message', 'Unknown error')}")
            return False
    except json.JSONDecodeError:
        print(f"   ❌ Invalid JSON response")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Vercel Cybersecurity API Tests")
    print("=" * 50)
    
    # Test basic endpoints
    print("\n📋 Basic Endpoint Tests")
    print("-" * 30)
    
    tests = [
        ("Health Check", f"{API_BASE_URL}{ENDPOINTS['health']}"),
        ("Root Endpoint", f"{API_BASE_URL}{ENDPOINTS['root']}"),
        ("Threat Stats", f"{API_BASE_URL}{ENDPOINTS['threats_stats']}"),
        ("IP Reputation", f"{API_BASE_URL}{ENDPOINTS['reputation_ip']}"),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, url in tests:
        if test_endpoint(name, url):
            passed += 1
    
    # Test validation endpoints
    print("\n📧 Validation Endpoint Tests")
    print("-" * 30)
    
    validation_tests = [
        ("Email Validation", f"{API_BASE_URL}{ENDPOINTS['validate_email']}", "POST", {
            "email": "test@example.com",
            "verify_syntax": True,
            "check_disposable": True
        }),
        ("Domain Validation", f"{API_BASE_URL}{ENDPOINTS['validate_domain']}", "POST", {
            "domain": "google.com"
        }),
        ("IP Validation", f"{API_BASE_URL}{ENDPOINTS['validate_ip']}", "POST", {
            "ip": "8.8.8.8"
        }),
        ("URL Validation", f"{API_BASE_URL}{ENDPOINTS['validate_url']}", "POST", {
            "url": "https://google.com"
        }),
    ]
    
    for name, url, method, data in validation_tests:
        if test_endpoint(name, url, method, data):
            passed += 1
        total += 1
    
    # Test bulk validation
    print("\n📦 Bulk Validation Test")
    print("-" * 30)
    
    if test_endpoint(
        "Bulk Email Validation",
        f"{API_BASE_URL}/api/v1/validate/bulk",
        "POST",
        {
            "items": ["test1@example.com", "test2@gmail.com"],
            "validation_type": "email",
            "async_mode": False
        }
    ):
        passed += 1
    total += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Your API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
