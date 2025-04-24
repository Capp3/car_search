# System Patterns

## Architectural Patterns
- **Modular Architecture**: Separation of components for flexibility and maintainability
- **Service-Oriented Design**: External API interactions and LLM integrations as services
- **MVC-like Pattern**: Separation of data, logic, and presentation

## Design Patterns
- **Strategy Pattern**: For different search strategies and LLM providers
- **Repository Pattern**: For data access and caching
- **Factory Pattern**: For creating service instances
- **Observer Pattern**: For UI updates and notifications

## Project Structure
```
car_search/
│
├── docs/                     # Documentation
│
├── src/                      # Source code
│   ├── __init__.py
│   ├── main.py               # Application entry point
│   │
│   ├── config/               # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   ├── data/                 # Data access layer
│   │   ├── __init__.py
│   │   ├── autotrader.py     # AutoTrader scraping
│   │   └── car_apis.py       # Car data API integration
│   │
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   ├── car.py
│   │   └── search.py
│   │
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   ├── comparison.py     # Car comparison logic
│   │   ├── reliability.py    # Reliability assessment
│   │   └── llm.py            # LLM integration
│   │
│   └── ui/                   # User interface
│       ├── __init__.py
│       ├── app.py            # Main application UI
│       ├── search_screen.py
│       └── results_screen.py
│
├── tests/                    # Unit and integration tests
│
├── .venv/                    # Virtual environment (gitignored)
│
└── README.md                 # Project documentation
```

## Coding Conventions
- PEP 8 style guide
- Type hints for all functions and methods
- Docstrings for modules, classes, and functions
- Async/await for I/O-bound operations (API calls, web scraping)

## Error Handling
- Comprehensive exception handling
- Graceful degradation when APIs are unavailable
- Informative error messages in the UI

## Configuration Management
- Environment variables for sensitive information
- Configuration files for user preferences
- Command-line arguments for runtime options 