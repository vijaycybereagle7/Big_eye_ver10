#!/usr/bin/env python3
"""Main testing framework script."""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the testing directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from generators.test_data_generator import TestDataGenerator
from coverage.coverage_reporter import CoverageReporter
from load.test_runner import LoadTestRunner


class TestFramework:
    """Main testing framework orchestrator."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.testing_dir = Path(__file__).parent
        self.results_dir = self.testing_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate test run ID
        self.test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_test_data(self, data_types: List[str] = None) -> bool:
        """Generate test data for testing."""
        print("🔧 Generating test data...")
        
        try:
            generator = TestDataGenerator()
            
            if data_types is None:
                # Generate all test data
                generator.generate_all_test_data()
            else:
                # Generate specific data types
                for data_type in data_types:
                    if data_type == "validation":
                        self._generate_validation_data(generator)
                    elif data_type == "reputation":
                        self._generate_reputation_data(generator)
                    elif data_type == "threat_intel":
                        self._generate_threat_intel_data(generator)
                    elif data_type == "load_test":
                        self._generate_load_test_data(generator)
                    elif data_type == "ml_test":
                        self._generate_ml_test_data(generator)
            
            print("✅ Test data generation complete")
            return True
            
        except Exception as e:
            print(f"❌ Error generating test data: {e}")
            return False
    
    def _generate_validation_data(self, generator: TestDataGenerator):
        """Generate validation test data."""
        generator.export_test_data("validation_emails.json", generator.generate_valid_emails(1000))
        generator.export_test_data("validation_domains.json", generator.generate_valid_domains(1000))
        generator.export_test_data("validation_ips.json", generator.generate_valid_ips(1000))
    
    def _generate_reputation_data(self, generator: TestDataGenerator):
        """Generate reputation test data."""
        generator.export_test_data("reputation_test_data.json", generator.generate_reputation_test_data())
    
    def _generate_threat_intel_data(self, generator: TestDataGenerator):
        """Generate threat intelligence test data."""
        generator.export_test_data("threat_intel_data.json", generator.generate_threat_intelligence_data())
    
    def _generate_load_test_data(self, generator: TestDataGenerator):
        """Generate load test data."""
        generator.export_test_data("load_test_data.json", generator.generate_load_test_data(1000))
    
    def _generate_ml_test_data(self, generator: TestDataGenerator):
        """Generate ML test data."""
        generator.export_test_data("ml_test_data.json", generator.generate_ml_test_data())
    
    def run_unit_tests(self, test_pattern: str = None, coverage: bool = True) -> Dict[str, Any]:
        """Run unit tests."""
        print("🧪 Running unit tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.testing_dir / "unit"),
            "-v",
            "--tb=short"
        ]
        
        if coverage:
            cmd.extend([
                "--cov=" + str(self.project_root / "api"),
                "--cov=" + str(self.project_root / "ai_ml"),
                "--cov-report=term-missing",
                "--cov-fail-under=70"
            ])
        
        if test_pattern:
            cmd.extend(["-k", test_pattern])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            test_results = {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_type": "unit"
            }
            
            # Parse test results
            if "passed" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "passed" in line and "failed" in line:
                        test_results["summary"] = line.strip()
                        break
            
            print(f"Unit tests {'✅ PASSED' if result.returncode == 0 else '❌ FAILED'}")
            if test_results.get("summary"):
                print(f"  {test_results['summary']}")
            
            return test_results
            
        except Exception as e:
            print(f"❌ Error running unit tests: {e}")
            return {"success": False, "error": str(e), "test_type": "unit"}
    
    def run_integration_tests(self, test_pattern: str = None) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.testing_dir / "integration"),
            "-v",
            "--tb=short",
            "--run-integration"  # Enable integration tests
        ]
        
        if test_pattern:
            cmd.extend(["-k", test_pattern])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            test_results = {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_type": "integration"
            }
            
            print(f"Integration tests {'✅ PASSED' if result.returncode == 0 else '❌ FAILED'}")
            
            return test_results
            
        except Exception as e:
            print(f"❌ Error running integration tests: {e}")
            return {"success": False, "error": str(e), "test_type": "integration"}
    
    def run_load_test(self, scenario: str, host: str = None) -> Dict[str, Any]:
        """Run load test."""
        print(f"📊 Running load test: {scenario}")
        
        try:
            runner = LoadTestRunner(scenario, host)
            results = runner.run_load_test()
            
            print(f"Load test {'✅ COMPLETED' if results.get('success') else '❌ FAILED'}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error running load test: {e}")
            return {"success": False, "error": str(e), "scenario": scenario}
    
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis."""
        print("📈 Running coverage analysis...")
        
        try:
            reporter = CoverageReporter(str(self.project_root))
            results = reporter.run_all_coverage_operations()
            
            if results["success"]:
                print("✅ Coverage analysis complete")
                if results["comprehensive_report"]:
                    coverage = results["comprehensive_report"]["overall_coverage"]
                    print(f"  Overall coverage: {coverage:.1f}%")
            else:
                print("❌ Coverage analysis failed")
                if "error" in results:
                    print(f"  Error: {results['error']}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error in coverage analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def run_comprehensive_test_suite(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        print("🚀 Running comprehensive test suite...")
        print(f"Test run ID: {self.test_run_id}")
        print("-" * 60)
        
        results = {
            "test_run_id": self.test_run_id,
            "start_time": datetime.now().isoformat(),
            "options": options,
            "phases": {}
        }
        
        try:
            # Phase 1: Generate test data
            if options.get("generate_data", True):
                print("\n📝 Phase 1: Test Data Generation")
                results["phases"]["data_generation"] = {
                    "success": self.generate_test_data(options.get("data_types")),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Phase 2: Unit tests
            if options.get("run_unit_tests", True):
                print("\n🧪 Phase 2: Unit Tests")
                unit_results = self.run_unit_tests(
                    test_pattern=options.get("test_pattern"),
                    coverage=options.get("coverage", True)
                )
                results["phases"]["unit_tests"] = unit_results
                results["phases"]["unit_tests"]["timestamp"] = datetime.now().isoformat()
            
            # Phase 3: Integration tests
            if options.get("run_integration_tests", False):
                print("\n🔗 Phase 3: Integration Tests")
                integration_results = self.run_integration_tests(
                    test_pattern=options.get("test_pattern")
                )
                results["phases"]["integration_tests"] = integration_results
                results["phases"]["integration_tests"]["timestamp"] = datetime.now().isoformat()
            
            # Phase 4: Load tests
            if options.get("run_load_tests", False):
                print("\n📊 Phase 4: Load Tests")
                load_results = {}
                for scenario in options.get("load_scenarios", ["smoke_test"]):
                    load_results[scenario] = self.run_load_test(
                        scenario, 
                        options.get("host")
                    )
                results["phases"]["load_tests"] = load_results
                results["phases"]["load_tests"]["timestamp"] = datetime.now().isoformat()
            
            # Phase 5: Coverage analysis
            if options.get("run_coverage", True):
                print("\n📈 Phase 5: Coverage Analysis")
                coverage_results = self.run_coverage_analysis()
                results["phases"]["coverage_analysis"] = coverage_results
                results["phases"]["coverage_analysis"]["timestamp"] = datetime.now().isoformat()
            
            # Calculate overall success
            results["overall_success"] = self._calculate_overall_success(results["phases"])
            
        except Exception as e:
            print(f"❌ Error in comprehensive test suite: {e}")
            results["error"] = str(e)
            results["overall_success"] = False
        
        results["end_time"] = datetime.now().isoformat()
        
        # Save results
        self._save_test_results(results)
        
        # Print summary
        self._print_test_summary(results)
        
        return results
    
    def _calculate_overall_success(self, phases: Dict[str, Any]) -> bool:
        """Calculate overall test success."""
        # Define which phases are critical
        critical_phases = ["unit_tests", "coverage_analysis"]
        
        # Check critical phases
        for phase in critical_phases:
            if phase in phases:
                if not phases[phase].get("success", False):
                    return False
        
        return True
    
    def _save_test_results(self, results: Dict[str, Any]):
        """Save test results to file."""
        results_file = self.results_dir / f"test_run_{self.test_run_id}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Test results saved to: {results_file}")
    
    def _print_test_summary(self, results: Dict[str, Any]):
        """Print test execution summary."""
        print("\n" + "=" * 60)
        print("TEST EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Test Run ID: {results['test_run_id']}")
        print(f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")
        print(f"Duration: {self._calculate_duration(results['start_time'], results['end_time'])}")
        
        print("\nPhase Results:")
        for phase_name, phase_results in results["phases"].items():
            status = "✅ PASSED" if phase_results.get("success", False) else "❌ FAILED"
            print(f"  {phase_name.replace('_', ' ').title()}: {status}")
        
        # Print specific results
        if "unit_tests" in results["phases"]:
            unit_results = results["phases"]["unit_tests"]
            if "summary" in unit_results:
                print(f"  Unit Tests: {unit_results['summary']}")
        
        if "coverage_analysis" in results["phases"]:
            coverage_results = results["phases"]["coverage_analysis"]
            if coverage_results.get("success") and coverage_results.get("comprehensive_report"):
                coverage = coverage_results["comprehensive_report"]["overall_coverage"]
                print(f"  Coverage: {coverage:.1f}%")
        
        # Print recommendations
        if "coverage_analysis" in results["phases"]:
            coverage_results = results["phases"]["coverage_analysis"]
            if coverage_results.get("success") and coverage_results.get("recommendations"):
                print("\nRecommendations:")
                for rec in coverage_results["recommendations"][:5]:  # Show top 5
                    print(f"  • {rec}")
        
        print("\n" + "=" * 60)
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """Calculate test duration."""
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        duration = end - start
        
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Cybersecurity API Testing Framework")
    
    parser.add_argument(
        "--mode",
        choices=["unit", "integration", "load", "coverage", "comprehensive"],
        default="comprehensive",
        help="Test mode to run"
    )
    
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root directory"
    )
    
    parser.add_argument(
        "--test-pattern",
        help="Pattern to filter tests"
    )
    
    parser.add_argument(
        "--scenario",
        help="Load test scenario"
    )
    
    parser.add_argument(
        "--host",
        default="http://localhost:8000",
        help="API host for load testing"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage analysis"
    )
    
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="Generate test data before running tests"
    )
    
    parser.add_argument(
        "--data-types",
        nargs="+",
        choices=["validation", "reputation", "threat_intel", "load_test", "ml_test"],
        help="Specific data types to generate"
    )
    
    args = parser.parse_args()
    
    # Initialize framework
    framework = TestFramework(args.project_root)
    
    # Run tests based on mode
    if args.mode == "unit":
        # Generate test data if requested
        if args.generate_data:
            framework.generate_test_data(args.data_types)
        
        # Run unit tests
        framework.run_unit_tests(
            test_pattern=args.test_pattern,
            coverage=not args.no_coverage
        )
    
    elif args.mode == "integration":
        framework.run_integration_tests(test_pattern=args.test_pattern)
    
    elif args.mode == "load":
        if not args.scenario:
            print("❌ Load test scenario required. Use --scenario")
            return
        
        framework.run_load_test(args.scenario, args.host)
    
    elif args.mode == "coverage":
        framework.run_coverage_analysis()
    
    elif args.mode == "comprehensive":
        options = {
            "generate_data": args.generate_data or True,
            "data_types": args.data_types,
            "run_unit_tests": True,
            "run_integration_tests": False,  # Disabled by default for speed
            "run_load_tests": False,  # Disabled by default
            "load_scenarios": ["smoke_test"] if args.scenario else [],
            "run_coverage": not args.no_coverage,
            "test_pattern": args.test_pattern,
            "host": args.host
        }
        
        framework.run_comprehensive_test_suite(options)


if __name__ == "__main__":
    main()