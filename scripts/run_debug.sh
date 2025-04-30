#!/bin/bash
# Script to run the Playwright debug tool with common configurations

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
if [ ! -f "scripts/playwright_debug.py" ]; then
    echo "Error: Debug script not found at scripts/playwright_debug.py"
    exit 1
fi

# Make the debug script executable
chmod +x scripts/playwright_debug.py

# Check for JSON only flag
json_only=""
for arg in "$@"; do
    if [ "$arg" == "--json-only" ]; then
        json_only="--json-only"
        break
    fi
done

# Parse command line arguments
if [ "$1" == "--url" ] && [ -n "$2" ]; then
    # Run with direct URL
    echo "Running debug script with URL: $2"
    python3 scripts/playwright_debug.py --url "$2" $json_only
elif [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage:"
    echo "  ./scripts/run_debug.sh --url 'https://www.autotrader.co.uk/car-search?postcode=BT73fn'"
    echo "  ./scripts/run_debug.sh ford bt73fn 2500"
    echo "  ./scripts/run_debug.sh --make ford --postcode bt73fn --max-price 2500"
    echo "  ./scripts/run_debug.sh --headless --make ford --max-price 2500 --postcode bt73fn"
    echo "  ./scripts/run_debug.sh --json-only --make ford --postcode bt73fn --max-price 2500"
    echo ""
    echo "Options:"
    echo "  --headless      Run browser in headless mode (no UI)"
    echo "  --json-only     Only output JSON results, skip HTML output"
    exit 0
elif [ -n "$1" ] && [ -n "$2" ] && [ -n "$3" ]; then
    # Simple format with three parameters: make postcode max-price
    echo "Running debug script with make: $1, postcode: $2, max-price: $3"
    python3 scripts/playwright_debug.py --make "$1" --postcode "$2" --max-price "$3" $json_only
else
    # Pass all arguments through to the script
    echo "Running debug script with args: $@"
    python3 scripts/playwright_debug.py "$@"
fi

# Check exit status
if [ $? -eq 0 ]; then
    echo "Debug script completed successfully"
    echo "Check debug_output/ directory for results"
    
    if [ -f "debug_output/pretty_results.json" ]; then
        echo ""
        echo "Pretty-printed JSON results are available at:"
        echo "  debug_output/pretty_results.json"
    fi
else
    echo "Debug script encountered an error"
fi 