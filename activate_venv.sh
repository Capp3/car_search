#!/bin/bash
# Simple script to activate the virtual environment
# Usage: source activate_venv.sh

# Get the project root directory (where this script is located)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtual environment
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    # Set PYTHONPATH to include the project root
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    echo "Virtual environment activated successfully."
    echo "Python path: $(which python)"
else
    echo "Error: Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Please create a virtual environment using:"
    echo "python -m venv .venv"
fi 