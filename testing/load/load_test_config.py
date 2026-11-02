"""Load testing configuration files."""

# load_test_config.py - Load test scenarios configuration
import json
from typing import Dict, List, Any

LOAD_TEST_SCENARIOS = {
    "smoke_test": {
        "description": "Quick smoke test to verify API is responding",
        "users": 5,
        "spawn_rate": 2,
        "duration": "1m",
        "user_classes": ["ValidationUser", "ReputationUser"],
        "host": "http://localhost:8000",
        "expected_rps": 10
    },
    
    "light_load": {
        "description": "Light load test for normal operations",
        "users": 25,
        "spawn_rate": 3,
        "duration": "5m",
        "user_classes": ["ValidationUser", "ReputationUser", "ThreatIntelUser"],
        "host": "http://localhost:8000",
        "expected_rps": 50
    },
    
    "moderate_load": {
        "description": "Moderate load test simulating typical production traffic",
        "users": 100,
        "spawn_rate": 5,
        "duration": "10m",
        "user_classes": ["ValidationUser", "ReputationUser", "ThreatIntelUser", "MLUser", "MixedWorkloadUser"],
        "host": "http://localhost:8000",
        "expected_rps": 200
    },
    
    "heavy_load": {
        "description": "Heavy load test to find breaking points",
        "users": 300,
        "spawn_rate": 10,
        "duration": "15m",
        "user_classes": ["ValidationUser", "ReputationUser", "ThreatIntelUser", "MLUser", "MixedWorkloadUser", "StressTestUser"],
        "host": "http://localhost:8000",
        "expected_rps": 500
    },
    
    "stress_test": {
        "description": "Stress test to find system limits",
        "users": 500,
        "spawn_rate": 20,
        "duration": "20m",
        "user_classes": ["ValidationUser", "ReputationUser", "StressTestUser"],
        "host": "http://localhost:8000",
        "expected_rps": 1000
    },
    
    "spike_test": {
        "description": "Spike test for sudden traffic increases",
        "users": {
            "initial": 10,
            "spike": 200,
            "sustained": 100
        },
        "spawn_rate": 50,
        "duration": "10m",
        "user_classes": ["MixedWorkloadUser"],
        "host": "http://localhost:8000"
    },
    
    "endurance_test": {
        "description": "Long-running endurance test",
        "users": 50,
        "spawn_rate": 2,
        "duration": "2h",
        "user_classes": ["ValidationUser", "ReputationUser", "MixedWorkloadUser"],
        "host": "http://localhost:8000",
        "expected_rps": 100
    },
    
    "benchmark": {
        "description": "Performance benchmarking test",
        "users": 1,
        "spawn_rate": 1,
        "duration": "30m",
        "user_classes": ["BenchmarkUser"],
        "host": "http://localhost:8000"
    }
}

API_ENDPOINTS = {
    "validation": {
        "email": "/api/v1/validate/email",
        "domain": "/api/v1/validate/domain",
        "ip": "/api/v1/validate/ip",
        "url": "/api/v1/validate/url",
        "bulk": "/api/v1/validate/bulk"
    },
    "reputation": {
        "query": "/api/v1/reputation/query",
        "bulk": "/api/v1/reputation/bulk"
    },
    "threat_intelligence": {
        "query": "/api/v1/threats/query",
        "search": "/api/v1/threats/search",
        "correlate": "/api/v1/threats/correlate"
    },
    "ml": {
        "anomaly_detection": "/api/v1/ml/anomaly-detection",
        "phishing_detection": "/api/v1/ml/phishing-detection",
        "domain_reputation": "/api/v1/ml/domain-reputation"
    },
    "admin": {
        "health": "/api/v1/admin/health",
        "metrics": "/api/v1/admin/metrics",
        "stats": "/api/v1/admin/stats"
    }
}

PERFORMANCE_THRESHOLDS = {
    "validation_endpoints": {
        "p50_response_time": 100,  # milliseconds
        "p95_response_time": 500,
        "p99_response_time": 1000,
        "max_response_time": 2000,
        "success_rate": 99.0  # percentage
    },
    "reputation_endpoints": {
        "p50_response_time": 500,
        "p95_response_time": 2000,
        "p99_response_time": 5000,
        "max_response_time": 10000,
        "success_rate": 98.0
    },
    "threat_intelligence_endpoints": {
        "p50_response_time": 1000,
        "p95_response_time": 5000,
        "p99_response_time": 10000,
        "max_response_time": 20000,
        "success_rate": 95.0
    },
    "ml_endpoints": {
        "p50_response_time": 2000,
        "p95_response_time": 10000,
        "p99_response_time": 20000,
        "max_response_time": 30000,
        "success_rate": 95.0
    }
}

