# Algorithm Design Document: Car Search Application

## Overview

This document outlines the key algorithms required for the Car Search application, focusing on data collection, processing, reliability scoring, value assessment, and LLM integration.

## 1. Web Scraping Algorithm

### Purpose
Efficiently extract car listing data from AutoTrader search results while respecting site policies and minimizing request volume.

### Inputs
- Search parameters (postcode, radius, price range, make, transmission)
- Page number

### Outputs
- Structured car listing data including:
  - Basic car details (make, model, year, price)
  - Technical specifications
  - Seller information
  - Listing URL for detailed view

### Algorithm Steps

```python
def scrape_autotrader_listings(search_params, page_number=1, max_retries=3):
    """
    Scrapes AutoTrader search results with respectful crawling behavior.
    
    Args:
        search_params: Dictionary of search parameters
        page_number: Current page to scrape
        max_retries: Maximum retry attempts for failed requests
        
    Returns:
        List of car listing dictionaries
    """
    # 1. Construct search URL with parameters
    url = construct_search_url(search_params, page_number)
    
    # 2. Implement rate limiting and respectful crawling
    sleep(random.uniform(1.5, 3.0))  # Random delay between requests
    
    # 3. Make request with appropriate headers and session management
    for attempt in range(max_retries):
        try:
            response = session.get(
                url, 
                headers=generate_realistic_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                break
                
            # Handle common HTTP errors
            if response.status_code in [429, 403]:
                wait_time = min(2 ** attempt, 30)  # Exponential backoff
                sleep(wait_time)
            else:
                # Other status codes
                sleep(1)
                
        except RequestException:
            if attempt == max_retries - 1:
                return []  # Return empty results after max retries
            sleep(2 ** attempt)  # Exponential backoff
    
    # 4. Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 5. Extract car listings with robust selectors
    car_listings = []
    listing_elements = soup.select('.search-page__results .search-card')
    
    for element in listing_elements:
        try:
            # Extract data with fallbacks for missing elements
            car = {
                'title': extract_with_fallback(element, '.product-card-content__title', ''),
                'price': extract_with_fallback(element, '.product-card-pricing__price', ''),
                'year': extract_year(element),
                'mileage': extract_mileage(element),
                'location': extract_with_fallback(element, '.product-card-seller__location', ''),
                'transmission': extract_with_fallback(element, '.technical-attributes [data-ui="transmission"]', ''),
                'fuel_type': extract_with_fallback(element, '.technical-attributes [data-ui="fuel-type"]', ''),
                'listing_url': extract_listing_url(element),
                'image_url': extract_image_url(element)
            }
            car_listings.append(car)
        except AttributeError:
            # Skip listings with parsing issues
            continue
    
    # 6. Determine pagination information
    total_pages = extract_total_pages(soup)
    has_next_page = page_number < total_pages
    
    # 7. Return structured data
    return {
        'listings': car_listings,
        'page_info': {
            'current_page': page_number,
            'total_pages': total_pages,
            'has_next_page': has_next_page
        }
    }
```

### Considerations
- Implementation of respectful crawling with random delays
- Robust error handling and retry mechanisms
- Dynamic selector fallbacks for site layout changes
- User-agent rotation to prevent blocking
- HTML parsing optimization for speed

## 2. Car Data Integration Algorithm

### Purpose
Integrate and normalize car data from multiple sources to provide comprehensive information about each vehicle.

### Inputs
- Basic car information from web scraping
- List of available car data APIs

### Outputs
- Enriched car data with reliability information, specifications, and market data

### Algorithm Steps

