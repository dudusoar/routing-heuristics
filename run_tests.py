#!/usr/bin/env python3
"""
Test runner script for Routing Heuristics.

Usage:
    python run_tests.py [options]

Options:
    --unit              Run unit tests only
    --integration       Run integration tests only  
    --all               Run all tests (default)
    --coverage          Run with coverage reporting
    --slow              Include slow tests
    --list              List available tests
    --help              Show this help message

Examples:
    python run_tests.py --unit
    python run_tests.py --integration
    python run_tests.py --all --coverage
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Routing Heuristics Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )
    
    parser.add_argument(
        "--integration", 
        action="store_true",
        help="Run integration tests only"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Run all tests (default)"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    
    parser.add_argument(
        "--slow",
        action="store_true", 
        help="Include slow tests (normally skipped)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available tests"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv, -vvv)"
    )
    
    parser.add_argument(
        "-k", "--filter",
        type=str,
        help="Only run tests matching substring"
    )
    
    parser.add_argument(
        "-x", "--exitfirst",
        action="store_true",
        help="Exit on first test failure"
    )
    
    return parser.parse_args()


def get_test_paths():
    """Get paths to test directories."""
    base_dir = Path(__file__).parent
    return {
        "unit": base_dir / "tests" / "unit",
        "integration": base_dir / "tests" / "integration",
        "all": base_dir / "tests"
    }


def list_tests():
    """List available tests."""
    test_paths = get_test_paths()
    
    print("Available tests in Routing Heuristics:")
    print("=" * 60)
    
    for category, path in test_paths.items():
        if path.exists():
            print(f"\n{category.upper()} TESTS ({path}):")
            print("-" * 40)
            
            # Find test files
            test_files = list(path.rglob("test_*.py"))
            if not test_files and category == "all":
                # Also look in subdirectories for 'all' category
                test_files = list((path.parent).rglob("test_*.py"))
            
            for test_file in sorted(test_files):
                rel_path = test_file.relative_to(path.parent)
                print(f"  {rel_path}")
                
                # Count test functions
                try:
                    with open(test_file, 'r') as f:
                        content = f.read()
                        test_count = content.count("def test_")
                        class_count = content.count("class Test")
                    if test_count > 0:
                        print(f"    ({test_count} test functions in {class_count} classes)")
                except:
                    pass
        else:
            print(f"\n{category.upper()} TESTS: Directory not found: {path}")
    
    print("\n" + "=" * 60)
    print("Run tests with: python run_tests.py [--unit|--integration|--all]")


def build_pytest_args(args):
    """Build pytest command line arguments."""
    pytest_args = []
    
    # Basic pytest options
    pytest_args.append("-v")
    
    # Verbosity
    if args.verbose >= 2:
        pytest_args.append("-vv")
    elif args.verbose >= 3:
        pytest_args.append("-vvv")
    
    # Exit on first failure
    if args.exitfirst:
        pytest_args.append("-x")
    
    # Test filter
    if args.filter:
        pytest_args.extend(["-k", args.filter])
    
    # Coverage
    if args.coverage:
        pytest_args.extend([
            "--cov=vrp_toolkit",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_html"
        ])
    
    # Slow tests
    if not args.slow:
        pytest_args.append("-m")
        pytest_args.append("not slow")
    
    # Determine test paths
    test_paths = get_test_paths()
    
    if args.unit:
        pytest_args.append(str(test_paths["unit"]))
        print(f"Running UNIT tests from: {test_paths['unit']}")
    elif args.integration:
        pytest_args.append(str(test_paths["integration"]))
        print(f"Running INTEGRATION tests from: {test_paths['integration']}")
    else:  # --all or default
        pytest_args.append(str(test_paths["all"]))
        print(f"Running ALL tests from: {test_paths['all']}")
    
    return pytest_args


def run_tests(pytest_args):
    """Run tests using pytest."""
    print("\n" + "=" * 60)
    print("Running tests...")
    print("=" * 60 + "\n")
    
    # Add pytest to command
    cmd = [sys.executable, "-m", "pytest"] + pytest_args
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        return 130
    except Exception as e:
        print(f"\nError running tests: {e}")
        return 1


def main():
    """Main entry point."""
    args = parse_args()
    
    # List tests if requested
    if args.list:
        list_tests()
        return 0
    
    # Build pytest arguments
    pytest_args = build_pytest_args(args)
    
    # Run tests
    return_code = run_tests(pytest_args)
    
    # Print summary
    print("\n" + "=" * 60)
    if return_code == 0:
        print("[PASS] All tests passed!")
    else:
        print("[FAIL] Some tests failed.")
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())
