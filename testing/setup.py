#!/usr/bin/env python3
"""Setup script for the testing framework."""

import os
import sys
import subprocess
from pathlib import Path


def setup_testing_environment():
    """Setup the testing environment."""
    print("🚀 Setting up Testing & Quality Assurance Framework")
    print("=" * 60)
    
    # Get the testing directory
    testing_dir = Path(__file__).parent
    os.chdir(testing_dir)
    
    # Step 1: Install dependencies
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    # Step 2: Generate test data
    print("\n🔧 Generating test data...")
    try:
        subprocess.run([
            sys.executable, "generators/test_data_generator.py"
        ], check=True, capture_output=True)
        print("✅ Test data generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate test data: {e}")
        return False
    
    # Step 3: Create directories
    print("\n📁 Creating test directories...")
    directories = [
        "coverage/reports",
        "coverage/reports/html",
        "coverage/reports/xml",
        "load/reports",
        "results",
        "fixtures/generated"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created successfully")
    
    # Step 4: Run a quick test
    print("\n🧪 Running quick test...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "unit/test_api_endpoints.py::TestValidationAPI::test_email_validation_valid",
            "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Quick test passed")
        else:
            print(f"⚠️  Quick test had issues (this may be expected if API is not running)")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("⚠️  Quick test timed out (this may be expected if API is not running)")
    except Exception as e:
        print(f"⚠️  Quick test failed: {e}")
    
    # Step 5: Print usage information
    print("\n" + "=" * 60)
    print("🎉 Testing framework setup complete!")
    print("\n📚 Quick Start Commands:")
    print("   # Run all unit tests")
    print("   python run_tests.py --mode unit")
    print("\n   # Run integration tests")
    print("   python run_tests.py --mode integration")
    print("\n   # Run load tests")
    print("   python load/test_runner.py smoke_test")
    print("\n   # Run coverage analysis")
    print("   python coverage/coverage_reporter.py")
    print("\n   # Run comprehensive test suite")
    print("   python run_tests.py --mode comprehensive")
    print("\n📖 See README.md for detailed documentation")
    print("=" * 60)
    
    return True


def check_dependencies():
    """Check if required dependencies are available."""
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "httpx",
        "faker",
        "locust"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main setup function."""
    print("Testing & Quality Assurance Framework Setup")
    print("==========================================")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Setup environment
    return setup_testing_environment()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)