```python
def enrich_car_data(car_listings, apis_config):
    """
    Enriches car listings with data from multiple API sources.
    
    Args:
        car_listings: List of car listing dictionaries
        apis_config: Configuration for available APIs
        
    Returns:
        List of enriched car dictionaries
    """
    # 1. Initialize API clients based on available configurations
    api_clients = initialize_api_clients(apis_config)
    
    # 2. Set up results cache to avoid duplicate API calls
    results_cache = {}
    
    # 3. Process each car listing for enrichment
    enriched_listings = []
    
    for car in car_listings:
        # 4. Extract make, model, year for API queries
        make, model, year = extract_car_identifiers(car)
        cache_key = f"{make}_{model}_{year}"
        
        # 5. Check cache first to avoid duplicate calls
        if cache_key in results_cache:
            enriched_car = combine_data(car, results_cache[cache_key])
            enriched_listings.append(enriched_car)
            continue
        
        # 6. Gather data from multiple sources with prioritization
        enrichment_data = {}
        
        # 7. Try each API in priority order with fallbacks
        for api_name, client in api_clients.items():
            try:
                if api_name == 'reliability_api':
                    api_data = client.get_reliability_data(make, model, year)
                    enrichment_data['reliability'] = api_data
                    
                elif api_name == 'specifications_api':
                    api_data = client.get_specifications(make, model, year)
                    enrichment_data['specifications'] = api_data
                    
                elif api_name == 'market_data_api':
                    api_data = client.get_market_data(make, model, year)
                    enrichment_data['market_data'] = api_data
                    
                # Additional API types as needed
                
            except (APIError, ConnectionError, TimeoutError):
                # Log error and continue with next API
                continue
        
        # 8. Cache results for future use
        results_cache[cache_key] = enrichment_data
        
        # 9. Combine original data with enrichment data
        enriched_car = combine_data(car, enrichment_data)
        enriched_listings.append(enriched_car)
    
    return enriched_listings
```

### Considerations
- Efficient caching strategy to minimize API calls
- Graceful degradation when APIs are unavailable
- Data normalization across different sources
- Error handling for API-specific issues
- Rate limiting compliance for each API

## 3. Reliability Scoring Algorithm

### Purpose
Calculate a standardized reliability score for each car based on multiple data sources.

### Inputs
- Car make, model, year, and mileage
- Reliability data from various sources

### Outputs
- Overall reliability score (1-5 scale)
- Component-specific reliability scores
- Common issues and their severity

### Algorithm Steps

```python
def calculate_reliability_score(car_data, reliability_sources):
    """
    Calculates a comprehensive reliability score for a car.
    
    Args:
        car_data: Dictionary with car details
        reliability_sources: List of reliability data sources
        
    Returns:
        Dictionary with reliability scores and issues
    """
    # 1. Extract basic car information
    make = car_data.get('make', '')
    model = car_data.get('model', '')
    year = car_data.get('year', 0)
    mileage = car_data.get('mileage', 0)
    
    # 2. Initialize component scores and weights
    components = {
        'engine': {'score': 0, 'weight': 0.30, 'data_points': 0},
        'transmission': {'score': 0, 'weight': 0.25, 'data_points': 0},
        'electrical': {'score': 0, 'weight': 0.15, 'data_points': 0},
        'suspension': {'score': 0, 'weight': 0.15, 'data_points': 0},
        'body': {'score': 0, 'weight': 0.10, 'data_points': 0},
        'interior': {'score': 0, 'weight': 0.05, 'data_points': 0}
    }
    
    # 3. Common issues tracking
    common_issues = []
    
    # 4. Process each reliability data source
    for source in reliability_sources:
        # Skip sources with no data for this car
        if not source.has_data_for(make, model, year):
            continue
            
        # 5. Get component scores from this source
        source_data = source.get_reliability_data(make, model, year)
        
        # 6. Update component scores with this source's data
        for component, data in source_data.get('components', {}).items():
            if component in components:
                components[component]['score'] += data.get('score', 0)
                components[component]['data_points'] += 1
                
                # Add component-specific issues
                for issue in data.get('issues', []):
                    if is_relevant_issue(issue, mileage):
                        common_issues.append({
                            'component': component,
                            'description': issue.get('description', ''),
                            'severity': issue.get('severity', 'medium'),
                            'frequency': issue.get('frequency', 'rare')
                        })
    
    # 7. Calculate average scores for each component
    for component, data in components.items():
        if data['data_points'] > 0:
            data['score'] = data['score'] / data['data_points']
        else:
            # If no data, use average of other components or default
            data['score'] = calculate_fallback_score(components, component)
    
    # 8. Apply age and mileage adjustment
    age_factor = calculate_age_factor(year)
    mileage_factor = calculate_mileage_factor(mileage)
    
    for component in components.values():
        component['score'] *= (age_factor * mileage_factor)
        # Ensure score stays within 1-5 range
        component['score'] = max(1, min(5, component['score']))
    
    # 9. Calculate weighted overall score
    overall_score = sum(
        component['score'] * component['weight'] 
        for component in components.values()
    )
    
    # 10. Format and return results
    return {
        'overall_score': round(overall_score, 1),
        'components': {
            name: {
                'score': round(data['score'], 1),
                'label': score_to_label(data['score'])
            }
            for name, data in components.items()
        },
        'common_issues': sorted(
            common_issues, 
            key=lambda x: severity_to_number(x['severity']),
            reverse=True
        )
    }
```

