#!/usr/bin/env python3
"""Entry point script for the Car Search application.

This script provides a convenient way to start the application from the command line.
"""

import sys

from src.car_search.main import main

if __name__ == "__main__":
    sys.exit(main())
