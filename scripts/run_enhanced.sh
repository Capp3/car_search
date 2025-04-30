#!/bin/bash
# Script to run the enhanced Playwright debug tool

# Activate virtual environment if available
if [ -d ".venv" ]; then
    echo "Activating .venv environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating venv environment..."
    source venv/bin/activate
else
    echo "Warning: No virtual environment found."
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3."
    exit 1
fi

# Check if the debug script exists
if [ ! -f "scripts/playwright_enhanced.py" ]; then
    echo "Error: Enhanced script not found at scripts/playwright_enhanced.py"
    exit 1
fi

# Make the debug script executable
chmod +x scripts/playwright_enhanced.py

# Parse command line arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage:"
    echo "  ./scripts/run_enhanced.sh --url 'https://www.autotrader.co.uk/car-search?postcode=BT73fn'"
    echo "  ./scripts/run_enhanced.sh ford bt73fn 2500"
    echo "  ./scripts/run_enhanced.sh --make ford --postcode bt73fn --max-price 2500 --wait 5"
    echo ""
    echo "Options:"
    echo "  --headless      Run browser in headless mode (no UI)"
    echo "  --json-only     Only output JSON results, skip HTML"
    echo "  --wait N        Add N seconds of additional wait time"
    exit 0
elif [ -n "$1" ] && [ -n "$2" ] && [ -n "$3" ] && [[ "$1" != --* ]] && [[ "$2" != --* ]] && [[ "$3" != --* ]]; then
    # Simple format with three parameters: make postcode max-price
    echo "Running enhanced script with make: $1, postcode: $2, max-price: $3"
    python3 scripts/playwright_enhanced.py --make "$1" --postcode "$2" --max-price "$3"
else
    # Pass all arguments through to the script
    echo "Running enhanced script with args: $@"
    python3 scripts/playwright_enhanced.py "$@"
fi

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "\033[92mEnhanced script completed successfully\033[0m"
    echo "Check debug_output/ directory for results:"
    echo "  - pretty_results.json (formatted JSON)"
    echo "  - dom_snapshot.html (full HTML after JS execution)"
    echo "  - screenshots/ (all screenshots taken during execution)"
else
    echo -e "\033[91mEnhanced script encountered an error\033[0m"
fi 