### Considerations
- Weighted scoring system for different components
- Age and mileage adjustment factors
- Handling of missing data with intelligent fallbacks
- Normalization across different data sources
- Issue relevance based on car's current mileage

## 4. Value Assessment Algorithm

### Purpose
Evaluate the value proposition of each car considering price, reliability, specifications, and market position.

### Inputs
- Car listing data with price
- Reliability score
- Market data for similar vehicles
- User preferences

### Outputs
- Value score (1-5 scale)
- Price position relative to market
- Value justification factors

### Algorithm Steps

```python
def assess_car_value(car_data, market_data, user_preferences):
    """
    Assesses the value proposition of a car based on multiple factors.
    
    Args:
        car_data: Dictionary with car details including reliability
        market_data: Market information for similar vehicles
        user_preferences: User's preference weightings
        
    Returns:
        Dictionary with value assessment
    """
    # 1. Extract relevant data
    price = car_data.get('price', 0)
    reliability_score = car_data.get('reliability', {}).get('overall_score', 0)
    mileage = car_data.get('mileage', 0)
    year = car_data.get('year', 0)
    
    # 2. Calculate market position factors
    market_metrics = calculate_market_position(
        car_data, market_data
    )
    
    price_percentile = market_metrics['price_percentile']
    mileage_percentile = market_metrics['mileage_percentile']
    age_percentile = market_metrics['age_percentile']
    
    # 3. Initialize factor scores
    factors = {
        'price_vs_market': 0,
        'reliability_value': 0,
        'mileage_value': 0,
        'age_value': 0,
        'features_value': 0
    }
    
    # 4. Calculate price value (lower percentile = better value)
    factors['price_vs_market'] = 5 - (price_percentile * 4)
    
    # 5. Calculate reliability value (higher reliability = better value)
    factors['reliability_value'] = reliability_score
    
    # 6. Calculate mileage value (lower mileage percentile = better value)
    factors['mileage_value'] = 5 - (mileage_percentile * 4)
    
    # 7. Calculate age value (lower age percentile = better value)
    factors['age_value'] = 5 - (age_percentile * 4)
    
    # 8. Calculate features value
    features_score = assess_features_value(car_data, market_data)
    factors['features_value'] = features_score
    
    # 9. Apply user preference weights
    weights = get_preference_weights(user_preferences)
    
    weighted_score = sum(
        factors[factor] * weights.get(factor, 0.2)  # Default weight 0.2
        for factor in factors
    )
    
    # 10. Normalize to 1-5 scale
    value_score = max(1, min(5, weighted_score))
    
    # 11. Determine value justification factors
    justifications = []
    
    if factors['price_vs_market'] >= 4:
        justifications.append({
            'factor': 'price',
            'description': 'Price significantly below market average',
            'impact': 'positive'
        })
    elif factors['price_vs_market'] <= 2:
        justifications.append({
            'factor': 'price',
            'description': 'Price above market average',
            'impact': 'negative'
        })
        
    if factors['reliability_value'] >= 4:
        justifications.append({
            'factor': 'reliability',
            'description': 'Excellent reliability record',
            'impact': 'positive'
        })
    elif factors['reliability_value'] <= 2:
        justifications.append({
            'factor': 'reliability',
            'description': 'Below average reliability',
            'impact': 'negative'
        })
        
    # Add more justifications for other factors
    
    # 12. Format and return results
    return {
        'value_score': round(value_score, 1),
        'value_label': score_to_label(value_score),
        'price_vs_market': {
            'percentile': price_percentile,
            'deviation_percent': market_metrics['price_deviation']
        },
        'factors': {
            factor: round(score, 1) for factor, score in factors.items()
        },
        'justifications': justifications
    }
```

