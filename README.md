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
- Terminal-based user interface (TUI)

### Data Integration
- AutoTrader search results scraping
- Multiple car data API integrations
- Local SQLite database for storage
- Data migration system
- Tag system for car categorization
- Flexible filtering system for advanced car search

## Setup

1. Install Poetry (if not already installed):
   ```bash
   pip install poetry
   ```
2. Clone the repository and navigate to it:
   ```bash
   git clone <repo-url>
   cd car_search
   ```
3. Install dependencies:
   ```bash
   poetry install
   ```
4. Activate the project environment:
   ```bash
   poetry shell
   ```

## Usage

```bash
poetry run python src/main.py
```

### API Keys

To use external API services, you'll need to obtain API keys:

1. Create a `.env` file in the project root:
   ```
   MOTORCHECK_API_KEY=your_motorcheck_api_key
   EDMUNDS_API_KEY=your_edmunds_api_key
   SMARTCAR_API_KEY=your_smartcar_api_key
   GOOGLE_API_KEY=your_google_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

2. Alternatively, set these as environment variables or configure them in the application settings.

## Project Structure

The project follows a modular architecture with separation of concerns:

- `src/config/`: Configuration management
- `src/data/`: Data access (web scraping and API interactions)
- `src/models/`: Data models
- `src/services/`: Business logic and LLM integration
  - `api_clients/`: API clients for car data services
  - `scrapers/`: Web scrapers for car listings
- `src/ui/`: Terminal user interface
- `src/examples/`: Example usage scripts

## Car Data Services

### Motorcheck API Client

The Motorcheck API client (`src/services/api_clients/motorcheck.py`) provides access to:

- Detailed car specifications
- Vehicle reliability data
- Vehicle history information
- VIN lookup and registration data

### Car Search Service

The Car Search Service (`src/services/car_search.py`) integrates multiple data sources:

- Scrapes car listings from AutoTrader
- Enriches car data with specifications from API clients
- Provides reliability and history information
- Offers parallel processing for efficient data retrieval

## Examples

Example scripts are available in the `src/examples/` directory:

```bash
# Run the car search example
poetry run python src/examples/car_search_example.py
```

## External Integrations

- AutoTrader (web scraping)
- Car data APIs:
  - Motorcheck API
  - Edmunds API
  - Smartcar API
- LLM Providers:
  - Google Gemini API (default)
  - OpenAI API (GPT-3.5/GPT-4)
  - Mock provider (for testing)

## License

See the LICENSE file for details.