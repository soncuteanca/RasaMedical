#!/usr/bin/env python3
"""
Simple test runner for RasaMedical project
Run with: 
  python run_tests.py          # Fast unit tests only
  python run_tests.py --all    # Include NLU accuracy tests
  python run_tests.py --nlu    # Only NLU accuracy tests
"""

import sys
import subprocess
import os

def run_tests(test_type="unit"):
    """Run the test suite based on type"""
    print("🧪 Running RasaMedical Tests...")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest found")
    except ImportError:
        print("❌ pytest not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
        print("✅ pytest installed")
    
    # Define test categories
    unit_tests = [
        "tests/test_medical_actions.py",
        "tests/test_appointment_actions.py", 
        "tests/test_performance.py"
    ]
    
    nlu_tests = [
        "tests/test_nlu_accuracy.py"
    ]
    
    # Select tests based on type
    if test_type == "unit":
        test_files = unit_tests
        print("🏃‍♂️ Running FAST unit tests (business logic)")
    elif test_type == "nlu":
        test_files = nlu_tests
        print("🧠 Running NLU accuracy tests (this will take several minutes)")
    elif test_type == "all":
        test_files = unit_tests + nlu_tests
        print("🎯 Running ALL tests (unit + NLU)")
    else:
        print(f"❌ Unknown test type: {test_type}")
        return False
    
    # Check which test files exist
    existing_tests = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_tests.append(test_file)
            print(f"✅ Found: {test_file}")
        else:
            print(f"⚠️  Missing: {test_file}")
    
    if not existing_tests:
        print("❌ No test files found!")
        return False
    
    print(f"\n🏃 Running {len(existing_tests)} test file(s)...")
    print("-" * 30)
    
    # Run pytest with appropriate settings
    try:
        pytest_args = [sys.executable, "-m", "pytest", "-v"]
        
        # For unit tests, use quiet mode for faster output
        if test_type == "unit":
            pytest_args.extend(["-q", "--tb=short"])
        
        pytest_args.extend(existing_tests)
        
        result = subprocess.run(pytest_args, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"\n✅ All {test_type} tests passed!")
            return True
        else:
            print(f"\n❌ {test_type.title()} tests failed (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--all", "-a"]:
            test_type = "all"
        elif arg in ["--nlu", "-n"]:
            test_type = "nlu"
        elif arg in ["--unit", "-u"]:
            test_type = "unit"
        elif arg in ["--help", "-h"]:
            print(__doc__)
            return
        else:
            print(f"❌ Unknown argument: {sys.argv[1]}")
            print(__doc__)
            sys.exit(1)
    else:
        test_type = "unit"  # Default to fast unit tests
    
    success = run_tests(test_type)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 