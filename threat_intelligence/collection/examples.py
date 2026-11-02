#!/usr/bin/env python3
"""
Example usage of Threat Intelligence Collection Scripts
Demonstrates various scenarios and use cases
"""

import asyncio
import logging
import sys
import os
from typing import List

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from threat_intel_manager import ThreatIntelligenceManager
from base_collector import ThreatIntelligenceData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_single_indicator_lookup():
    """Example: Lookup threat intelligence for a single indicator"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Indicator Lookup")
    print("="*60)
    
    # Initialize manager
    manager = ThreatIntelligenceManager("threat_intel_config.json")
    
    try:
        # Test different indicator types
        test_cases = [
            ("8.8.8.8", "ip"),
            ("google.com", "domain"),
            ("https://www.google.com/search?q=test", "url"),
            ("d41d8cd98f00b204e9800998ecf8427e", "hash")
        ]
        
        for indicator, ind_type in test_cases:
            print(f"\nLooking up {ind_type}: {indicator}")
            print("-" * 50)
            
            # Use a subset of collectors for faster demo
            collectors = ["virustotal", "urlhaus", "threatfox"]
            
            results = await manager.lookup_indicator(
                indicator=indicator,
                indicator_type=ind_type,
                collectors=collectors,
                max_collectors=3
            )
            
            # Display results
            print(f"Found {len(results)} results from {len(collectors)} collectors:")
            
            for result in results:
                print(f"  Source: {result.source}")
                print(f"  Confidence: {result.confidence}")
                print(f"  Score: {result.score}")
                print(f"  Tags: {result.tags[:3]}...")  # First 3 tags
                print()
    
    finally:
        await manager.close()


async def example_bulk_lookup():
    """Example: Bulk lookup multiple indicators"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Bulk Indicator Lookup")
    print("="*60)
    
    manager = ThreatIntelligenceManager("threat_intel_config.json")
    
    try:
        # Sample indicators for testing
        indicators = [
            "8.8.8.8",
            "1.1.1.1", 
            "google.com",
            "microsoft.com",
            "d41d8cd98f00b204e9800998ecf8427e",
            "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        ]
        
        print(f"Looking up {len(indicators)} indicators...")
        
        # Use only fast public APIs for demo
        collectors = ["urlhaus", "malwarebazaar", "threatfox"]
        
        results = await manager.bulk_lookup(
            indicators=indicators,
            indicator_type="auto",
            collectors=collectors,
            delay_between_requests=2.0
        )
        
        # Print summary
        manager.print_summary(results)
        
        # Save results
        manager.save_results(results, "bulk_lookup_results.json")
        print(f"\nResults saved to bulk_lookup_results.json")
    
    finally:
        await manager.close()


async def example_specific_collector():
    """Example: Use a specific collector directly"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Specific Collector Usage")
    print("="*60)
    
    from urlhaus_collector import URLhausCollector
    
    # URLhaus doesn't require API key
    async with URLhausCollector() as collector:
        print("Using URLhaus collector directly...")
        
        # Recent malware samples
        print("\nGetting recent malware samples:")
        print("-" * 40)
        
        recent_samples = await collector.get_recent_malware(limit=5)
        
        for sample in recent_samples:
            print(f"Hash: {sample.indicator}")
            print(f"Type: {sample.indicator_type}")
            print(f"Confidence: {sample.confidence}")
            print(f"Tags: {sample.tags}")
            print()


async def example_custom_analysis():
    """Example: Custom analysis of threat intelligence data"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom Analysis")
    print("="*60)
    
    manager = ThreatIntelligenceManager("threat_intel_config.json")
    
    try:
        # Test indicators with different threat levels
        test_indicators = [
            "8.8.8.8",  # Google's DNS (likely clean)
            "malware-example.com",  # Hypothetical malware domain
            "d41d8cd98f00b204e9800998ecf8427e",  # Empty file hash
        ]
        
        results = await manager.bulk_lookup(
            indicators=test_indicators,
            collectors=["virustotal", "urlhaus", "abuseipdb"],
            delay_between_requests=1.0
        )
        
        # Custom analysis
        print("Custom Analysis Results:")
        print("-" * 40)
        
        # High confidence threats
        high_confidence = [r for r in results if r.confidence and r.confidence >= 0.8]
        print(f"High confidence threats: {len(high_confidence)}")
        
        # Threats by source
        source_counts = {}
        for result in results:
            source = result.source
            if source not in source_counts:
                source_counts[source] = 0
            source_counts[source] += 1
        
        print("\nResults by source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count}")
        
        # Suspicious indicators
        suspicious = [r for r in results if r.confidence and r.confidence > 0.5]
        print(f"\nSuspicious indicators: {len(suspicious)}")
        
        if suspicious:
            print("\nTop suspicious indicators:")
            suspicious.sort(key=lambda x: x.confidence or 0, reverse=True)
            for result in suspicious[:3]:
                print(f"  {result.indicator} (confidence: {result.confidence:.2f})")
    
    finally:
        await manager.close()


async def example_rate_limited_collection():
    """Example: Rate-limited collection with multiple collectors"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Rate-Limited Collection")
    print("="*60)
    
    manager = ThreatIntelligenceManager("threat_intel_config.json")
    
    try:
        # Use all available collectors with proper rate limiting
        available_collectors = manager.get_available_collectors()
        print(f"Available collectors: {available_collectors}")
        
        # Single indicator, multiple collectors with staggered requests
        test_ip = "192.0.2.1"  # Example IP
        print(f"\nLooking up IP {test_ip} with all available collectors...")
        
        results = await manager.lookup_indicator(
            indicator=test_ip,
            indicator_type="ip",
            collectors=available_collectors,
            max_collectors=10
        )
        
        # Analyze results by source
        print("\nResults by source:")
        source_results = {}
        for result in results:
            source = result.source
            if source not in source_results:
                source_results[source] = []
            source_results[source].append(result)
        
        for source, source_data in source_results.items():
            avg_confidence = sum(r.confidence or 0 for r in source_data) / len(source_data)
            print(f"  {source}: {len(source_data)} results, avg confidence: {avg_confidence:.2f}")
    
    finally:
        await manager.close()


async def main():
    """Run all examples"""
    print("Threat Intelligence Collection Examples")
    print("=====================================")
    
    # Check if config file exists
    config_file = "threat_intel_config.json"
    if not os.path.exists(config_file):
        print(f"Warning: {config_file} not found.")
        print("Please copy threat_intel_config.json.template to threat_intel_config.json")
        print("and add your API keys for full functionality.")
        print("\nContinuing with limited functionality (public APIs only)...")
    
    examples = [
        example_single_indicator_lookup,
        example_bulk_lookup,
        example_specific_collector,
        example_custom_analysis,
        example_rate_limited_collection
    ]
    
    for example_func in examples:
        try:
            await example_func()
            print("\n" + "="*60)
            print(f"Example completed: {example_func.__name__}")
            print("="*60)
        except Exception as e:
            print(f"\nError in {example_func.__name__}: {e}")
            logger.exception(f"Error in example {example_func.__name__}")
    
    print("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main())