### Considerations
- Dynamic weighting based on user preferences
- Market position analysis for fair comparison
- Feature value assessment relative to price point
- Multiple justification factors for transparency
- Normalization across different car classes

## 5. LLM Prompt Engineering Algorithm

### Purpose
Generate effective prompts for LLM providers to extract useful insights about cars.

### Inputs
- Car data (single car or multiple for comparison)
- User query or context
- LLM provider capabilities

### Outputs
- Optimized prompt for LLM
- Parsing strategy for response

### Algorithm Steps

```python
def generate_car_analysis_prompt(car_data, context, llm_config):
    """
    Generates optimized prompts for LLM-based car analysis.
    
    Args:
        car_data: Dictionary or list of cars to analyze
        context: User query or analysis context
        llm_config: Configuration for the LLM provider
        
    Returns:
        Dictionary with prompt and parsing strategy
    """
    # 1. Determine prompt type based on context
    prompt_type = determine_prompt_type(context)
    
    # 2. Initialize prompt components
    components = {
        'system_prompt': '',
        'car_data': '',
        'specific_query': '',
        'output_format': ''
    }
    
    # 3. Generate system prompt based on provider and type
    if prompt_type == 'single_car_analysis':
        components['system_prompt'] = (
            "You are an expert car advisor helping a user evaluate a used car purchase. "
            "Provide a concise, factual analysis of the vehicle based on the data provided. "
            "Focus on reliability, value for money, and potential issues to be aware of. "
            "Use objective information and avoid speculation when possible."
        )
    elif prompt_type == 'car_comparison':
        components['system_prompt'] = (
            "You are an expert car advisor helping a user compare multiple used cars. "
            "Provide a concise, factual comparison highlighting the key differences, "
            "strengths, and weaknesses of each vehicle. Focus on reliability, value, "
            "and which car might be best suited for different priorities."
        )
    elif prompt_type == 'specific_question':
        components['system_prompt'] = (
            "You are an expert car advisor answering a specific question about a vehicle. "
            "Provide a direct, factual answer based on the car data provided. "
            "If the data doesn't contain the answer, acknowledge this limitation."
        )
    
    # 4. Format car data for prompt
    if isinstance(car_data, list):
        # Multiple cars - comparison format
        components['car_data'] = format_cars_for_comparison(car_data)
    else:
        # Single car - detailed format
        components['car_data'] = format_car_details(car_data)
    
    # 5. Add specific query if available
    if context.get('user_query'):
        components['specific_query'] = (
            f"The user specifically wants to know: {context['user_query']}"
        )
    
    # 6. Add output format guidance based on provider capabilities
    if llm_config.get('supports_json'):
        components['output_format'] = (
            "Return your response in the following JSON format:\n"
            "{\n"
            "  \"analysis\": \"Your main analysis text\",\n"
            "  \"key_points\": [\"point 1\", \"point 2\", ...],\n"
            "  \"recommendation\": \"Your overall recommendation\"\n"
            "}"
        )
    else:
        components['output_format'] = (
            "Structure your response with these sections:\n"
            "ANALYSIS: Your main analysis\n"
            "KEY POINTS:\n- Point 1\n- Point 2\n...\n"
            "RECOMMENDATION: Your overall recommendation"
        )
    
    # 7. Assemble final prompt
    prompt = "\n\n".join(
        component for component in components.values() if component
    )
    
    # 8. Determine parsing strategy based on output format
    parsing_strategy = determine_parsing_strategy(
        llm_config, components['output_format']
    )
    
    # 9. Return prompt and parsing information
    return {
        'prompt': prompt,
        'parsing_strategy': parsing_strategy,
        'prompt_type': prompt_type,
        'token_estimate': estimate_tokens(prompt, llm_config)
    }
```

### Considerations
- Provider-specific prompt optimization
- Structured output formatting for reliable parsing
- Token count optimization for cost efficiency
- Context-aware prompt generation
- Fallback strategies for parsing errors

## 6. Search Result Ranking Algorithm

