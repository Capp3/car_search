# Intelligent Car Shopping with LLM

A smart car search assistant that helps find the most reliable and value-for-money cars based on user-defined parameters.

## Features

- Location-based search (UK postcodes)
- Price range filtering
- Make/model filtering options
- Drivetrain type filtering (automatic/manual)
- Car reliability comparison using public data
- Value-for-money assessment
- LLM-powered decision support
- QT Based windowing environment with log console

### Data Integration
- AutoTrader search results scraping
- Multiple car data API integrations
- Local SQLite database for storage
- Data migration system
- Tag system for car categorization
- Flexible filtering system for advanced car search

## Project Structure

```
car_search/
├── config/                  # Configuration files and .env
├── docs/                    # Documentation
│   ├── tasks.md             # Project tasks and progress
│   ├── implementation-plan.md # Implementation plan
├── logs/                    # Application logs
├── src/                     # Source code
│   └── car_search/          # Main package
│       ├── config/          # Configuration management
│       ├── core/            # Core utilities (logging, etc.)
│       ├── data/            # Data handling and API clients
│       └── ui/              # User interface components
└── tests/                   # Test cases
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- UV for package management
- PyQt6 for the UI

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/car_search.git
   cd car_search
   ```

2. Create and activate a virtual environment with UV:
   ```
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   uv pip install -e .
   ```

4. Set up configuration:
   ```
   cp config/.env.sample config/.env
   ```
   Edit the `.env` file to add your API keys for:
   - API Ninjas
   - Consumer Reports (RapidAPI)
   - Google Gemini (optional)

### Running the Application

```
python -m src.car_search.main
```

## Development

### Current Status

The application is in active development. Currently implemented:
- Basic UI framework with search parameters form
- Results display and car detail views
- API clients for car data sources

### Upcoming Features

- AutoTrader search integration
- LLM recommendations for car purchasing decisions
- Value scoring and comparison tools
- Advanced filtering and sorting

## Contributing

Contributions are welcome! Please check the `docs/tasks.md` file for current tasks and priorities.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Recent Updates

- 2023-07-26: Refactored search panel into a separate component
- 2023-07-20: Implemented initial API clients and results view
- 2023-07-13: Completed search parameters form
- 2023-07-10: Basic configuration management system
