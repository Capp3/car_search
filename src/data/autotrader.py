"""
AutoTrader scraping module.

This module provides functionality to scrape car listings from AutoTrader UK
based on user-defined search parameters.
"""

import re
import time
import logging
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
import random
import uuid

import requests
from bs4 import BeautifulSoup
from pydantic import ValidationError

from src.config import settings
from src.models import Car, SearchParameters, ConfidenceLevel, AttributeType, SearchResult

# Configure logging
logger = logging.getLogger(__name__)

# AutoTrader base URL
BASE_URL = "https://www.autotrader.co.uk/car-search"


class AutoTraderScraper:
    """
    AutoTrader scraping client.
    
    This class provides methods to search for cars on AutoTrader
    and extract details from car listings.
    """
    
    def __init__(self):
        """Initialize the AutoTrader scraper."""
        self.headers = {
            "User-Agent": settings.app.user_agent,
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.autotrader.co.uk/",
            "Connection": "keep-alive",
        }
        
        # Set delay between requests to avoid being blocked
        self.request_delay = settings.app.request_delay
        
        # For storing the last request time to manage rate limiting
        self.last_request_time = 0
    
    def _build_search_url(self, params: SearchParameters, page: int = 1) -> str:
        """
        Build the AutoTrader search URL based on the search parameters.
        
        Args:
            params: The search parameters.
            page: The page number to fetch.
            
        Returns:
            The complete search URL.
        """
        # Convert the search parameters to AutoTrader query parameters
        query_params = params.to_autotrader_params()
        
        # Add the page number if it's not the first page
        if page > 1:
            query_params["page"] = page
        
        # Build the URL with query parameters
        query_string = urllib.parse.urlencode(query_params)
        return f"{BASE_URL}?{query_string}"
    
    def _make_request(self, url: str) -> Optional[str]:
        """
        Make an HTTP request with appropriate delay and error handling.
        
        Args:
            url: The URL to request.
            
        Returns:
            The HTML content of the page if successful, None otherwise.
        """
        # Calculate time since last request to implement rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            # Add a small random component to the delay to seem more human-like
            delay = self.request_delay - time_since_last + random.uniform(0.1, 0.5)
            logger.debug(f"Rate limiting: sleeping for {delay:.2f} seconds")
            time.sleep(delay)
        
        # Update the last request time
        self.last_request_time = time.time()
        
        # Make the request
        try:
            logger.info(f"Making request to: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 429:
                logger.warning("Rate limited by AutoTrader. Waiting longer before retry.")
                time.sleep(60)  # Wait a minute before trying again
                return None
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error making request: {e}")
            return None
    
    def _parse_search_results(self, html: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Parse the HTML of a search results page to extract car listings.
        
        Args:
            html: The HTML content of the search results page.
            
        Returns:
            A tuple containing:
            - A list of dictionaries with car data
            - The total number of results
        """
        listings = []
        total_results = 0
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract total results count
            results_count = soup.select_one('.search-form__count')
            if results_count:
                count_text = results_count.text.strip()
                # Extract number from text like "1,234 cars"
                if match := re.search(r'([\d,]+)', count_text):
                    total_results = int(match.group(1).replace(',', ''))
            
            # Extract car listings
            listing_elements = soup.select('.search-page__results .search-result')
            for listing in listing_elements:
                try:
                    # Extract car ID
                    car_id = listing.get('id', f"unknown-{uuid.uuid4()}")
                    
                    # Extract title
                    title_element = listing.select_one('.product-card-content__title')
                    title = title_element.text.strip() if title_element else "Unknown"
                    
                    # Extract price
                    price_element = listing.select_one('.product-card-pricing__price')
                    price_text = price_element.text.strip() if price_element else "0"
                    # Remove non-numeric characters like £ and ,
                    price = int(re.sub(r'[^\d]', '', price_text) or "0")
                    
                    # Extract URL
                    url_element = listing.select_one('a.tracking-standard-link')
                    relative_url = url_element.get('href', '') if url_element else ''
                    full_url = f"https://www.autotrader.co.uk{relative_url}" if relative_url else ""
                    
                    # Extract image URL
                    img_element = listing.select_one('.product-card-image img')
                    img_url = img_element.get('src', '') if img_element else ''
                    
                    # Extract location
                    location_element = listing.select_one('.product-card-meta__item:nth-child(1)')
                    location = location_element.text.strip() if location_element else "Unknown location"
                    
                    # Extract year if included in title
                    year = None
                    if title:
                        year_match = re.search(r'\b(19|20)\d{2}\b', title)
                        if year_match:
                            year = int(year_match.group(0))
                    
                    # Try to extract make and model from title
                    make = None
                    model = None
                    if title:
                        # This is a very simplified approach - would need more sophisticated
                        # parsing in a real implementation
                        title_parts = title.split()
                        if len(title_parts) > 1 and year:
                            # Assume the make is the word after the year
                            year_index = title_parts.index(str(year)) if str(year) in title_parts else -1
                            if year_index >= 0 and year_index < len(title_parts) - 1:
                                make = title_parts[year_index + 1]
                    
                    # Extract mileage
                    mileage_element = listing.select_one('.product-card-specification span:contains("miles")')
                    mileage = None
                    if mileage_element:
                        mileage_text = mileage_element.text.strip()
                        mileage_match = re.search(r'([\d,]+)', mileage_text)
                        if mileage_match:
                            mileage = int(mileage_match.group(1).replace(',', ''))
                    
                    # Extract transmission
                    transmission_element = listing.select_one('.product-card-specification span:contains("Manual"), .product-card-specification span:contains("Automatic")')
                    transmission = None
                    if transmission_element:
                        transmission_text = transmission_element.text.strip().lower()
                        if "manual" in transmission_text:
                            transmission = "manual"
                        elif "automatic" in transmission_text:
                            transmission = "automatic"
                    
                    # Extract fuel type
                    fuel_element = listing.select_one('.product-card-specification span:contains("Petrol"), .product-card-specification span:contains("Diesel"), .product-card-specification span:contains("Electric"), .product-card-specification span:contains("Hybrid")')
                    fuel_type = None
                    if fuel_element:
                        fuel_text = fuel_element.text.strip().lower()
                        if "petrol" in fuel_text:
                            fuel_type = "petrol"
                        elif "diesel" in fuel_text:
                            fuel_type = "diesel"
                        elif "electric" in fuel_text:
                            fuel_type = "electric"
                        elif "hybrid" in fuel_text:
                            fuel_type = "hybrid"
                    
                    # Create listing data
                    listing_data = {
                        "id": car_id,
                        "title": title,
                        "price": price,
                        "url": full_url,
                        "image_url": img_url,
                        "location": location,
                        "year": year,
                        "make": make,
                        "model": model,
                        "mileage": mileage,
                        "transmission": transmission,
                        "fuel_type": fuel_type,
                    }
                    
                    listings.append(listing_data)
                    
                except Exception as e:
                    logger.warning(f"Error parsing listing: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
        
        return listings, total_results
    
    def _create_car_from_listing(self, listing: Dict[str, Any]) -> Car:
        """
        Create a Car model from a listing dictionary.
        
        Args:
            listing: Dictionary containing car data from a search result.
            
        Returns:
            A Car object populated with the data from the listing.
        """
        try:
            car = Car(id=listing["id"])
            
            # Add the basic attributes
            for key, value in listing.items():
                if value is not None:
                    # Skip None values
                    attr_type = None
                    if key == "price" or key == "mileage" or key == "year":
                        attr_type = AttributeType.NUMBER
                    elif key == "id" or key == "title" or key == "url" or key == "location" or key == "make" or key == "model":
                        attr_type = AttributeType.TEXT
                    
                    car.set_attribute(
                        name=key,
                        value=value,
                        source="autotrader_search",
                        confidence=ConfidenceLevel.MEDIUM,
                        attr_type=attr_type
                    )
            
            return car
            
        except Exception as e:
            logger.error(f"Error creating car from listing: {e}")
            # Create a minimal car object with just the ID
            return Car(id=listing.get("id", f"unknown-{uuid.uuid4()}"))
    
    def _extract_car_details(self, url: str, car: Car) -> Car:
        """
        Extract detailed information about a car from its AutoTrader page.
        
        Args:
            url: The URL of the car listing.
            car: The Car object to update with detailed information.
            
        Returns:
            The updated Car object.
        """
        # This would fetch the car's detail page and extract more information
        # For now, this is a placeholder for future implementation
        logger.info(f"Extracting details from: {url}")
        
        html = self._make_request(url)
        if not html:
            logger.warning(f"Failed to fetch details page: {url}")
            return car
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract description
            description_element = soup.select_one('.fpa__description')
            if description_element:
                description = description_element.text.strip()
                car.set_attribute(
                    name="description",
                    value=description,
                    source="autotrader_detail",
                    confidence=ConfidenceLevel.HIGH,
                    attr_type=AttributeType.TEXT
                )
            
            # Extract more detailed specifications
            specs_elements = soup.select('.fpaSpecifications__listItem')
            for spec in specs_elements:
                try:
                    key_element = spec.select_one('.fpaSpecifications__term')
                    value_element = spec.select_one('.fpaSpecifications__value')
                    
                    if key_element and value_element:
                        key = key_element.text.strip().lower().replace(' ', '_')
                        value = value_element.text.strip()
                        
                        # Determine attribute type
                        attr_type = AttributeType.TEXT
                        if re.match(r'^\d+(\.\d+)?$', value):
                            attr_type = AttributeType.NUMBER
                            value = float(value) if '.' in value else int(value)
                        
                        car.set_attribute(
                            name=key,
                            value=value,
                            source="autotrader_detail",
                            confidence=ConfidenceLevel.HIGH,
                            attr_type=attr_type
                        )
                except Exception as e:
                    logger.warning(f"Error parsing specification item: {e}")
            
            # Extract seller info
            seller_element = soup.select_one('.seller-name')
            if seller_element:
                seller_name = seller_element.text.strip()
                car.set_attribute(
                    name="seller_name",
                    value=seller_name,
                    source="autotrader_detail",
                    confidence=ConfidenceLevel.HIGH,
                    attr_type=AttributeType.TEXT
                )
            
            # Extract additional images
            image_elements = soup.select('.fpa-image-gallery__thumbnails img')
            if image_elements:
                image_urls = [img.get('src', '').replace('_th.', '_27.') for img in image_elements if img.get('src')]
                car.set_attribute(
                    name="images",
                    value=image_urls,
                    source="autotrader_detail",
                    confidence=ConfidenceLevel.HIGH,
                    attr_type=AttributeType.LIST
                )
            
            return car
            
        except Exception as e:
            logger.error(f"Error extracting car details: {e}")
            return car
    
    def search(self, params: SearchParameters, max_pages: int = 1, fetch_details: bool = False) -> SearchResult:
        """
        Search for cars on AutoTrader.
        
        Args:
            params: The search parameters.
            max_pages: Maximum number of pages to fetch (default: 1).
            fetch_details: Whether to fetch detailed information for each car.
            
        Returns:
            A SearchResult object containing the matched cars.
        """
        start_time = time.time()
        all_listings = []
        total_results = 0
        
        # Fetch the search results
        for page in range(1, max_pages + 1):
            url = self._build_search_url(params, page)
            html = self._make_request(url)
            
            if not html:
                logger.warning(f"Failed to fetch page {page}")
                continue
            
            listings, page_total = self._parse_search_results(html)
            all_listings.extend(listings)
            
            # Update total results count from the first page
            if page == 1:
                total_results = page_total
            
            # If there are no more results, stop fetching
            if len(listings) == 0:
                break
            
            logger.info(f"Fetched page {page}/{max_pages} with {len(listings)} listings")
        
        # Convert listings to Car objects
        cars = []
        for listing in all_listings:
            car = self._create_car_from_listing(listing)
            
            # Fetch detailed information if requested
            if fetch_details and car.url:
                car = self._extract_car_details(car.url, car)
            
            cars.append(car)
        
        # Create and return the search result
        search_time = time.time() - start_time
        result = SearchResult(cars=cars, total_matches=total_results, parameters=params, search_time=search_time)
        
        logger.info(f"Search completed in {search_time:.2f} seconds. Found {len(cars)} cars.")
        return result