### Purpose
Rank car search results based on multiple criteria including reliability, value, and match to user preferences.

### Inputs
- List of car listings with enriched data
- User preferences and search parameters

### Outputs
- Ranked list of car listings
- Ranking explanation factors

### Algorithm Steps

```python
def rank_search_results(car_listings, user_preferences):
    """
    Ranks car search results based on multiple factors and user preferences.
    
    Args:
        car_listings: List of enriched car listings
        user_preferences: Dictionary of user preferences
        
    Returns:
        List of ranked car listings with ranking factors
    """
    # 1. Extract ranking preferences
    prioritize_reliability = user_preferences.get('prioritize_reliability', 0.5)
    prioritize_value = user_preferences.get('prioritize_value', 0.5)
    prioritize_newer = user_preferences.get('prioritize_newer', 0.5)
    prioritize_lower_mileage = user_preferences.get('prioritize_lower_mileage', 0.5)
    
    # 2. Define scoring weights based on preferences
    weights = {
        'reliability_score': 0.3 * (1 + prioritize_reliability),
        'value_score': 0.3 * (1 + prioritize_value),
        'year': 0.2 * (1 + prioritize_newer),
        'mileage': 0.2 * (1 + prioritize_lower_mileage)
    }
    
    # Normalize weights to sum to 1.0
    weight_sum = sum(weights.values())
    weights = {k: v / weight_sum for k, v in weights.items()}
    
    # 3. Calculate ranking scores for each car
    for car in car_listings:
        # Initialize scoring components
        scores = {}
        
        # Reliability score (higher is better)
        reliability = car.get('reliability', {}).get('overall_score', 0)
        scores['reliability_score'] = min(reliability / 5.0, 1.0)
        
        # Value score (higher is better)
        value = car.get('value_assessment', {}).get('value_score', 0)
        scores['value_score'] = min(value / 5.0, 1.0)
        
        # Year score (newer is better)
        current_year = datetime.now().year
        oldest_year = min(c.get('year', current_year) for c in car_listings)
        year_range = max(current_year - oldest_year, 1)
        year_score = (car.get('year', oldest_year) - oldest_year) / year_range
        scores['year'] = year_score
        
        # Mileage score (lower is better)
        mileages = [c.get('mileage', 0) for c in car_listings if c.get('mileage', 0) > 0]
        if mileages:
            min_mileage = min(mileages)
            max_mileage = max(mileages)
            mileage_range = max(max_mileage - min_mileage, 1)
            mileage_score = 1.0 - ((car.get('mileage', max_mileage) - min_mileage) / mileage_range)
        else:
            mileage_score = 0.5  # Default if mileage data missing
        scores['mileage'] = mileage_score
        
        # Calculate weighted total score
        total_score = sum(
            scores[factor] * weight for factor, weight in weights.items()
        )
        
        # Store scores and ranking factors
        car['ranking'] = {
            'total_score': total_score,
            'component_scores': scores,
            'weights': weights,
            'top_factors': determine_top_factors(scores, weights)
        }
    
    # 4. Sort cars by total score (descending)
    ranked_cars = sorted(
        car_listings,
        key=lambda car: car.get('ranking', {}).get('total_score', 0),
        reverse=True
    )
    
    # 5. Add rank position and percentile
    total_cars = len(ranked_cars)
    for i, car in enumerate(ranked_cars):
        car['ranking']['position'] = i + 1
        car['ranking']['percentile'] = ((total_cars - i) / total_cars) * 100
    
    return ranked_cars
```

### Considerations
- Dynamic weighting based on user preferences
- Normalization of different scoring factors
- Relative scoring based on result set
- Transparency in ranking factors
- Handling of missing data points

## Conclusion

These algorithms form the core of the Car Search application's intelligence, providing users with reliable, data-driven insights for making informed car purchasing decisions. Each algorithm has been designed with flexibility, robustness, and performance in mind, while accounting for real-world challenges such as missing data, API limitations, and varying data quality.

Implementation should proceed incrementally, starting with the web scraping algorithm and building up to the more complex ranking and LLM integration components. Each algorithm should include comprehensive unit tests and performance benchmarks to ensure reliability and efficiency. 