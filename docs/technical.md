# Car Search Technical Documentation

This document provides technical details about the implementation of the Car Search application, with focus on architectural decisions, third-party integrations, and complex algorithms.

## Architecture Overview

The Car Search application follows a modular architecture with clear separation of concerns:

1. **UI Layer**: Qt-based user interface components
2. **Service Layer**: Core business logic and coordination
3. **Provider Layer**: External integrations (APIs, web scraping)
4. **Model Layer**: Data structures and validation
5. **Configuration Layer**: System settings and user preferences

The application uses dependency injection to facilitate testing and component replacement.

## Web Scraping Strategy

### Browser Automation with Playwright (2023-08-10)

After testing different web scraping approaches, we've decided to migrate to Playwright for browser automation to handle increasingly complex JavaScript-heavy websites.

#### Key Components

1. **Browser Session Management**
   - Chromium-based browser launched in headless mode (no UI)
   - Configurable options for debugging (screenshot capture, slow-mo)
   - Custom user agent rotation to avoid detection
   - Cookie and session management

2. **Resilient Selector Strategy**
   - Multiple selector options for each element type
   - Automatic fallbacks when primary selectors fail
   - Dynamic wait for elements to appear
   - Content validation to ensure correct data extraction

3. **Interactive Element Handling**
   - Cookie consent dialog management
   - "Load more" button detection and activation
   - Modal popup handling
   - CAPTCHA detection (with fallback to user intervention)

4. **Error Handling**
   - Screenshot capture on failure for debugging
   - Detailed logging of page state
   - Retry logic with exponential backoff
   - Graceful degradation to previous HTTP-based method

#### Implementation Details

```python
# Sample Playwright session configuration
async def create_browser_session():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=config.HEADLESS,
            slow_mo=config.SLOW_MO if config.DEBUG else None
        )
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="en-GB"
        )
        
        # Handle cookies
        if os.path.exists("cookies.json"):
            cookies = json.loads(open("cookies.json").read())
            await context.add_cookies(cookies)
            
        page = await context.new_page()
        page.set_default_timeout(config.TIMEOUT * 1000)
        
        # Add event listeners
        if config.DEBUG:
            page.on("console", lambda msg: logger.debug(f"Browser console: {msg.text}"))
            
        return browser, context, page
```

#### Advantages over HTTP-only Approach

1. **JavaScript Handling**: Can execute JavaScript and handle dynamic content loading
2. **Interactive Elements**: Can interact with forms, buttons, and dialogs
3. **Visual Debugging**: Can capture screenshots for troubleshooting
4. **Cookie Management**: Maintains session cookies between requests
5. **Mobile Emulation**: Can simulate mobile devices when needed

#### Performance Considerations

Browser automation is more resource-intensive than direct HTTP requests:

1. **Memory Usage**: Chromium instance requires ~100-200MB RAM
2. **CPU Usage**: Higher than HTTP-only approach
3. **Request Speed**: Slower than direct HTTP (1-3 second page loads vs. ~200ms HTTP requests)

To mitigate these issues:

1. **Caching**: Aggressive caching of search results
2. **Parallel Processing**: Multiple browser instances for concurrent searches (limited to 2-3)
3. **Resource Cleanup**: Proper browser cleanup after use
4. **Graceful Degradation**: Fallback to HTTP-only approach when possible

## API Integration

### Car Data Sources

The application integrates with multiple external APIs to gather car data:

1. **API Ninjas**: Basic vehicle specifications
2. **Consumer Reports**: Reliability ratings and reviews
3. **JD Power**: Additional reliability data

Each API client follows a consistent pattern:

1. Request formation with proper authentication
2. Response parsing with error handling
3. Rate limiting and retry logic
4. Data normalization to our internal models

### LLM Integration (Planned)

We plan to integrate with Google Gemini API for intelligent car analysis:

1. **Prompt Engineering**: Carefully designed prompts for specific analysis tasks
2. **Context Management**: Providing appropriate context for accurate results
3. **Response Processing**: Extracting structured data from LLM responses
4. **Caching**: Storing results to reduce API usage

## Data Models and Validation

All data models use Pydantic for validation and serialization:

```python
from pydantic import BaseModel, Field, validator

class SearchParameters(BaseModel):
    postcode: str = Field(..., min_length=5, max_length=8)
    radius: int = Field(10, ge=5, le=50)
    make: Optional[str] = None
    model: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    
    @validator('postcode')
    def validate_postcode(cls, v):
        if not re.match(r'^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$', v.upper()):
            raise ValueError('Invalid UK postcode format')
        return v.upper().replace(' ', '')
```

## UI Design

The application uses Qt for the user interface:

1. **Main Window**: Central container with tab-based interface
2. **Search Panel**: Form for entering search parameters
3. **Results View**: Table/grid with filtering and sorting
4. **Detail View**: Comprehensive information about selected vehicles
5. **Analysis Panel**: LLM-generated insights and recommendations

## Testing Strategy

1. **Unit Tests**: For core business logic and data models
2. **Integration Tests**: For API clients and search workflows
3. **UI Tests**: For user interaction and display
4. **Performance Tests**: For resource usage and response times

## Configuration Management

Application settings are managed through a layered approach:

1. **Environment Variables**: Sensitive values (API keys)
2. **Config Files**: System-wide settings
3. **User Preferences**: User-specific settings stored in QSettings

## Logging and Debugging

The application uses Python's logging module with structured logging:

1. **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
2. **Log Rotation**: Daily rotation with 7-day retention
3. **Contextual Information**: Each log entry includes context (user action, component)
4. **Error Reporting**: Detailed error information with stack traces

## Security Considerations

1. **API Key Storage**: Keys stored securely, not in source code
2. **Data Privacy**: Minimal data collection, local storage where possible
3. **Input Validation**: All user inputs validated before use
4. **Error Handling**: No sensitive information in error messages

## Performance Optimization

1. **Caching**: Results cached to reduce API and scraping calls
2. **Lazy Loading**: Data loaded only when needed
3. **Background Processing**: Heavy operations run in background threads
4. **Resource Management**: Proper cleanup of resources (browser instances, network connections)

## Future Technical Enhancements

1. **Database Integration**: Move from file-based storage to proper database
2. **Multi-threading**: Improve UI responsiveness during heavy operations
3. **Cloud Synchronization**: Optional sync of user preferences and saved searches
4. **Mobile Compatibility**: Responsive design for various screen sizes
5. **Plugin Architecture**: Allow for easy extension with new data sources 