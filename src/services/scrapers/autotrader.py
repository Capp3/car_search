"""
AutoTrader scraper module.

This module provides functionality to scrape car listings from AutoTrader
and extract relevant information.
"""

import logging
import time
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urlencode, quote_plus

import requests
from bs4 import BeautifulSoup

from src.models import Car, ConfidenceLevel, AttributeType
from src.services.scrapers.base_scraper import BaseScraper, ScraperResult

# Configure logging
logger = logging.getLogger(__name__)


class AutoTraderScraper(BaseScraper):
    """
    Scraper for extracting car listings data from AutoTrader.
    """
    
    # Base URLs for different regions
    BASE_URLS = {
        "uk": "https://www.autotrader.co.uk",
        "us": "https://www.autotrader.com",
        # Add more regions as needed
    }
    
    # Search path templates for different regions
    SEARCH_PATHS = {
        "uk": "/car-search",
        "us": "/cars-for-sale",
    }
    
    # User agents to rotate (to avoid blocking)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    ]
    
    def __init__(self, region: str = "uk", delay_between_requests: float = 1.0):
        """
        Initialize the AutoTrader scraper.
        
        Args:
            region: The region to scrape (e.g., "uk", "us").
            delay_between_requests: Delay between requests in seconds to avoid rate limiting.
        """
        if region not in self.BASE_URLS:
            raise ValueError(f"Unsupported region: {region}. Supported regions: {', '.join(self.BASE_URLS.keys())}")
        
        self.region = region
        self.base_url = self.BASE_URLS[region]
        self.search_path = self.SEARCH_PATHS[region]
        self.delay = delay_between_requests
        self.user_agent_index = 0
        
        self.session = requests.Session()
        self.last_request_time = 0
        
        logger.info(f"Initialized AutoTrader scraper for region: {region}")
    
    def _get_next_user_agent(self) -> str:
        """
        Get the next user agent in the rotation.
        
        Returns:
            A user agent string.
        """
        user_agent = self.USER_AGENTS[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(self.USER_AGENTS)
        return user_agent
    
    def _make_request(self, url: str) -> requests.Response:
        """
        Make an HTTP request with appropriate delays and headers.
        
        Args:
            url: URL to request.
            
        Returns:
            The HTTP response.
        """
        # Respect the delay between requests
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.delay:
            sleep_time = self.delay - time_since_last_request
            logger.debug(f"Sleeping for {sleep_time:.2f} seconds before next request")
            time.sleep(sleep_time)
        
        headers = {
            "User-Agent": self._get_next_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": self.base_url,
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        logger.debug(f"Making request to: {url}")
        response = self.session.get(url, headers=headers, timeout=30)
        self.last_request_time = time.time()
        
        response.raise_for_status()
        return response
    
    def build_search_url(self, params: Dict[str, Any]) -> str:
        """
        Build a search URL for AutoTrader based on the provided parameters.
        
        Args:
            params: Dictionary of search parameters.
            
        Returns:
            The constructed search URL.
        """
        # Common parameters between regions
        search_params = {}
        
        if self.region == "uk":
            # UK-specific parameter mapping
            if "make" in params:
                search_params["make"] = params["make"]
            if "model" in params:
                search_params["model"] = params["model"]
            if "postcode" in params:
                search_params["postcode"] = params["postcode"]
            if "radius" in params:
                search_params["radius"] = params["radius"]
            if "min_year" in params:
                search_params["year-from"] = params["min_year"]
            if "max_year" in params:
                search_params["year-to"] = params["max_year"]
            if "min_price" in params:
                search_params["price-from"] = params["min_price"]
            if "max_price" in params:
                search_params["price-to"] = params["max_price"]
            if "fuel_type" in params:
                search_params["fuel-type"] = params["fuel_type"]
            if "transmission" in params:
                search_params["transmission"] = params["transmission"]
            if "body_type" in params:
                search_params["body-type"] = params["body_type"]
            
        elif self.region == "us":
            # US-specific parameter mapping
            if "make" in params:
                search_params["makeCodeList"] = params["make"]
            if "model" in params:
                search_params["modelCodeList"] = params["model"]
            if "zip" in params:
                search_params["zip"] = params["zip"]
            if "search_radius" in params:
                search_params["searchRadius"] = params["search_radius"]
            if "min_year" in params:
                search_params["startYear"] = params["min_year"]
            if "max_year" in params:
                search_params["endYear"] = params["max_year"]
            if "min_price" in params:
                search_params["minPrice"] = params["min_price"]
            if "max_price" in params:
                search_params["maxPrice"] = params["max_price"]
            
        # Construct the URL
        query_string = urlencode(search_params)
        url = f"{self.base_url}{self.search_path}?{query_string}"
        
        logger.debug(f"Built search URL: {url}")
        return url
    
    def search(self, params: Dict[str, Any], limit: int = 10) -> ScraperResult:
        """
        Search for cars on AutoTrader using the provided parameters.
        
        Args:
            params: Dictionary of search parameters.
            limit: Maximum number of results to return.
            
        Returns:
            A ScraperResult containing the scraped cars.
        """
        logger.info(f"Searching AutoTrader with params: {params}, limit: {limit}")
        
        search_url = self.build_search_url(params)
        result = ScraperResult(source="autotrader", region=self.region, url=search_url)
        
        try:
            response = self._make_request(search_url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract car listings based on region-specific selectors
            if self.region == "uk":
                listings = self._extract_uk_listings(soup, limit)
            elif self.region == "us":
                listings = self._extract_us_listings(soup, limit)
            else:
                listings = []
            
            # Process each listing into a Car object
            for listing in listings:
                car = self._process_listing(listing)
                if car:
                    result.add_car(car)
            
            # Check if we need to get more results from pagination
            if len(result.cars) < limit:
                # Handle pagination here
                # This is a simplified version that doesn't handle pagination
                pass
            
            logger.info(f"Found {len(result.cars)} car listings on AutoTrader")
            result.success = True
            
        except Exception as e:
            logger.error(f"Error scraping AutoTrader: {str(e)}")
            result.error = str(e)
        
        return result
    
    def _extract_uk_listings(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """
        Extract car listings from UK AutoTrader search results.
        
        Args:
            soup: BeautifulSoup object of the search results page.
            limit: Maximum number of listings to extract.
            
        Returns:
            List of dictionaries containing listing data.
        """
        listings = []
        
        # This selector is for the UK AutoTrader site and may need to be updated
        # if the site structure changes
        listing_elements = soup.select("li.search-page__result")
        
        for idx, element in enumerate(listing_elements):
            if idx >= limit:
                break
                
            try:
                listing = {}
                
                # Extract listing ID
                listing_id = element.get("id", "")
                if listing_id and listing_id.startswith("product-"):
                    listing["id"] = listing_id.replace("product-", "")
                
                # Extract title (make, model)
                title_element = element.select_one("h3.product-card-details__title")
                if title_element:
                    listing["title"] = title_element.text.strip()
                
                # Extract price
                price_element = element.select_one("div.product-card-pricing__price")
                if price_element:
                    price_text = price_element.text.strip()
                    # Extract numeric price
                    price_match = re.search(r'[\d,]+', price_text)
                    if price_match:
                        price_str = price_match.group(0).replace(',', '')
                        listing["price"] = int(price_str)
                
                # Extract year and mileage
                key_specs = element.select("ul.product-card-details__subtitle li")
                for spec in key_specs:
                    spec_text = spec.text.strip()
                    
                    # Year
                    year_match = re.search(r'\b(19|20)\d{2}\b', spec_text)
                    if year_match:
                        listing["year"] = int(year_match.group(0))
                    
                    # Mileage
                    mileage_match = re.search(r'([\d,]+)\s*miles', spec_text, re.IGNORECASE)
                    if mileage_match:
                        mileage_str = mileage_match.group(1).replace(',', '')
                        listing["mileage"] = int(mileage_str)
                    
                    # Fuel type
                    for fuel_type in ["Petrol", "Diesel", "Electric", "Hybrid"]:
                        if fuel_type.lower() in spec_text.lower():
                            listing["fuel_type"] = fuel_type
                            break
                    
                    # Transmission
                    for transmission in ["Manual", "Automatic"]:
                        if transmission.lower() in spec_text.lower():
                            listing["transmission"] = transmission
                            break
                
                # Extract URL
                url_element = element.select_one("a.product-card-content")
                if url_element and "href" in url_element.attrs:
                    listing["url"] = self.base_url + url_element["href"]
                
                # Extract image URL
                img_element = element.select_one("img.product-card-image__img")
                if img_element and "src" in img_element.attrs:
                    listing["image_url"] = img_element["src"]
                
                # Extract location
                location_element = element.select_one("p.product-card-seller__location")
                if location_element:
                    listing["location"] = location_element.text.strip()
                
                # If we have the essential data, add to results
                if "id" in listing and "title" in listing:
                    listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error processing listing element: {str(e)}")
        
        return listings
    
    def _extract_us_listings(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """
        Extract car listings from US AutoTrader search results.
        
        Args:
            soup: BeautifulSoup object of the search results page.
            limit: Maximum number of listings to extract.
            
        Returns:
            List of dictionaries containing listing data.
        """
        listings = []
        
        # This is a simplified version for US AutoTrader
        # US site uses a lot of JavaScript and may require a more complex approach
        listing_elements = soup.select("div.inventory-listing")
        
        for idx, element in enumerate(listing_elements):
            if idx >= limit:
                break
                
            try:
                listing = {}
                
                # Extract listing ID
                listing_id = element.get("data-listing-id", "")
                if listing_id:
                    listing["id"] = listing_id
                
                # Extract title (make, model)
                title_element = element.select_one("h2.listing-title")
                if title_element:
                    listing["title"] = title_element.text.strip()
                
                # Extract price
                price_element = element.select_one("span.first-price")
                if price_element:
                    price_text = price_element.text.strip()
                    # Extract numeric price
                    price_match = re.search(r'[\d,]+', price_text)
                    if price_match:
                        price_str = price_match.group(0).replace(',', '')
                        listing["price"] = int(price_str)
                
                # Extract year, make, and model from title
                if "title" in listing:
                    year_match = re.search(r'\b(19|20)\d{2}\b', listing["title"])
                    if year_match:
                        listing["year"] = int(year_match.group(0))
                
                # Extract mileage
                mileage_element = element.select_one("span.text-bold.text-subdued.display-block")
                if mileage_element:
                    mileage_text = mileage_element.text.strip()
                    mileage_match = re.search(r'([\d,]+)\s*miles', mileage_text, re.IGNORECASE)
                    if mileage_match:
                        mileage_str = mileage_match.group(1).replace(',', '')
                        listing["mileage"] = int(mileage_str)
                
                # Extract URL
                url_element = element.select_one("a.inventory-link")
                if url_element and "href" in url_element.attrs:
                    listing["url"] = self.base_url + url_element["href"]
                
                # Extract image URL
                img_element = element.select_one("img.image")
                if img_element and "src" in img_element.attrs:
                    listing["image_url"] = img_element["src"]
                
                # Extract location
                location_element = element.select_one("div.seller-info")
                if location_element:
                    listing["location"] = location_element.text.strip()
                
                # If we have the essential data, add to results
                if "id" in listing and "title" in listing:
                    listings.append(listing)
                
            except Exception as e:
                logger.error(f"Error processing US listing element: {str(e)}")
        
        return listings
    
    def _process_listing(self, listing_data: Dict[str, Any]) -> Optional[Car]:
        """
        Process a listing dictionary into a Car object.
        
        Args:
            listing_data: Dictionary containing listing data.
            
        Returns:
            A Car object, or None if processing failed.
        """
        try:
            # Create a unique ID for the car
            car_id = f"autotrader_{self.region}_{listing_data.get('id', '')}"
            
            # Create a new Car object
            car = Car(id=car_id)
            
            # Basic car information
            car.title = listing_data.get("title", "")
            
            # Extract make and model from title if available
            title = listing_data.get("title", "")
            if title:
                # Make and model extraction is approximate; ideally, the site would 
                # provide structured data
                parts = title.split()
                if parts:
                    # First word is often the make
                    car.set_attribute("make", parts[0], AttributeType.STRING, 
                                     ConfidenceLevel.MEDIUM, "autotrader")
                    
                    # If there are more words, combine them as the model
                    if len(parts) > 1:
                        model = " ".join(parts[1:])
                        car.set_attribute("model", model, AttributeType.STRING, 
                                         ConfidenceLevel.MEDIUM, "autotrader")
            
            # Set the source URL
            url = listing_data.get("url", "")
            if url:
                car.set_attribute("source_url", url, AttributeType.URL, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            # Set the image URL if available
            image_url = listing_data.get("image_url", "")
            if image_url:
                car.set_attribute("image_url", image_url, AttributeType.URL, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            # Set numeric attributes
            price = listing_data.get("price")
            if price is not None:
                car.set_attribute("price", price, AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            year = listing_data.get("year")
            if year is not None:
                car.set_attribute("year", year, AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            mileage = listing_data.get("mileage")
            if mileage is not None:
                car.set_attribute("mileage", mileage, AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            # Set categorical attributes
            fuel_type = listing_data.get("fuel_type")
            if fuel_type:
                car.set_attribute("fuel_type", fuel_type, AttributeType.STRING, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            transmission = listing_data.get("transmission")
            if transmission:
                car.set_attribute("transmission", transmission, AttributeType.STRING, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            location = listing_data.get("location")
            if location:
                car.set_attribute("location", location, AttributeType.STRING, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            # Set the date the data was scraped
            car.set_attribute("date_scraped", datetime.now().isoformat(), 
                             AttributeType.DATETIME, ConfidenceLevel.HIGH, "autotrader")
            
            return car
        
        except Exception as e:
            logger.error(f"Error processing listing data into Car object: {str(e)}")
            return None
    
    def get_car_details(self, url: str) -> Optional[Car]:
        """
        Scrape detailed information for a specific car listing.
        
        Args:
            url: URL of the car listing.
            
        Returns:
            A Car object with detailed information, or None if scraping failed.
        """
        logger.info(f"Fetching details for car: {url}")
        
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract the car ID from the URL
            car_id_match = re.search(r'/([0-9]+)$', url)
            car_id = f"autotrader_{self.region}_unknown"
            if car_id_match:
                car_id = f"autotrader_{self.region}_{car_id_match.group(1)}"
            
            car = Car(id=car_id)
            car.set_attribute("source_url", url, AttributeType.URL, 
                             ConfidenceLevel.HIGH, "autotrader")
            
            # Extract car details based on region
            if self.region == "uk":
                self._extract_uk_car_details(soup, car)
            elif self.region == "us":
                self._extract_us_car_details(soup, car)
            
            logger.info(f"Successfully scraped details for car: {car_id}")
            return car
            
        except Exception as e:
            logger.error(f"Error getting car details: {str(e)}")
            return None
    
    def _extract_uk_car_details(self, soup: BeautifulSoup, car: Car) -> None:
        """
        Extract detailed car information from UK AutoTrader listing page.
        
        Args:
            soup: BeautifulSoup object of the listing page.
            car: Car object to populate with details.
        """
        # Extract title
        title_element = soup.select_one("h1.advert-heading__title")
        if title_element:
            car.title = title_element.text.strip()
        
        # Extract price
        price_element = soup.select_one("div.advert-price__cash-price")
        if price_element:
            price_text = price_element.text.strip()
            price_match = re.search(r'£([\d,]+)', price_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                car.set_attribute("price", int(price_str), AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
        
        # Extract key specs
        key_specs = soup.select("ul.key-specifications li")
        for spec in key_specs:
            spec_text = spec.text.strip()
            
            # Year
            year_match = re.search(r'\b(19|20)\d{2}\b', spec_text)
            if year_match:
                car.set_attribute("year", int(year_match.group(0)), AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            # Mileage
            mileage_match = re.search(r'([\d,]+)\s*miles', spec_text, re.IGNORECASE)
            if mileage_match:
                mileage_str = mileage_match.group(1).replace(',', '')
                car.set_attribute("mileage", int(mileage_str), AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
            
            # Fuel type
            for fuel_type in ["Petrol", "Diesel", "Electric", "Hybrid"]:
                if fuel_type.lower() in spec_text.lower():
                    car.set_attribute("fuel_type", fuel_type, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")
                    break
            
            # Transmission
            for transmission in ["Manual", "Automatic"]:
                if transmission.lower() in spec_text.lower():
                    car.set_attribute("transmission", transmission, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")
                    break
            
            # Body type
            for body_type in ["Hatchback", "Saloon", "Estate", "SUV", "Coupe", "Convertible", "MPV", "Van"]:
                if body_type.lower() in spec_text.lower():
                    car.set_attribute("body_type", body_type, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")
                    break
        
        # Extract description
        description_element = soup.select_one("div.key-specification-description")
        if description_element:
            car.set_attribute("description", description_element.text.strip(), 
                             AttributeType.TEXT, ConfidenceLevel.HIGH, "autotrader")
        
        # Extract seller information
        seller_element = soup.select_one("div.seller-name__link")
        if seller_element:
            car.set_attribute("seller", seller_element.text.strip(), 
                             AttributeType.STRING, ConfidenceLevel.HIGH, "autotrader")
        
        location_element = soup.select_one("div.seller-location")
        if location_element:
            car.set_attribute("location", location_element.text.strip(), 
                             AttributeType.STRING, ConfidenceLevel.HIGH, "autotrader")
        
        # Extract image URLs
        image_elements = soup.select("img.image-gallery-slide__img")
        image_urls = []
        for img in image_elements:
            if "src" in img.attrs:
                image_urls.append(img["src"])
        
        if image_urls:
            car.set_attribute("image_urls", json.dumps(image_urls), 
                             AttributeType.JSON, ConfidenceLevel.HIGH, "autotrader")
            # Also set the first image as the main image
            car.set_attribute("image_url", image_urls[0], 
                             AttributeType.URL, ConfidenceLevel.HIGH, "autotrader")
        
        # Extract technical specs
        tech_specs = soup.select("table.tech-spec tbody tr")
        for spec in tech_specs:
            label_element = spec.select_one("th")
            value_element = spec.select_one("td")
            
            if label_element and value_element:
                label = label_element.text.strip().lower()
                value = value_element.text.strip()
                
                # Map common technical specs to Car attributes
                if "engine size" in label:
                    engine_size_match = re.search(r'([\d.]+)', value)
                    if engine_size_match:
                        car.set_attribute("engine_size", float(engine_size_match.group(1)), 
                                         AttributeType.NUMERIC, ConfidenceLevel.HIGH, "autotrader")
                
                elif "power" in label:
                    power_match = re.search(r'([\d.]+)', value)
                    if power_match:
                        car.set_attribute("power_bhp", float(power_match.group(1)), 
                                         AttributeType.NUMERIC, ConfidenceLevel.HIGH, "autotrader")
                
                elif "acceleration" in label:
                    accel_match = re.search(r'([\d.]+)', value)
                    if accel_match:
                        car.set_attribute("acceleration_0_60mph", float(accel_match.group(1)), 
                                         AttributeType.NUMERIC, ConfidenceLevel.HIGH, "autotrader")
                
                elif "economy" in label or "mpg" in label:
                    mpg_match = re.search(r'([\d.]+)', value)
                    if mpg_match:
                        car.set_attribute("mpg", float(mpg_match.group(1)), 
                                         AttributeType.NUMERIC, ConfidenceLevel.HIGH, "autotrader")
                
                elif "co2" in label:
                    co2_match = re.search(r'([\d.]+)', value)
                    if co2_match:
                        car.set_attribute("co2_emissions", float(co2_match.group(1)), 
                                         AttributeType.NUMERIC, ConfidenceLevel.HIGH, "autotrader")
                
                elif "insurance group" in label:
                    car.set_attribute("insurance_group", value, 
                                     AttributeType.STRING, ConfidenceLevel.HIGH, "autotrader")
    
    def _extract_us_car_details(self, soup: BeautifulSoup, car: Car) -> None:
        """
        Extract detailed car information from US AutoTrader listing page.
        
        Args:
            soup: BeautifulSoup object of the listing page.
            car: Car object to populate with details.
        """
        # Extract title
        title_element = soup.select_one("h1.listing-title")
        if title_element:
            car.title = title_element.text.strip()
        
        # Extract price
        price_element = soup.select_one("span.primary-price")
        if price_element:
            price_text = price_element.text.strip()
            price_match = re.search(r'\$([\d,]+)', price_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                car.set_attribute("price", int(price_str), AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
        
        # Extract mileage
        mileage_element = soup.select_one("div.mileage")
        if mileage_element:
            mileage_text = mileage_element.text.strip()
            mileage_match = re.search(r'([\d,]+)\s*miles', mileage_text, re.IGNORECASE)
            if mileage_match:
                mileage_str = mileage_match.group(1).replace(',', '')
                car.set_attribute("mileage", int(mileage_str), AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
        
        # Extract year, make, model from title
        if car.title:
            title_parts = car.title.split()
            year_match = re.search(r'\b(19|20)\d{2}\b', car.title)
            if year_match:
                car.set_attribute("year", int(year_match.group(0)), AttributeType.NUMERIC, 
                                 ConfidenceLevel.HIGH, "autotrader")
                
                # Make is typically after the year
                year_index = title_parts.index(year_match.group(0))
                if year_index + 1 < len(title_parts):
                    car.set_attribute("make", title_parts[year_index + 1], AttributeType.STRING, 
                                     ConfidenceLevel.MEDIUM, "autotrader")
                    
                    # Model is typically the rest of the title
                    if year_index + 2 < len(title_parts):
                        model = " ".join(title_parts[year_index + 2:])
                        car.set_attribute("model", model, AttributeType.STRING, 
                                         ConfidenceLevel.MEDIUM, "autotrader")
        
        # Extract description
        description_element = soup.select_one("div.seller-notes")
        if description_element:
            car.set_attribute("description", description_element.text.strip(), 
                             AttributeType.TEXT, ConfidenceLevel.HIGH, "autotrader")
        
        # Extract location
        location_element = soup.select_one("div.seller-info")
        if location_element:
            car.set_attribute("location", location_element.text.strip(), 
                             AttributeType.STRING, ConfidenceLevel.HIGH, "autotrader")
        
        # Extract image URLs
        image_elements = soup.select("div.media-viewer img")
        image_urls = []
        for img in image_elements:
            if "src" in img.attrs:
                image_urls.append(img["src"])
        
        if image_urls:
            car.set_attribute("image_urls", json.dumps(image_urls), 
                             AttributeType.JSON, ConfidenceLevel.HIGH, "autotrader")
            # Also set the first image as the main image
            car.set_attribute("image_url", image_urls[0], 
                             AttributeType.URL, ConfidenceLevel.HIGH, "autotrader")
        
        # Extract vehicle details
        detail_elements = soup.select("div.details-section table tr")
        for detail in detail_elements:
            cells = detail.select("td")
            if len(cells) >= 2:
                label = cells[0].text.strip().lower()
                value = cells[1].text.strip()
                
                # Map common details to Car attributes
                if "style" in label:
                    car.set_attribute("body_type", value, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")
                
                elif "engine" in label:
                    car.set_attribute("engine", value, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")
                
                elif "fuel" in label:
                    car.set_attribute("fuel_type", value, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")
                
                elif "transmission" in label:
                    car.set_attribute("transmission", value, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")
                
                elif "drive type" in label:
                    car.set_attribute("drive_type", value, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")
                
                elif "color" in label:
                    car.set_attribute("color", value, AttributeType.STRING, 
                                     ConfidenceLevel.HIGH, "autotrader")


# Create a singleton instance for easy importing
autotrader_scraper = AutoTraderScraper() 