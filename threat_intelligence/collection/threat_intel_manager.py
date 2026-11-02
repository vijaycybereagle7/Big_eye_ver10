#!/usr/bin/env python3
"""
Threat Intelligence Collection Manager
Unified interface for all threat intelligence collectors
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import argparse

from base_collector import ThreatIntelligenceData, save_results_to_file

# Import all collectors
from virustotal_collector import VirusTotalCollector
from abuseipdb_collector import AbuseIPDBCollector
from safebrowsing_collector import GoogleSafeBrowsingCollector
from otx_collector import AlienVaultOTXCollector
from shodan_collector import ShodanCollector
from securitytrails_collector import SecurityTrailsCollector
from urlhaus_collector import URLhausCollector
from phishtank_collector import PhishTankCollector
from malwarebazaar_collector import MalwareBazaarCollector
from threatfox_collector import ThreatFoxCollector
from circl_hashlookup_collector import CIRCLHashlookupCollector
from spamhaus_collector import SpamhausCollector
from greynoise_collector import GreyNoiseCollector

logger = logging.getLogger(__name__)


class ThreatIntelligenceManager:
    """Manager for all threat intelligence collectors"""
    
    def __init__(self, config_file: str = "threat_intel_config.json"):
        self.config = self._load_config(config_file)
        self.collectors = {}
        self.results = []
        
        # Initialize collectors based on config
        self._initialize_collectors()
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "virustotal_api_key": None,
            "abuseipdb_api_key": None,
            "google_safebrowsing_api_key": None,
            "otx_api_key": None,
            "shodan_api_key": None,
            "securitytrails_api_key": None,
            "phishtank_app_key": None,
            "threatfox_api_key": None,  # Not required for public API
            "circl_username": None,
            "circl_password": None,
            "greynoise_api_key": None,
            "malwarebazaar_api_key": None,  # Not required for public API
            "urlhaus_api_key": None,  # Not required for public API
            "spamhaus_api_key": None,  # Not required for public API
            "rate_limit_delay": 1.0,  # seconds between requests
            "output_directory": "threat_intel_results"
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load config file {config_file}: {e}. Using defaults.")
        
        return default_config
    
    def _initialize_collectors(self):
        """Initialize all collectors based on configuration"""
        collectors_info = [
            ("virustotal", "VirusTotal", self.config.get("virustotal_api_key"), VirusTotalCollector),
            ("abuseipdb", "AbuseIPDB", self.config.get("abuseipdb_api_key"), AbuseIPDBCollector),
            ("safebrowsing", "GoogleSafeBrowsing", self.config.get("google_safebrowsing_api_key"), GoogleSafeBrowsingCollector),
            ("otx", "AlienVaultOTX", self.config.get("otx_api_key"), AlienVaultOTXCollector),
            ("shodan", "Shodan", self.config.get("shodan_api_key"), ShodanCollector),
            ("securitytrails", "SecurityTrails", self.config.get("securitytrails_api_key"), SecurityTrailsCollector),
            ("urlhaus", "URLhaus", self.config.get("urlhaus_api_key"), URLhausCollector),  # No API key needed
            ("phishtank", "PhishTank", self.config.get("phishtank_app_key"), PhishTankCollector),
            ("malwarebazaar", "MalwareBazaar", self.config.get("malwarebazaar_api_key"), MalwareBazaarCollector),  # No API key needed
            ("threatfox", "ThreatFox", self.config.get("threatfox_api_key"), ThreatFoxCollector),  # No API key needed
            ("circl", "CIRCL", (self.config.get("circl_username"), self.config.get("circl_password")), CIRCLHashlookupCollector),
            ("spamhaus", "Spamhaus", self.config.get("spamhaus_api_key"), SpamhausCollector),  # No API key needed
            ("greynoise", "GreyNoise", self.config.get("greynoise_api_key"), GreyNoiseCollector),
        ]
        
        for key, name, credential, collector_class in collectors_info:
            try:
                if credential:
                    if isinstance(credential, tuple):
                        # For CIRCL which needs username and password
                        collector = collector_class(credential[0], credential[1])
                    else:
                        collector = collector_class(credential)
                    self.collectors[key] = collector
                    logger.info(f"Initialized {name} collector")
                else:
                    logger.warning(f"No credentials provided for {name} collector")
            except Exception as e:
                logger.error(f"Failed to initialize {name} collector: {e}")
    
    def get_available_collectors(self) -> List[str]:
        """Get list of available collectors"""
        return list(self.collectors.keys())
    
    async def lookup_indicator(
        self, 
        indicator: str, 
        indicator_type: str = "auto",
        collectors: List[str] = None,
        max_collectors: int = None
    ) -> List[ThreatIntelligenceData]:
        """Lookup threat intelligence for an indicator"""
        if not collectors:
            collectors = list(self.collectors.keys())
        
        if max_collectors:
            collectors = collectors[:max_collectors]
        
        # Determine indicator type if auto
        if indicator_type == "auto":
            indicator_type = self._detect_indicator_type(indicator)
        
        logger.info(f"Looking up {indicator_type} indicator: {indicator}")
        logger.info(f"Using collectors: {collectors}")
        
        tasks = []
        task_collectors = []
        
        # Create lookup tasks for each collector
        for collector_key in collectors:
            if collector_key not in self.collectors:
                logger.warning(f"Collector {collector_key} not available")
                continue
            
            collector = self.collectors[collector_key]
            
            if indicator_type == "ip":
                task = collector.lookup_ip(indicator)
            elif indicator_type == "domain":
                task = collector.lookup_domain(indicator)
            elif indicator_type == "url":
                task = collector.lookup_url(indicator)
            elif indicator_type == "hash":
                task = collector.lookup_hash(indicator)
            else:
                logger.warning(f"Unknown indicator type: {indicator_type}")
                continue
            
            tasks.append(task)
            task_collectors.append(collector_key)
        
        # Execute all lookups concurrently
        results = []
        if tasks:
            try:
                all_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for collector_key, result in zip(task_collectors, all_results):
                    
                    if isinstance(result, Exception):
                        logger.error(f"Error in {collector_key}: {result}")
                        continue
                    
                    if isinstance(result, list):
                        results.extend(result)
                    else:
                        results.append(result)
                        
            except Exception as e:
                logger.error(f"Error during concurrent lookup: {e}")
        
        # Store results
        self.results.extend(results)
        
        return results
    
    def _detect_indicator_type(self, indicator: str) -> str:
        """Automatically detect indicator type"""
        # Simple heuristic-based detection
        
        # Check for hash patterns
        if len(indicator) in [32, 40, 64, 128] and all(c in '0123456789abcdefABCDEF' for c in indicator.replace('-', '')):
            return "hash"
        
        # Check for IP address
        if indicator.count('.') == 3 and all(part.isdigit() and 0 <= int(part) <= 255 for part in indicator.split('.')):
            return "ip"
        
        # Check for URL
        if indicator.startswith(('http://', 'https://')):
            return "url"
        
        # Check for domain (contains dots and no spaces)
        if '.' in indicator and ' ' not in indicator and not indicator.count('.') == 3:
            return "domain"
        
        # Default to domain
        return "domain"
    
    async def bulk_lookup(
        self, 
        indicators: List[str], 
        indicator_type: str = "auto",
        collectors: List[str] = None,
        delay_between_requests: float = None
    ) -> List[ThreatIntelligenceData]:
        """Bulk lookup multiple indicators"""
        if delay_between_requests is None:
            delay_between_requests = self.config.get("rate_limit_delay", 1.0)
        
        all_results = []
        
        for i, indicator in enumerate(indicators):
            logger.info(f"Processing indicator {i+1}/{len(indicators)}: {indicator}")
            
            try:
                results = await self.lookup_indicator(indicator, indicator_type, collectors)
                all_results.extend(results)
                
                # Add delay between requests to respect rate limits
                if i < len(indicators) - 1:
                    await asyncio.sleep(delay_between_requests)
                    
            except Exception as e:
                logger.error(f"Error processing indicator {indicator}: {e}")
                continue
        
        return all_results
    
    def save_results(
        self, 
        results: List[ThreatIntelligenceData] = None,
        filename: str = None,
        output_dir: str = None
    ):
        """Save results to file"""
        if results is None:
            results = self.results
        
        if output_dir is None:
            output_dir = self.config.get("output_directory", "threat_intel_results")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"threat_intel_results_{timestamp}.json"
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            save_results_to_file(results, filepath)
            logger.info(f"Results saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def get_summary(self, results: List[ThreatIntelligenceData] = None) -> Dict[str, Any]:
        """Get summary of threat intelligence results"""
        if results is None:
            results = self.results
        
        summary = {
            "total_results": len(results),
            "by_source": {},
            "by_indicator_type": {},
            "by_confidence": {
                "high": 0,      # confidence >= 0.8
                "medium": 0,    # 0.5 <= confidence < 0.8
                "low": 0,       # confidence < 0.5
                "unknown": 0    # no confidence score
            },
            "by_indicator": {}
        }
        
        for result in results:
            # Count by source
            source = result.source
            if source not in summary["by_source"]:
                summary["by_source"][source] = 0
            summary["by_source"][source] += 1
            
            # Count by indicator type
            ind_type = result.indicator_type
            if ind_type not in summary["by_indicator_type"]:
                summary["by_indicator_type"][ind_type] = 0
            summary["by_indicator_type"][ind_type] += 1
            
            # Count by confidence
            if result.confidence is None:
                summary["by_confidence"]["unknown"] += 1
            elif result.confidence >= 0.8:
                summary["by_confidence"]["high"] += 1
            elif result.confidence >= 0.5:
                summary["by_confidence"]["medium"] += 1
            else:
                summary["by_confidence"]["low"] += 1
            
            # Count by indicator
            indicator = result.indicator
            if indicator not in summary["by_indicator"]:
                summary["by_indicator"][indicator] = 0
            summary["by_indicator"][indicator] += 1
        
        return summary
    
    def print_summary(self, results: List[ThreatIntelligenceData] = None):
        """Print summary of results"""
        summary = self.get_summary(results)
        
        print("\n" + "="*50)
        print("THREAT INTELLIGENCE COLLECTION SUMMARY")
        print("="*50)
        print(f"Total results: {summary['total_results']}")
        print()
        
        print("By Source:")
        for source, count in summary['by_source'].items():
            print(f"  {source}: {count}")
        print()
        
        print("By Indicator Type:")
        for ind_type, count in summary['by_indicator_type'].items():
            print(f"  {ind_type}: {count}")
        print()
        
        print("By Confidence Level:")
        for conf_level, count in summary['by_confidence'].items():
            print(f"  {conf_level}: {count}")
        print()
        
        print("Top Indicators:")
        sorted_indicators = sorted(summary['by_indicator'].items(), key=lambda x: x[1], reverse=True)
        for indicator, count in sorted_indicators[:10]:  # Top 10
            print(f"  {indicator}: {count}")
        print()
    
    async def close(self):
        """Close all collectors"""
        for collector in self.collectors.values():
            await collector.close()


async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Threat Intelligence Collection Manager")
    parser.add_argument("--indicator", type=str, help="Single indicator to lookup")
    parser.add_argument("--file", type=str, help="File containing indicators (one per line)")
    parser.add_argument("--type", type=str, choices=["ip", "domain", "url", "hash", "auto"], 
                       default="auto", help="Indicator type")
    parser.add_argument("--collectors", type=str, nargs="+", 
                       help="Specific collectors to use")
    parser.add_argument("--max-collectors", type=int, help="Maximum number of collectors to use")
    parser.add_argument("--output", type=str, help="Output filename")
    parser.add_argument("--output-dir", type=str, default="threat_intel_results", 
                       help="Output directory")
    parser.add_argument("--delay", type=float, default=1.0, 
                       help="Delay between requests (seconds)")
    parser.add_argument("--config", type=str, default="threat_intel_config.json",
                       help="Configuration file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize manager
    manager = ThreatIntelligenceManager(args.config)
    
    try:
        # Get indicators
        indicators = []
        
        if args.indicator:
            indicators = [args.indicator]
        elif args.file:
            if os.path.exists(args.file):
                with open(args.file, 'r') as f:
                    indicators = [line.strip() for line in f if line.strip()]
            else:
                logger.error(f"File not found: {args.file}")
                return
        else:
            logger.error("Must specify either --indicator or --file")
            return
        
        logger.info(f"Processing {len(indicators)} indicators")
        logger.info(f"Available collectors: {manager.get_available_collectors()}")
        
        # Perform lookup
        if len(indicators) == 1:
            results = await manager.lookup_indicator(
                indicators[0], 
                args.type, 
                args.collectors,
                args.max_collectors
            )
        else:
            results = await manager.bulk_lookup(
                indicators,
                args.type,
                args.collectors,
                args.delay
            )
        
        # Print summary
        manager.print_summary(results)
        
        # Save results
        manager.save_results(results, args.output, args.output_dir)
        
        # Print some sample results
        print("\nSample Results:")
        print("-" * 50)
        for result in results[:5]:  # Show first 5 results
            print(f"Source: {result.source}")
            print(f"Type: {result.indicator_type}")
            print(f"Indicator: {result.indicator}")
            print(f"Confidence: {result.confidence}")
            print(f"Score: {result.score}")
            print(f"Tags: {result.tags}")
            print("-" * 50)
    
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
