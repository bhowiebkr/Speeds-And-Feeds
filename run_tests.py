#!/usr/bin/env python3
"""
Test Runner for Speeds and Feeds Calculator
Runs all tests in the tests directory.
"""

import sys
import os
import subprocess

def run_test(test_file):
    """Run a single test file and return the result"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, 
            os.path.join('tests', test_file)
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False

def main():
    """Run all tests"""
    print("Speeds and Feeds Calculator - Test Suite")
    
    # Find all test files
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')
    test_files = [f for f in os.listdir(tests_dir) 
                  if f.startswith('test_') and f.endswith('.py')]
    
    if not test_files:
        print("No test files found in tests directory!")
        return False
    
    results = {}
    for test_file in sorted(test_files):
        results[test_file] = run_test(test_file)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_file, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_file:30} : {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("ALL TESTS PASSED!")
        return True
    else:
        print(f"{total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)