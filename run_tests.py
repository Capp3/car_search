#!/usr/bin/env python
"""
Test runner script for the Car Search application.

This script runs the tests with the proper configuration and provides
options for test coverage reporting.
"""

import os
import sys
import pytest


def main():
    """Run the tests with the proper configuration."""
    # Add the project root to the Python path if needed
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Default arguments for pytest
    args = [
        "--verbose",
        "tests"
    ]
    
    # Check for coverage argument
    if "--coverage" in sys.argv:
        sys.argv.remove("--coverage")
        args = [
            "--cov=src",
            "--cov-report=term",
            "--cov-report=html:coverage_report",
        ] + args
    
    # Run the tests
    return pytest.main(args)


if __name__ == "__main__":
    sys.exit(main()) 