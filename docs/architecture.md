# Car Search Application Architecture

## System Overview

The Car Search application is designed with a modular architecture to enable clean separation of concerns, maintainable code, and flexibility for future enhancements. The system follows these core principles:

1. **Modularity**: Clear separation between UI, business logic, and external integrations
2. **Extensibility**: Support for multiple data sources and LLM providers
3. **Maintainability**: Well-defined interfaces between components
4. **Configurability**: External configuration for API keys and settings

## Component Architecture

```mermaid
graph TD
    subgraph "Car Search Application"
    
    UI["UI Layer<br>(Qt6)"]
    BL["Business Logic Layer"]
    EI["External Integration Layer"]
    
    UI -->|"Search Params"| BL
    BL -->|"Results"| UI
    BL -->|"API Requests"| EI
    EI -->|"API Responses"| BL
    
    subgraph "UI Layer"
    MF["Main Form"]
    SR["Search Results View"]
    DV["Detail View"]
    LR["LLM Recommendations View"]
    CP["Configuration Panel"]
    end
    
    subgraph "Business Logic Layer"
    SM["Search Manager"]
    DM["Data Manager"]
    LM["LLM Manager"]
    CM["Configuration Manager"]
    end
    
    subgraph "External Integration Layer"
    WS["Web Scraper<br>(AutoTrader)"]
    CD["Car Data API Clients"]
    LA["LLM API Clients"]
    end
    
    MF -->|"Parameters"| SM
    SM -->|"Search Request"| WS
    WS -->|"Car Listings"| SM
    SM -->|"Process Data"| DM
    DM -->|"Enrichment Request"| CD
    CD -->|"Reliability Data"| DM
    DM -->|"Processed Data"| SM
    SM -->|"Analysis Request"| LM
    LM -->|"API Request"| LA
    LA -->|"Recommendations"| LM
    LM -->|"Insights"| SM
    SM -->|"Display Results"| SR
    SR -->|"Select Car"| DV
    LM -->|"Show Recommendations"| LR
    MF -->|"Settings"| CP
    CP -->|"Update Config"| CM
    CM -->|"Config"| SM
    CM -->|"Config"| DM
    CM -->|"Config"| LM
    
    end
    
    style UI fill:#4dabf7,stroke:#0066cc,color:white
    style BL fill:#4dbb5f,stroke:#36873f,color:white
    style EI fill:#ffa64d,stroke:#cc7a30,color:white
    style MF fill:#a5d8ff,stroke:#4dabf7
    style SR fill:#a5d8ff,stroke:#4dabf7
    style DV fill:#a5d8ff,stroke:#4dabf7
    style LR fill:#a5d8ff,stroke:#4dabf7
    style CP fill:#a5d8ff,stroke:#4dabf7
    style SM fill:#b2f2bb,stroke:#4dbb5f
    style DM fill:#b2f2bb,stroke:#4dbb5f
    style LM fill:#b2f2bb,stroke:#4dbb5f
    style CM fill:#b2f2bb,stroke:#4dbb5f
    style WS fill:#ffe8cc,stroke:#ffa64d
    style CD fill:#ffe8cc,stroke:#ffa64d
    style LA fill:#ffe8cc,stroke:#ffa64d
```

## Configuration Management Design

The configuration management system is designed to securely handle API keys and application settings while providing flexibility and ease of use. After evaluating multiple approaches, a Pydantic-based solution was selected.

### Design Options Considered

1. **Environment Variables with dotenv**
   - Simple implementation using environment variables loaded from .env files
   - Good for secure storage of sensitive information
   - Limited structure for complex configurations

2. **YAML/JSON Configuration Files with Environment Variable Overrides**
   - Structured configuration with hierarchical organization
   - Human-readable format with version control for non-sensitive settings
   - More complex implementation than pure environment variables

3. **Database-Backed Configuration**
   - Structured data storage with schema validation
   - Support for runtime changes and user-specific settings
   - Most complex implementation with additional dependencies

4. **Pydantic Settings Management** (Selected)
   - Strong typing and validation of configuration values
   - Compatible with environment variables and configuration files
   - Extensible as requirements grow with good documentation

### Selected Approach: Pydantic Settings Management

The configuration system will use Pydantic's BaseSettings with the following components:

```mermaid
graph TD
    subgraph "Configuration System"
    Settings["AppSettings<br>(Pydantic BaseSettings)"]
    Manager["ConfigManager"]
    EnvFile[".env File"]
    DefaultFile["default_settings.json"]
    
    EnvFile -->|"Load"| Settings
    DefaultFile -->|"Default Values"| Manager
    Manager -->|"Access/Update"| Settings
    
    subgraph "Setting Categories"
    API["APISettings<br>(API Keys)"]
    Logging["LogSettings<br>(Log Configuration)"]
    App["App Configuration"]
    end
    
    Settings -->|"Contains"| API
    Settings -->|"Contains"| Logging
    Settings -->|"Contains"| App
    end
    
    Code["Application Code"] -->|"Use"| Manager
    
    style Settings fill:#4dabf7,stroke:#0066cc,color:white
    style Manager fill:#4dbb5f,stroke:#36873f,color:white
    style EnvFile fill:#ffa64d,stroke:#cc7a30
    style DefaultFile fill:#ffa64d,stroke:#cc7a30
    style API fill:#a5d8ff,stroke:#4dabf7
    style Logging fill:#a5d8ff,stroke:#4dabf7
    style App fill:#a5d8ff,stroke:#4dabf7
```

