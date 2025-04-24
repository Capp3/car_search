#!/bin/bash
# Setup development environment and run tests for Car Search application

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${YELLOW}Setting up development environment for Car Search...${NC}"

# Check if Poetry is installed
if ! command_exists poetry; then
    echo -e "${RED}Poetry is not installed. Please install Poetry first:${NC}"
    echo -e "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies with Poetry...${NC}"
poetry install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file for API keys...${NC}"
    cat > .env << EOF
# API Keys for Car Search Application
# Uncomment and add your keys below

# Car data API keys
# MOTORCHECK_API_KEY=your_key_here
# EDMUNDS_API_KEY=your_key_here
# SMARTCAR_API_KEY=your_key_here

# LLM API keys
# GOOGLE_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
EOF
    echo -e "${GREEN}.env file created. Please edit it to add your API keys.${NC}"
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
poetry run python run_tests.py

# Print success message
echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "To activate the environment, run: ${YELLOW}poetry shell${NC}"
echo -e "To run the application, run: ${YELLOW}python src/main.py${NC}"
echo -e "To run the car search example, run: ${YELLOW}python src/examples/car_search_example.py${NC}"
echo -e "To run tests with coverage, run: ${YELLOW}python run_tests.py --coverage${NC}" 