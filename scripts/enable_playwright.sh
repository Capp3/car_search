#!/bin/bash
# Script to enable Playwright mode for car_search

# Set the environment variable to use Playwright
export SEARCH_USE_PLAYWRIGHT=true

# If running from script directory, navigate to project root
SCRIPT_DIR=$(dirname "$0")
if [ "$SCRIPT_DIR" = "scripts" ]; then
    cd ..
fi

# Check if we need to install Playwright browsers
if python -c "import sys; from src.utils.playwright_utils import ensure_playwright_installed; sys.exit(0 if ensure_playwright_installed() else 1)"; then
    echo "Playwright browsers are already installed."
else
    echo "Installing Playwright browsers..."
    python -m playwright install chromium
fi

# Run the application with Playwright mode enabled
echo "Starting car_search with Playwright mode enabled..."
python car_search_app.py 