### Implementation Details

- **Directory Structure**:
  ```
  car_search/
  ├── config/                    # Configuration directory
  │   ├── .env                   # Environment variables (not in version control)
  │   ├── .env.sample            # Sample environment variables (in version control)
  │   └── default_settings.json  # Default settings (in version control)
  ```

- **Key Components**:
  1. **Pydantic Settings Models**: Typed models for different configuration categories
  2. **Configuration Manager**: Interface for accessing and updating settings
  3. **Environment Files**: Store sensitive values securely
  4. **Default Settings**: Provide fallback values for optional settings

- **Features**:
  - Secure storage of API keys via environment variables
  - Strong validation of configuration values
  - Support for hierarchical configuration structure
  - Runtime updates to non-sensitive configuration
  - Masked sensitive values in debugging output

### Benefits of Selected Approach

- Leverages existing Pydantic dependency in the project
- Provides type safety and validation
- Scales well as configuration requirements grow
- Follows Python best practices
- Supports secure handling of sensitive data
- Works well with both environment variables and configuration files

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as UI Layer
    participant BL as Business Logic
    participant WS as Web Scraper
    participant CD as Car Data APIs
    participant LLM as LLM APIs
    
    User->>UI: Input search parameters
    UI->>BL: Request search
    BL->>WS: Scrape search results
    WS-->>BL: Return car listings
    BL->>CD: Request reliability data
    CD-->>BL: Return reliability info
    BL->>BL: Process and score results
    BL->>LLM: Request analysis
    LLM-->>BL: Return recommendations
    BL-->>UI: Return processed results
    UI-->>User: Display results and recommendations
    User->>UI: Select car for details
    UI-->>User: Show detailed view
```

## Component Details

### UI Layer

The UI layer is built using Qt6 and consists of the following components:

1. **Main Form**: Provides inputs for search parameters (postcode, radius, price range, etc.)
2. **Search Results View**: Displays the search results in a list or grid with sorting/filtering
3. **Detail View**: Shows detailed information for a selected car
4. **LLM Recommendations View**: Displays insights and recommendations from the LLM
5. **Configuration Panel**: Allows configuration of API keys, LLM providers, and other settings

### Business Logic Layer

The business logic layer handles the core application logic:

1. **Search Manager**: Coordinates the search process, from input validation to result display
2. **Data Manager**: Handles data processing, enrichment, and scoring
3. **LLM Manager**: Manages interactions with LLM providers, including prompt engineering
4. **Configuration Manager**: Manages application settings and API configurations

### External Integration Layer

The external integration layer manages interactions with external services:

1. **Web Scraper**: Handles scraping of AutoTrader search results
2. **Car Data API Clients**: Integrates with car reliability data sources
3. **LLM API Clients**: Connects to LLM providers (primarily Google Gemini)

## Module Structure

The project will follow this directory structure:

```
car_search/
├── src/
│   ├── ui/              # Qt6 UI components
│   ├── core/            # Core application logic
│   ├── search/          # Search and web scraping
│   ├── data/            # Car data integration
│   ├── llm/             # LLM integration
│   └── config/          # Configuration management
├── tests/               # Test modules
├── docs/                # Documentation
└── config/              # Configuration files
```

## Configuration Management

Configuration will be managed through:

1. Environment variables for sensitive information (API keys)
2. Configuration files for application settings
3. UI settings panel for user-configurable options

## Technical Considerations

### Performance

- Implement caching for web scraping results to reduce redundant requests
- Optimize data processing for large result sets
- Manage LLM API usage efficiently to minimize costs

### Security

- Store API keys securely using environment variables
- Validate user input to prevent injection attacks
- Implement proper error handling without leaking sensitive information

### Extensibility

- Use abstract interfaces for external integrations
- Implement provider pattern for LLM integrations
- Design for easy addition of new data sources

## Implementation Priorities

1. **Core infrastructure**: Project structure, configuration, basic UI
2. **Search functionality**: Web scraping and basic result display
3. **Data enrichment**: Integration with car data APIs
4. **LLM integration**: Connect with Google Gemini for analysis
5. **Advanced features**: Comparison tools, saved searches, etc.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Web scraping blocked | Medium | High | Respectful crawling, fallback options |
| API rate limiting | Medium | Medium | Caching, request throttling |
| LLM cost increases | Low | Medium | Usage tracking, provider abstraction |
| Cross-platform issues | Medium | Low | Regular testing, minimal platform-specific code | 