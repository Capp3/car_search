# Car Search Memory Bank

This document serves as a reference for key design decisions made during the creative phases of the Car Search project. It captures the essence of architectural, UI/UX, and algorithmic decisions to guide implementation.

## Architecture Decisions

### Module Structure

- **Selected Approach**: Layered Architecture with Functional Modules
- **Directory Structure**:

  ```
  car_search/
  ├── ui/              # Qt6 UI components
  ├── core/            # Core application logic
  ├── search/          # Search and web scraping
  ├── data/            # Car data integration
  ├── llm/             # LLM integration
  └── config/          # Configuration management
  ```

### Interface Guidelines

1. **UI Interfaces**:
   - Each UI component should accept data models and emit signals for user actions
   - UI should not directly interact with external services
   - Use dependency injection for business logic components

2. **Business Logic Interfaces**:
   - Define clear service interfaces for each business domain using abstract base classes
   - Implement proper error handling and logging
   - Use dependency injection to improve testability

3. **External Integration Interfaces**:
   - Create abstract base classes for external services
   - Implement concrete adapter classes for specific external services
   - Use dependency injection to enable easy switching between implementations

### Data Flow

1. **User Interaction Flow**: UI → Core Services → External Services → Core Services → UI
2. **Configuration Flow**: Load at startup → Components request from manager → Propagate changes
3. **Error Handling Flow**: External services capture errors → Core services process → UI displays messages

## UI/UX Decisions

### Layout Structure

- **Selected Approach**: Tabbed Interface with Sidebar
- **Component Structure**:

  ```
  QMainWindow
  ├── QMenuBar (File, Edit, View, Settings, Help)
  ├── QToolBar (Common actions)
  ├── QTabWidget (Main content)
  │   ├── SearchTab
  │   ├── ResultsTab
  │   ├── DetailsTab
  │   ├── AnalysisTab
  │   └── SettingsTab
  ├── QDockWidget (Sidebar)
  └── QStatusBar
  ```

### Navigation Flow

1. **Primary Flow**: Search → Results → Details → Analysis
2. **Alternative Flows**: Sidebar access to saved searches, multi-car comparison, settings access

### Tab-Specific Guidelines

1. **Search Tab**: Grid layout, visual validation, prominent buttons
2. **Results Tab**: Sortable table, visual indicators for ratings, multi-selection
3. **Details Tab**: Sectioned information, tabs/accordions for organization
4. **Analysis Tab**: Clear LLM recommendations, options to refine search
5. **Settings Tab**: Logical grouping, appropriate controls, clear descriptions

### Visual Design

1. **Color Scheme**: Neutral base, accent colors for interactive elements, light/dark themes
2. **Typography**: Clear hierarchy, consistent headings, adequate sizing
3. **Interactive Elements**: Consistent button styles, hover/active states, keyboard navigation
4. **Data Visualization**: Consistent rating indicators, simple charts, visual indicators for values

## Algorithm Decisions

### Car Matching Algorithm

- **Selected Approach**: Vector-Based Similarity Matching
- **Key Components**:
  1. Text normalization (lowercase, remove punctuation)
  2. Feature vector creation with make, model, year, trim, etc.
  3. Weighted similarity calculation with configurable thresholds
  4. Jaccard similarity for categorical attributes

### Scoring System

- **Selected Approach**: Multi-factor Categorical Scoring
- **Categories**: Excellent, Good, Fair, Poor, Unknown
- **Factors**:
  1. Reliability (40% weight)
  2. Value (30% weight)
  3. Safety (20% weight)
  4. Fuel Economy (10% weight)
- **Handling Missing Data**: Recalculate weights for available data only

### Integration Guidelines

1. **Data Preprocessing**: Clean and normalize all sources, standardize naming, implement caching
2. **Matching Process**: Run on result retrieval, cache results, provide confidence indicators
3. **Scoring Integration**: Calculate after matching, use relevant market data
4. **Performance Optimization**: Precompute vectors, implement indexing, use background processing
5. **User Experience**: Display confidence, explain factors, allow custom weighting

## Implementation Priorities

1. Complete search functionality following module interfaces
2. Implement results display view based on UI design
3. Develop car matching algorithm using vector-based similarity
4. Build out UI tabs according to navigation flow
5. Integrate LLM capabilities following architecture guidelines
