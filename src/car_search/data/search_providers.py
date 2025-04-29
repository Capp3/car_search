"""Search providers for the Car Search application.

This module provides interfaces and implementations for search providers that
retrieve car listing data from various sources.
"""

import asyncio
import os
import re
import time
import urllib.parse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

import aiohttp
import bs4
from bs4 import BeautifulSoup

from ..config.manager import config_manager
from ..core.logging import get_logger
from ..models.car_data import CarListingData
from ..models.search_parameters import SearchParameters

# Set up logger for this module
logger = get_logger(__name__)


class ISearchProvider(ABC):
    """Interface for search providers."""

    @abstractmethod
    async def search(self, parameters: SearchParameters) -> List[CarListingData]:
        """Search for car listings using the provided parameters.

        Args:
            parameters: Search parameters

        Returns:
            List of car listing data objects
        """
        pass

    @abstractmethod
    def construct_search_url(self, parameters: SearchParameters) -> str:
        """Construct a search URL from the provided parameters.

        Args:
            parameters: Search parameters

        Returns:
            Search URL
        """
        pass


class AutoTraderProvider(ISearchProvider):
    """Search provider for AutoTrader UK."""

    BASE_URL = "https://www.autotrader.co.uk"
    SEARCH_PATH = "/car-search"

    def __init__(self):
        """Initialize the AutoTrader search provider."""
        # Get base URL from configuration if available
        self.base_url = config_manager.get_setting("api.autotrader_base_url") or self.BASE_URL

        # Get request delay from configuration
        self.request_delay = config_manager.get_setting("search.request_delay") or 1.5

        # Initialize timestamp of last request
        self.last_request_time = 0

        logger.info(f"Initialized AutoTrader search provider with base URL: {self.base_url}")

    def construct_search_url(self, parameters: SearchParameters) -> str:
        """Construct an AutoTrader search URL from the provided parameters.

        Args:
            parameters: Search parameters

        Returns:
            AutoTrader search URL
        """
        # Convert parameters to URL parameters
        url_params = parameters.to_url_params()

        # Add limit parameter to reduce result set size and improve performance
        url_params["per-page"] = "50"  # Limit to 50 results per page
        url_params["page"] = "1"  # Start with first page

        # Construct query string
        query_string = urllib.parse.urlencode(url_params)

        # Construct full URL
        url = f"{self.base_url}{self.SEARCH_PATH}?{query_string}"

        logger.debug(f"Constructed AutoTrader search URL: {url}")
        return url

    async def search(self, parameters: SearchParameters) -> List[CarListingData]:
        """Search for car listings on AutoTrader using the provided parameters.

        Args:
            parameters: Search parameters

        Returns:
            List of car listing data objects
        """
        # Build two different URL formats - the original and a new format
        urls_to_try = []

        # Original URL format
        original_url = self.construct_search_url(parameters)
        urls_to_try.append(original_url)

        # Newer 'cars/results' URL format
        if parameters.postcode:
            alt_url = f"{self.base_url}/cars/results?postcode={parameters.postcode}&radius={parameters.radius}"
            if parameters.min_price > 0:
                alt_url += f"&price-from={parameters.min_price}"
            if parameters.max_price < 100000:
                alt_url += f"&price-to={parameters.max_price}"
            if parameters.make and parameters.make.lower() != "any":
                alt_url += f"&make={parameters.make}"
            if parameters.transmission:
                alt_url += f"&transmission={parameters.transmission.lower()}"
            alt_url += "&include-delivery-option=on&page=1"
            urls_to_try.append(alt_url)

        # Try each URL format
        logger.info(f"Will try {len(urls_to_try)} different URL formats")

        for i, url in enumerate(urls_to_try):
            logger.info(f"Trying URL format {i + 1}: {url}")

            # Rate limiting to avoid overloading the server
            self._handle_rate_limit()

            try:
                # Fetch search results page
                async with aiohttp.ClientSession() as session:
                    logger.debug(f"Sending HTTP request to AutoTrader with URL format {i + 1}")
                    response = await self._fetch_url(session, url)

                    if not response:
                        logger.error(f"Failed to fetch search results for URL format {i + 1}")
                        continue

                    # Log response size to help with debugging
                    response_size = len(response)
                    logger.debug(f"Received response of {response_size} bytes for URL format {i + 1}")

                    # Check for error messages or captcha
                    error_indicators = ["captcha", "access denied", "too many requests", "blocked"]
                    errors_found = [
                        indicator for indicator in error_indicators if indicator.lower() in response.lower()
                    ]
                    if errors_found:
                        logger.error(f"Response contains error indicators: {errors_found}")
                        continue

                    # Parse search results
                    logger.debug(f"Parsing search results HTML from URL format {i + 1}")
                    listings = self._parse_search_results(response)

                    # If we found listings, return them
                    if listings:
                        logger.info(f"Found {len(listings)} car listings with URL format {i + 1}")
                        return listings
                    else:
                        logger.info(f"No car listings found with URL format {i + 1}")

                        # Save the response for debugging if needed
                        if response_size < 1000000:  # Don't save huge responses
                            debug_path = Path.home() / ".car_search" / "debug"
                            os.makedirs(debug_path, exist_ok=True)
                            debug_file = debug_path / f"autotrader_response_format{i + 1}_{int(time.time())}.html"
                            try:
                                with open(debug_file, "w", encoding="utf-8") as f:
                                    f.write(response)
                                logger.debug(f"Saved empty results response to {debug_file} for debugging")
                            except Exception as e:
                                logger.error(f"Failed to save debug response: {e}")
            except Exception as e:
                logger.error(f"Error searching AutoTrader with URL format {i + 1}: {e}")

        # Check if we should use test data
        use_test_data = config_manager.get_setting("search.use_test_data")

        if use_test_data:
            # Return test data if enabled
            logger.info("No results found with any URL format - returning test data (enabled in settings)")
            return self._create_test_results(parameters)
        else:
            # Return empty list if test data is disabled
            logger.info("No results found with any URL format - returning empty list (test data disabled in settings)")
            return []

    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch content from a URL.

        Args:
            session: aiohttp client session
            url: URL to fetch

        Returns:
            Response content as string or None if error
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.autotrader.co.uk/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
                "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
            }

            # Create a timeout for the request
            timeout = aiohttp.ClientTimeout(total=15, connect=10)

            logger.debug(f"Fetching URL with 15s timeout: {url}")

            # Use the session with timeout
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    logger.debug(f"Received 200 response from {url}")
                    return await response.text()
                else:
                    logger.error(f"HTTP error {response.status} when fetching {url}")
                    return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout when fetching {url}")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _parse_search_results(self, html_content: str) -> List[CarListingData]:
        """Parse search results from HTML content.

        Args:
            html_content: HTML content of search results page

        Returns:
            List of car listing data objects
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            listings = []

            # Extract site structure information for debugging
            self._debug_html_structure(soup)

            # Try multiple selectors for search results
            for selector in [
                # Current AutoTrader selectors (2025)
                "article.product-card",
                "div.product-card",
                "div[data-testid='search-card']",
                "article[data-testid]",
                "li.search-page__result",
                # Slightly older AutoTrader selectors
                "li.product-card",
                "li[data-testid*='search-card']",
                "article.advert-card",
                "div.search-results__result",
                # Alternative selectors that might work
                "div.vehicle-card",
                "li.search-result-item",
                "li.result-card",
                "ul.results-list > li",
                "div.listings > div",
                "section.search-result",
                # Very generic fallbacks
                "div.card",
                "div[data-id]",
                "[data-advert-id]",
                "a[href*='/car-details']",
                "a[href*='/classified/advert']",
            ]:
                listing_items = soup.select(selector)
                if listing_items:
                    logger.debug(f"Found {len(listing_items)} listings with selector: {selector}")
                    for item in listing_items:
                        try:
                            # Extract listing data with more robust error handling
                            listing_data = self._extract_listing_data(item)
                            if listing_data:
                                listings.append(listing_data)
                        except Exception as e:
                            logger.error(f"Error parsing listing item with selector {selector}: {e}")
                            continue

                    # If we found listings, stop trying other selectors
                    if listings:
                        break

            # If no listings found with any selector, try an alternative approach
            if not listings:
                logger.warning("No listings found with known selectors, trying fallback extraction")
                # Look for any links that might point to car details
                car_links = soup.select("a[href*='/car-details'], a[href*='/classified/advert']")
                if car_links:
                    logger.debug(f"Found {len(car_links)} car links in fallback mode")
                    # Process the first few links (limit to 20 to prevent overload)
                    for link in car_links[:20]:
                        href = link.get("href", "")
                        if not href:
                            continue

                        # Create a minimal listing from just the link
                        listing_url = f"{self.base_url}{href}" if href.startswith("/") else href
                        listing_id = self._extract_id_from_url(listing_url)

                        if listing_id:
                            # Get any text we can find in the link or its parent
                            title_text = link.get_text(strip=True) or "Unknown Car"
                            make, model, year = self._extract_make_model_year(title_text)

                            # Create a basic listing
                            try:
                                listing_data = CarListingData(
                                    id=listing_id,
                                    title=title_text or f"{make} {model} {year}",
                                    make=make,
                                    model=model,
                                    year=year if year > 0 else 2000,
                                    price=5000.0,  # Default value
                                    mileage=50000,  # Default value
                                    location="Unknown",
                                    listing_url=listing_url,
                                    overall_score=5.0,  # Neutral score
                                )
                                listings.append(listing_data)
                            except Exception as e:
                                logger.error(f"Error creating fallback listing: {e}")

            logger.debug(f"Total listings found: {len(listings)}")
            return listings

        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            return []

    def _debug_html_structure(self, soup: BeautifulSoup):
        """Extract and log information about the HTML structure for debugging.

        Args:
            soup: BeautifulSoup object of the page
        """
        try:
            # Log title to verify we got a proper page
            title = soup.title.text if soup.title else "No title"
            logger.debug(f"Page title: {title}")

            # Check if we're on an error page
            if "access denied" in title.lower() or "captcha" in title.lower() or "blocked" in title.lower():
                logger.error(f"Received error page: {title}")
                return

            # Look for search-related text
            search_text = soup.find(string=re.compile(r"(found|results|cars|vehicles)", re.IGNORECASE))
            if search_text:
                logger.debug(f"Found search-related text: {search_text.strip()}")

            # Check for main sections
            main_sections = []
            for section in soup.select("main, div[role='main'], section, div.container"):
                classes = section.get("class", [])
                main_sections.append(f"{section.name}.{' '.join(classes)}")

            logger.debug(f"Main sections: {main_sections[:5]}")

            # Find any list elements
            list_elements = soup.select("ul, ol")
            logger.debug(f"Found {len(list_elements)} list elements")

            # Look at the first 3 lists in detail
            for i, ul in enumerate(list_elements[:3]):
                classes = ul.get("class", [])
                children = ul.select("li")
                logger.debug(f"List {i + 1}: class='{' '.join(classes)}', items={len(children)}")

                # Check first list item in each list
                if children:
                    first_li = children[0]
                    li_classes = first_li.get("class", [])
                    li_id = first_li.get("id", "")
                    li_data = {k: v for k, v in first_li.attrs.items() if k.startswith("data-")}

                    logger.debug(f"  First item: class='{' '.join(li_classes)}', id='{li_id}', data-attrs={li_data}")

                    # Look for car-related text in this item
                    car_terms = ["car", "vehicle", "price", "miles", "year", "make", "model"]
                    item_text = first_li.get_text(" ", strip=True)
                    contains_car_terms = any(term in item_text.lower() for term in car_terms)

                    if contains_car_terms:
                        logger.debug(f"  Item contains car-related text: '{item_text[:100]}...'")

                        # Look for important elements within this item
                        for selector in ["a[href]", "img", "div.price", "span.price", "[data-testid]"]:
                            elements = first_li.select(selector)
                            if elements:
                                logger.debug(f"  Found {len(elements)} {selector} elements in this item")

                                # For links, check the URL
                                if selector == "a[href]":
                                    href = elements[0].get("href", "")
                                    logger.debug(f"  First link href: {href}")

            # Find key divs with potential result data
            for selector in ["div.results", "div.listings", "div.search-results", "div.cars"]:
                elements = soup.select(selector)
                if elements:
                    logger.debug(f"Found {len(elements)} elements matching '{selector}'")

        except Exception as e:
            logger.error(f"Error in debug HTML structure: {e}")
            # This is just for debug, so errors shouldn't stop processing

    def _extract_listing_data(self, listing_item: bs4.element.Tag) -> Optional[CarListingData]:
        """Extract car listing data from a listing item.

        Args:
            listing_item: BeautifulSoup Tag containing listing item

        Returns:
            CarListingData object or None if extraction failed
        """
        try:
            # Get listing URL and ID - try multiple possible selectors
            listing_link = (
                listing_item.select_one("a.tracking-standard-link")
                or listing_item.select_one("a[data-testid*='search-result']")
                or listing_item.select_one("a.advert-link")
                or listing_item.select_one("a[href*='/car-details/']")
            )

            if not listing_link:
                # If we still can't find a link, look for any anchor tag with href
                all_links = listing_item.select("a[href]")
                for link in all_links:
                    href = link.get("href", "")
                    if "/car-details/" in href or "/classified/advert/" in href:
                        listing_link = link
                        break

            if not listing_link:
                logger.debug(f"Could not find listing link in {listing_item.get('class', [])}")
                return None

            # Extract URL, ensuring it's a full URL
            href = listing_link.get("href", "")
            listing_url = f"{self.base_url}{href}" if href.startswith("/") else href
            listing_id = self._extract_id_from_url(listing_url)

            if not listing_url or not listing_id:
                logger.debug(f"Invalid listing URL: {listing_url}")
                return None

            # Get title and extract make/model/year - try multiple possible selectors
            title_elem = (
                listing_item.select_one("h3.product-card-details__title")
                or listing_item.select_one("h2[data-testid*='title']")
                or listing_item.select_one("h2.advert-title")
                or listing_item.select_one("h2")
                or listing_item.select_one("h3")
            )

            title = title_elem.text.strip() if title_elem else ""
            make, model, year = self._extract_make_model_year(title)

            # Get price - try multiple selectors
            price_elem = (
                listing_item.select_one("div.product-card-pricing__price")
                or listing_item.select_one("[data-testid*='price']")
                or listing_item.select_one(".advert-price")
                or listing_item.select_one(".vehicle-price")
            )

            price_text = price_elem.text.strip() if price_elem else ""
            price = self._extract_price(price_text)

            # Get mileage - try multiple selectors
            mileage_elem = (
                listing_item.select_one("p.product-card-details__subtitle")
                or listing_item.select_one("[data-testid*='mileage']")
                or listing_item.select_one(".advert-mileage")
                or listing_item.select_one(".key-specifications-item")
            )

            mileage_text = mileage_elem.text.strip() if mileage_elem else ""
            mileage = self._extract_mileage(mileage_text)

            # If we couldn't find mileage with specific selectors, try to find it in any text
            if mileage == 0:
                # Look for any text containing "miles" in the listing
                all_text = listing_item.get_text()
                mileage = self._extract_mileage(all_text)

            # Get location - try multiple selectors
            location_elem = (
                listing_item.select_one("p.product-card-seller-info__location")
                or listing_item.select_one("[data-testid*='location']")
                or listing_item.select_one(".advert-location")
                or listing_item.select_one(".seller-location")
            )

            location = location_elem.text.strip() if location_elem else "Unknown"

            # Get image URL - try multiple selectors
            img_elem = (
                listing_item.select_one("img.product-card-image__img")
                or listing_item.select_one("img[data-testid*='image']")
                or listing_item.select_one("img.advert-image")
                or listing_item.select_one("img")
            )

            image_url = img_elem.get("src") or img_elem.get("data-src") if img_elem else None

            # Extract key specs - try multiple selectors
            specs_elems = (
                listing_item.select("ul.listing-key-specs li.atc-type-picanto")
                or listing_item.select("[data-testid*='key-specs'] li")
                or listing_item.select(".advert-key-specs li")
                or listing_item.select(".key-specifications-item")
            )

            specs = [spec.text.strip() for spec in specs_elems] if specs_elems else []

            # Extract specs details
            transmission, fuel_type, engine_size, body_type = self._extract_specs(specs)

            # If we couldn't find specs in list items, try to extract from any text
            if not any([transmission, fuel_type, engine_size, body_type]):
                all_text = listing_item.get_text()
                transmission_match = re.search(r"(automatic|manual|auto|man)", all_text, re.IGNORECASE)
                if transmission_match:
                    transmission_text = transmission_match.group(1).lower()
                    if transmission_text in ["automatic", "auto"]:
                        transmission = "Automatic"
                    elif transmission_text in ["manual", "man"]:
                        transmission = "Manual"

                fuel_type_match = re.search(r"(petrol|diesel|electric|hybrid)", all_text, re.IGNORECASE)
                if fuel_type_match:
                    fuel_type = fuel_type_match.group(1).capitalize()

            # Create car listing data
            listing_data = CarListingData(
                id=listing_id,
                title=title or f"{make} {model} {year}",
                make=make,
                model=model,
                year=year if year > 0 else 2000,  # Default year if not found
                price=price if price > 0 else 5000.0,  # Default price if not found
                mileage=mileage,
                location=location,
                engine_size=engine_size,
                fuel_type=fuel_type,
                transmission=transmission,
                body_type=body_type,
                image_url=image_url,
                listing_url=listing_url,
                # Default to a medium score initially
                overall_score=7.0,
            )

            return listing_data

        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None

    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract listing ID from URL.

        Args:
            url: Listing URL

        Returns:
            Listing ID or None if not found
        """
        if not url:
            return None

        # Try different URL patterns as the structure might have changed
        # First try the original pattern: /car-details/[ID]
        pattern = r"/car-details/([0-9]+)"
        match = re.search(pattern, url)
        if match:
            return match.group(1)

        # Try alternative pattern: /classified/advert/[ID]
        pattern = r"/classified/advert/([0-9a-f-]+)"
        match = re.search(pattern, url)
        if match:
            return match.group(1)

        # Try to find any numeric ID in the URL
        pattern = r"(?:/|=)([0-9]{5,})(?:/|$)"
        match = re.search(pattern, url)
        if match:
            return match.group(1)

        # If all else fails, use a hash of the URL as the ID
        import hashlib

        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _extract_make_model_year(self, title: str) -> tuple:
        """Extract make, model, and year from listing title.

        Args:
            title: Listing title

        Returns:
            Tuple of (make, model, year)
        """
        # Default values
        make = "Unknown"
        model = "Unknown"
        year = 0

        if not title:
            return make, model, year

        # Extract year (usually at the beginning or end of the title)
        year_pattern = r"\b(19[7-9][0-9]|20[0-2][0-9])\b"
        year_match = re.search(year_pattern, title)

        if year_match:
            year = int(year_match.group(1))
            # Remove year from title for easier make/model extraction
            title = title.replace(year_match.group(0), "").strip()

        # Common car makes for better matching
        common_makes = [
            "Audi",
            "BMW",
            "Citroen",
            "Dacia",
            "Fiat",
            "Ford",
            "Honda",
            "Hyundai",
            "Jaguar",
            "Kia",
            "Land Rover",
            "Lexus",
            "Mazda",
            "Mercedes",
            "Mercedes-Benz",
            "Mini",
            "Mitsubishi",
            "Nissan",
            "Peugeot",
            "Porsche",
            "Renault",
            "Seat",
            "Skoda",
            "Suzuki",
            "Tesla",
            "Toyota",
            "Vauxhall",
            "Volkswagen",
            "Volvo",
        ]

        # Try to match known makes
        for car_make in common_makes:
            if car_make.lower() in title.lower():
                make = car_make
                # Extract model (text after make)
                pattern = rf"{re.escape(car_make)}\s+(.*?)(?:\s+\d|\s+\(|\s*$)"
                model_match = re.search(pattern, title, re.IGNORECASE)
                if model_match:
                    model = model_match.group(1).strip()
                break

        return make, model, year

    def _extract_price(self, price_text: str) -> float:
        """Extract price from price text.

        Args:
            price_text: Price text from listing

        Returns:
            Price as a float
        """
        if not price_text:
            return 0.0

        # First try the standard UK format with pound sign
        price_pattern = r"£([0-9,.]+)"
        match = re.search(price_pattern, price_text)

        if match:
            price_str = match.group(1).replace(",", "")
            try:
                return float(price_str)
            except ValueError:
                pass

        # Try alternative format without pound sign but with decimal
        price_pattern = r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
        match = re.search(price_pattern, price_text)

        if match:
            price_str = match.group(1).replace(",", "")
            try:
                return float(price_str)
            except ValueError:
                pass

        # Try extracting any number that could be a price
        price_pattern = r"(\d+(?:,\d+)*)"
        match = re.search(price_pattern, price_text)

        if match:
            price_str = match.group(1).replace(",", "")
            try:
                # Verify this is in a reasonable price range (£500 - £1,000,000)
                price = float(price_str)
                if 500 <= price <= 1000000:
                    return price
            except ValueError:
                pass

        logger.debug(f"Could not extract price from: '{price_text}'")
        return 0.0

    def _extract_mileage(self, mileage_text: str) -> int:
        """Extract mileage from mileage text.

        Args:
            mileage_text: Mileage text from listing

        Returns:
            Mileage as an integer
        """
        if not mileage_text:
            return 0

        # First try standard format with "miles" suffix
        mileage_pattern = r"([0-9,\.]+)\s*miles?"
        match = re.search(mileage_pattern, mileage_text, re.IGNORECASE)

        if match:
            mileage_str = match.group(1).replace(",", "").replace(".", "")
            try:
                return int(mileage_str)
            except ValueError:
                pass

        # Try format with "mi" suffix
        mileage_pattern = r"([0-9,\.]+)\s*mi\b"
        match = re.search(mileage_pattern, mileage_text, re.IGNORECASE)

        if match:
            mileage_str = match.group(1).replace(",", "").replace(".", "")
            try:
                return int(mileage_str)
            except ValueError:
                pass

        # Try to find any number between 1k-200k which is likely to be mileage
        mileage_pattern = r"\b([1-9][0-9]{3,5})\b"
        matches = re.findall(mileage_pattern, mileage_text.replace(",", ""))

        if matches:
            # If multiple matches, use the one most likely to be mileage (in typical range)
            for match in matches:
                try:
                    mileage = int(match)
                    if 1000 <= mileage <= 200000:
                        return mileage
                except ValueError:
                    continue

        logger.debug(f"Could not extract mileage from: '{mileage_text}'")
        return 0

    def _extract_specs(self, specs: List[str]) -> tuple:
        """Extract specifications from specs list.

        Args:
            specs: List of specification strings

        Returns:
            Tuple of (transmission, fuel_type, engine_size, body_type)
        """
        transmission = None
        fuel_type = None
        engine_size = None
        body_type = None

        for spec in specs:
            spec_lower = spec.lower()

            # Check for transmission
            if "automatic" in spec_lower:
                transmission = "Automatic"
            elif "manual" in spec_lower:
                transmission = "Manual"

            # Check for fuel type
            if "petrol" in spec_lower:
                fuel_type = "Petrol"
            elif "diesel" in spec_lower:
                fuel_type = "Diesel"
            elif "hybrid" in spec_lower:
                fuel_type = "Hybrid"
            elif "electric" in spec_lower:
                fuel_type = "Electric"

            # Check for engine size
            engine_pattern = r"(\d+\.\d+)L"
            engine_match = re.search(engine_pattern, spec)
            if engine_match:
                try:
                    engine_size = float(engine_match.group(1))
                except ValueError:
                    pass

            # Check for body type
            body_types = ["hatchback", "saloon", "estate", "suv", "convertible", "coupe", "mpv"]
            for body in body_types:
                if body in spec_lower:
                    body_type = body.capitalize()
                    break

        return transmission, fuel_type, engine_size, body_type

    def _handle_rate_limit(self):
        """Apply rate limiting to avoid overloading the server."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            logger.debug(f"Rate limiting applied, sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _create_test_results(self, parameters: SearchParameters) -> List[CarListingData]:
        """Create test results when real results cannot be obtained.

        Args:
            parameters: Search parameters

        Returns:
            List of test car listings
        """
        logger.info("Creating test results as fallback")

        # Create 5 test results with different makes/models
        test_cars = []

        # Use parameters for some values if available
        price_min = parameters.min_price or 1000
        price_max = parameters.max_price or 10000

        # Test car 1: Ford Fiesta
        test_cars.append(
            CarListingData(
                id="test-1",
                title="2018 Ford Fiesta 1.0L EcoBoost",
                make="Ford",
                model="Fiesta",
                year=2018,
                price=8495.0,
                mileage=35000,
                location="Belfast, Northern Ireland",
                engine_size=1.0,
                fuel_type="Petrol",
                transmission="Manual",
                body_type="Hatchback",
                listing_url="https://www.autotrader.co.uk/car-details/test-1",
                overall_score=8.2,
            )
        )

        # Test car 2: VW Golf
        test_cars.append(
            CarListingData(
                id="test-2",
                title="2017 Volkswagen Golf 1.6 TDI",
                make="Volkswagen",
                model="Golf",
                year=2017,
                price=9995.0,
                mileage=42000,
                location="Lisburn, Northern Ireland",
                engine_size=1.6,
                fuel_type="Diesel",
                transmission="Manual",
                body_type="Hatchback",
                listing_url="https://www.autotrader.co.uk/car-details/test-2",
                overall_score=7.9,
            )
        )

        # Test car 3: Toyota Yaris
        test_cars.append(
            CarListingData(
                id="test-3",
                title="2019 Toyota Yaris 1.5 Hybrid",
                make="Toyota",
                model="Yaris",
                year=2019,
                price=9250.0,
                mileage=28000,
                location="Bangor, Northern Ireland",
                engine_size=1.5,
                fuel_type="Hybrid",
                transmission="Automatic",
                body_type="Hatchback",
                listing_url="https://www.autotrader.co.uk/car-details/test-3",
                overall_score=8.5,
            )
        )

        # Test car 4: Vauxhall Corsa
        test_cars.append(
            CarListingData(
                id="test-4",
                title="2016 Vauxhall Corsa 1.4i",
                make="Vauxhall",
                model="Corsa",
                year=2016,
                price=5995.0,
                mileage=55000,
                location="Newtownards, Northern Ireland",
                engine_size=1.4,
                fuel_type="Petrol",
                transmission="Manual",
                body_type="Hatchback",
                listing_url="https://www.autotrader.co.uk/car-details/test-4",
                overall_score=7.2,
            )
        )

        # Test car 5: Nissan Qashqai
        test_cars.append(
            CarListingData(
                id="test-5",
                title="2018 Nissan Qashqai 1.5 dCi",
                make="Nissan",
                model="Qashqai",
                year=2018,
                price=10995.0,
                mileage=38000,
                location="Carrickfergus, Northern Ireland",
                engine_size=1.5,
                fuel_type="Diesel",
                transmission="Manual",
                body_type="SUV",
                listing_url="https://www.autotrader.co.uk/car-details/test-5",
                overall_score=8.0,
            )
        )

        return test_cars