LOAD_TEST_DATA_CONFIG = {
    "validation_test_data": {
        "valid_emails_count": 1000,
        "invalid_emails_count": 500,
        "valid_domains_count": 1000,
        "invalid_domains_count": 500,
        "valid_ips_count": 1000,
        "suspicious_ips_count": 200,
        "valid_urls_count": 1000,
        "malicious_urls_count": 300
    },
    "reputation_test_data": {
        "good_reputation_ips": 70,
        "bad_reputation_ips": 20,
        "unknown_reputation_ips": 10,
        "good_reputation_domains": 70,
        "bad_reputation_domains": 20,
        "unknown_reputation_domains": 10
    },
    "threat_intel_test_data": {
        "malware_indicators": 50,
        "botnet_indicators": 30,
        "phishing_indicators": 40,
        "clean_indicators": 80
    }
}


# test_runner.py - Load test execution script
#!/usr/bin/env python3
"""Load test execution script."""

import os
import sys
import time
import subprocess
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add the testing directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_test_config import LOAD_TEST_SCENARIOS, PERFORMANCE_THRESHOLDS


class LoadTestRunner:
    """Load test execution and reporting."""
    
    def __init__(self, scenario: str, host: str = None):
        self.scenario = scenario
        self.scenario_config = LOAD_TEST_SCENARIOS[scenario]
        self.host = host or self.scenario_config["host"]
        self.results_dir = Path("testing/load/reports")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique test run ID
        self.test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = self.results_dir / f"{scenario}_{self.test_run_id}.json"
        
    def run_load_test(self) -> Dict[str, Any]:
        """Execute the load test."""
        print(f"🚀 Starting load test: {self.scenario}")
        print(f"📊 Scenario: {self.scenario_config['description']}")
        print(f"🎯 Host: {self.host}")
        print(f"👥 Users: {self.scenario_config['users']}")
        print(f"⏱️  Duration: {self.scenario_config['duration']}")
        print("-" * 50)
        
        # Prepare locust command
        cmd = self._build_locust_command()
        
        # Execute load test
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            end_time = time.time()
            
            test_results = {
                "test_run_id": self.test_run_id,
                "scenario": self.scenario,
                "host": self.host,
                "config": self.scenario_config,
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.fromtimestamp(end_time).isoformat(),
                "duration": end_time - start_time,
                "command": " ".join(cmd),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            # Parse results if successful
            if result.returncode == 0:
                test_results["parsed_results"] = self._parse_locust_results(result.stdout)
                test_results["performance_analysis"] = self._analyze_performance(test_results["parsed_results"])
            
            # Save results
            self._save_results(test_results)
            
            return test_results
            
        except subprocess.TimeoutExpired:
            error_result = {
                "test_run_id": self.test_run_id,
                "scenario": self.scenario,
                "error": "Load test timed out",
                "success": False
            }
            self._save_results(error_result)
            return error_result
            
        except Exception as e:
            error_result = {
                "test_run_id": self.test_run_id,
                "scenario": self.scenario,
                "error": str(e),
                "success": False
            }
            self._save_results(error_result)
            return error_result
    
    def _build_locust_command(self) -> List[str]:
        """Build locust command from scenario config."""
        config = self.scenario_config
        
        cmd = [
            "python", "-m", "locust",
            "-f", "locustfile.py",
            "--host", self.host,
            "--headless",
            "--csv", str(self.results_dir / f"{self.scenario}_{self.test_run_id}")
        ]
        
        # Add users
        if isinstance(config["users"], dict):
            # Spike test configuration
            cmd.extend(["--users", str(config["users"]["sustained"])])
            cmd.extend(["--spawn-rate", str(config["spawn_rate"])])
            cmd.extend(["--run-time", config["duration"]])
        else:
            # Standard configuration
            cmd.extend(["--users", str(config["users"])])
            cmd.extend(["--spawn-rate", str(config["spawn_rate"])])
            cmd.extend(["--run-time", config["duration"]])
        
        return cmd
    
    def _parse_locust_results(self, stdout: str) -> Dict[str, Any]:
        """Parse locust output to extract key metrics."""
        results = {}
        lines = stdout.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract RPS
            if "Requests/s:" in line:
                try:
                    rps = float(line.split("Requests/s:")[1].strip())
                    results["requests_per_second"] = rps
                except (ValueError, IndexError):
                    pass
            
            # Extract total requests
            if "Request count:" in line:
                try:
                    total_requests = int(line.split("Request count:")[1].split(",")[0].strip())
                    results["total_requests"] = total_requests
                except (ValueError, IndexError):
                    pass
            
            # Extract failure count
            if "Failure count:" in line:
                try:
                    failures = int(line.split("Failure count:")[1].strip())
                    results["total_failures"] = failures
                except (ValueError, IndexError):
                    pass
            
            # Extract response times
            if "Response time (ms):" in line:
                try:
                    response_times = line.split("Response time (ms):")[1].strip()
                    parts = response_times.split(",")
                    
                    results["response_time_p50"] = float(parts[0].split(":")[1].strip())
                    results["response_time_p95"] = float(parts[1].split(":")[1].strip())
                    results["response_time_p99"] = float(parts[2].split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
        
        # Calculate success rate if we have the data
        if "total_requests" in results and "total_failures" in results:
            results["success_rate"] = (
                (results["total_requests"] - results["total_failures"]) / 
                results["total_requests"] * 100
            )
        
        return results
    
    def _analyze_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance against thresholds."""
        analysis = {
            "overall_status": "PASS",
            "metrics": {},
            "violations": [],
            "warnings": []
        }
        
        # Analyze validation endpoint performance
        if "response_time_p50" in results:
            validation_p50 = results["response_time_p50"]
            threshold = PERFORMANCE_THRESHOLDS["validation_endpoints"]["p50_response_time"]
            
            analysis["metrics"]["validation_p50"] = {
                "value": validation_p50,
                "threshold": threshold,
                "status": "PASS" if validation_p50 <= threshold else "FAIL"
            }
            
            if validation_p50 > threshold:
                analysis["violations"].append(
                    f"Validation P50 response time ({validation_p50}ms) exceeds threshold ({threshold}ms)"
                )
                analysis["overall_status"] = "FAIL"
        
        # Analyze success rate
        if "success_rate" in results:
            success_rate = results["success_rate"]
            threshold = PERFORMANCE_THRESHOLDS["validation_endpoints"]["success_rate"]
            
            analysis["metrics"]["success_rate"] = {
                "value": success_rate,
                "threshold": threshold,
                "status": "PASS" if success_rate >= threshold else "FAIL"
            }
            
            if success_rate < threshold:
                analysis["violations"].append(
                    f"Success rate ({success_rate:.1f}%) below threshold ({threshold}%)"
                )
                analysis["overall_status"] = "FAIL"
        
        # Add warnings for high response times
        if "response_time_p95" in results:
            p95 = results["response_time_p95"]
            if p95 > PERFORMANCE_THRESHOLDS["validation_endpoints"]["p95_response_time"]:
                analysis["warnings"].append(
                    f"P95 response time ({p95}ms) is high"
                )
        
        return analysis
    
    def _save_results(self, results: Dict[str, Any]):
        """Save test results to file."""
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📝 Results saved to: {self.results_file}")


def main():
    """Main function to run load tests."""
    parser = argparse.ArgumentParser(description="Load test runner")
    parser.add_argument(
        "scenario",
        choices=list(LOAD_TEST_SCENARIOS.keys()),
        help="Load test scenario to run"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="API host URL (overrides scenario default)"
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenarios"
    )
    
    args = parser.parse_args()
    
    if args.list_scenarios:
        print("Available load test scenarios:")
        print("-" * 50)
        for name, config in LOAD_TEST_SCENARIOS.items():
            print(f"{name}: {config['description']}")
        return
    
    # Run load test
    runner = LoadTestRunner(args.scenario, args.host)
    results = runner.run_load_test()
    
    # Print summary
    print("\n" + "=" * 50)
    print("LOAD TEST SUMMARY")
    print("=" * 50)
    print(f"Scenario: {results['scenario']}")
    print(f"Success: {results.get('success', False)}")
    
    if results.get("success") and "parsed_results" in results:
        parsed = results["parsed_results"]
        print(f"Total Requests: {parsed.get('total_requests', 'N/A')}")
        print(f"Requests/sec: {parsed.get('requests_per_second', 'N/A')}")
        print(f"Success Rate: {parsed.get('success_rate', 'N/A'):.1f}%")
        print(f"P50 Response Time: {parsed.get('response_time_p50', 'N/A')}ms")
        print(f"P95 Response Time: {parsed.get('response_time_p95', 'N/A')}ms")
        
        if "performance_analysis" in results:
            analysis = results["performance_analysis"]
            print(f"\nPerformance Analysis:")
            print(f"Overall Status: {analysis['overall_status']}")
            
            if analysis["violations"]:
                print("Violations:")
                for violation in analysis["violations"]:
                    print(f"  ❌ {violation}")
            
            if analysis["warnings"]:
                print("Warnings:")
                for warning in analysis["warnings"]:
                    print(f"  ⚠️  {warning}")
    
    if not results.get("success"):
        print(f"Error: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()