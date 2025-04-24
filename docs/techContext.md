# Technical Context

## Development Environment
- **Language**: Python 3
- **Package Management**: UV over PIP
- **Virtual Environment**: .venv
- **Version Control**: Git

## External Dependencies
- **Web Scraping**: BeautifulSoup/Selenium for AutoTrader
- **APIs**: Various car data APIs (selection in progress)
- **LLM Integration**: Google Gemini API (primary), with optional support for OpenAI and Anthropic
- **Terminal UI**: Framework TBD (possibly textual, urwid, or rich)

## Architecture
- Terminal-based application using a TUI
- Modular design with separation of concerns:
  - Search parameter management
  - Data collection (web scraping + API calls)
  - Data processing and comparison
  - LLM integration for decision support
  - User interface

## API Resources
- AutoTrader search as base for scraping
- Car data APIs for comprehensive information:
  - Smartcar
  - Edmunds
  - Vehicle Databases
  - MotorCheck
  - Additional options being evaluated

## System Requirements
- Python 3.x environment
- Internet connection for API access
- Terminal with sufficient capabilities for TUI

## Potential Challenges
- Web scraping reliability
- API rate limits
- Data consistency across different sources
- Effective prompt engineering for LLM 