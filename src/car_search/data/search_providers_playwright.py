"""Search providers using Playwright for the Car Search application.

This module provides implementations of search providers that use Playwright
for browser automation to retrieve car listing data.
"""

import os
import re
import time
from pathlib import Path
from typing import List, Optional, Dict

from bs4 import BeautifulSoup

from ...utils.playwright_utils import (
    cleanup_session,
    ensure_playwright_installed,
    setup_browser_session,
    setup_screenshot_directory,
    take_screenshot,
)
from ..config.manager import config_manager
from ..core.logging import get_logger
from ..models.car_data import CarListingData
from ..models.search_parameters import SearchParameters
from .search_providers import ISearchProvider

# Set up logger for this module
logger = get_logger(__name__)


class PlaywrightAutoTraderProvider(ISearchProvider):
    """Search provider for AutoTrader UK using Playwright browser automation."""

    BASE_URL = "https://www.autotrader.co.uk"
    SEARCH_PATH = "/car-search"

    def __init__(self):
        """Initialize the AutoTrader search provider with Playwright."""
        # Get base URL from configuration if available
        self.base_url = config_manager.get_setting("api.autotrader_base_url") or self.BASE_URL

        # Get request delay from configuration
        self.request_delay = config_manager.get_setting("search.request_delay") or 1.5

        # Initialize timestamp of last request
        self.last_request_time = 0

        # Playwright settings
        self.headless = config_manager.get_setting("playwright.headless") or True
        self.slow_mo = config_manager.get_setting("playwright.slow_mo")
        self.screenshot_enabled = config_manager.get_setting("playwright.screenshot_enabled") or True
        self.debug_mode = config_manager.get_setting("playwright.debug_mode") or False
        self.timeout = config_manager.get_setting("playwright.timeout") or 30
        self.user_agent = config_manager.get_setting("playwright.user_agent")

        # Viewport settings
        self.viewport_width = config_manager.get_setting("playwright.viewport_width") or 1280
        self.viewport_height = config_manager.get_setting("playwright.viewport_height") or 800

        # Create the debug directories if they don't exist
        self.debug_dir = Path.home() / ".car_search" / "debug"
        os.makedirs(self.debug_dir, exist_ok=True)

        # Ensure Playwright is installed
        if not ensure_playwright_installed():
            logger.error("Playwright or its browsers are not installed. Some features may not work.")

        logger.info(f"Initialized PlaywrightAutoTrader provider with base URL: {self.base_url}")

    def construct_search_url(self, parameters: SearchParameters) -> str:
        """Construct an AutoTrader search URL from the provided parameters.

        Args:
            parameters: Search parameters

        Returns:
            AutoTrader search URL
        """
        # This implementation is the same as the original
        # Convert parameters to URL parameters
        url_params = parameters.to_url_params()

        # Add limit parameter to reduce result set size and improve performance
        url_params["per-page"] = "50"  # Limit to 50 results per page
        url_params["page"] = "1"  # Start with first page

        # Construct query string
        import urllib.parse

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
            
        # Also try a third format with more results per page
        if parameters.postcode:
            alt_url_2 = f"{self.base_url}/car-search?postcode={parameters.postcode}&radius={parameters.radius}"
            if parameters.min_price > 0:
                alt_url_2 += f"&price-from={parameters.min_price}"
            if parameters.max_price < 100000:
                alt_url_2 += f"&price-to={parameters.max_price}"
            if parameters.make and parameters.make.lower() != "any":
                alt_url_2 += f"&make={parameters.make}"
            if parameters.transmission:
                alt_url_2 += f"&transmission={parameters.transmission.lower()}"
            alt_url_2 += "&homeDeliveryAdverts=include&advertising-location=at_cars&page=1&per-page=100"
            urls_to_try.append(alt_url_2)
            
        # Also try a fourth URL format that may return more results
        if parameters.postcode:
            alt_url_3 = f"{self.base_url}/results?radius={parameters.radius}&postcode={parameters.postcode}"
            if parameters.min_price > 0:
                alt_url_3 += f"&price-from={parameters.min_price}"
            if parameters.max_price < 100000:
                alt_url_3 += f"&price-to={parameters.max_price}"
            if parameters.make and parameters.make.lower() != "any":
                alt_url_3 += f"&make={parameters.make.lower()}"
            if parameters.transmission:
                alt_url_3 += f"&transmission={parameters.transmission.lower()}"
            alt_url_3 += "&include-delivery-option=on&quantity-of-doors=2&quantity-of-doors=3&quantity-of-doors=4&quantity-of-doors=5&page=1"
            urls_to_try.append(alt_url_3)

        # Try each URL format
        logger.info(f"Will try {len(urls_to_try)} different URL formats using Playwright")

        # Create screenshot directory for this session
        session_dir = setup_screenshot_directory()
        logger.info(f"Created screenshot directory: {session_dir}")
        
        # Track all listings by ID to avoid duplicates
        all_listings: Dict[str, CarListingData] = {}

        for i, url in enumerate(urls_to_try):
            logger.info(f"Trying URL format {i + 1} with Playwright: {url}")

            # Rate limiting to avoid overloading the server
            self._handle_rate_limit()

            try:
                # Fetch search results page with Playwright
                html_content = await self._fetch_with_playwright(url, session_dir, f"format_{i + 1}")

                if not html_content:
                    logger.error(f"Failed to fetch search results for URL format {i + 1}")
                    continue

                # Log response size to help with debugging
                response_size = len(html_content)
                logger.debug(f"Received response of {response_size} bytes for URL format {i + 1}")

                # Check for error messages or captcha
                error_indicators = ["captcha", "access denied", "too many requests", "blocked"]
                errors_found = [
                    indicator for indicator in error_indicators if indicator.lower() in html_content.lower()
                ]
                if errors_found:
                    logger.error(f"Response contains error indicators: {errors_found}")
                    continue

                # Parse search results
                logger.debug(f"Parsing search results HTML from URL format {i + 1}")
                format_listings = self._parse_search_results(html_content)
                
                # Add unique listings to our result set
                for listing in format_listings:
                    all_listings[listing.id] = listing

                logger.info(f"Found {len(format_listings)} car listings with URL format {i + 1}")
                
                # If we already have a good number of listings, we can stop
                if len(all_listings) >= 50:
                    logger.info(f"Found {len(all_listings)} total listings, stopping search")
                    break
                    
            except Exception as e:
                logger.error(f"Error searching AutoTrader with URL format {i + 1}: {e}")

        # Convert dictionary to list
        listings = list(all_listings.values())
        
        # Post-process listings to filter by price range
        filtered_listings = []
        for listing in listings:
            if parameters.min_price <= listing.price <= parameters.max_price:
                filtered_listings.append(listing)
            else:
                logger.debug(f"Filtered out listing with price {listing.price} (outside range {parameters.min_price}-{parameters.max_price})")
                
        logger.info(f"Final count after price filtering: {len(filtered_listings)} listings (from original {len(listings)})")
                
        # If we have listings after filtering, return them
        if filtered_listings:
            return filtered_listings

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

    async def _fetch_with_playwright(self, url: str, session_dir: Path, screenshot_prefix: str) -> Optional[str]:
        """Fetch content from a URL using Playwright browser automation.

        Args:
            url: URL to fetch
            session_dir: Directory to save screenshots
            screenshot_prefix: Prefix for screenshot filenames

        Returns:
            HTML content as string or None if error
        """
        logger.debug(f"Fetching URL with Playwright: {url}")
        html_content = None

        # Make sure Playwright is installed
        if not ensure_playwright_installed():
            logger.error("Error: Playwright or its browsers are not installed")
            return None

        # Set up browser session
        p, browser, context, page = await setup_browser_session(
            headless=self.headless,
            slow_mo=self.slow_mo,
            user_agent=self.user_agent,
            viewport={"width": self.viewport_width, "height": self.viewport_height},
            session_dir=session_dir,
            debug=self.debug_mode,
        )

        try:
            # Set timeout
            page.set_default_timeout(self.timeout * 1000)  # Convert to ms

            # Go to the URL and wait for network to be idle
            logger.debug(f"Navigating to URL: {url}")
            response = await page.goto(url, wait_until="networkidle")

            if response:
                status = response.status
                logger.debug(f"Page loaded with status: {status}")

                if status == 200:
                    # Handle cookie consent if it appears
                    await self._handle_cookie_consent(page, session_dir, screenshot_prefix)

                    # Wait for the content to load
                    await self._wait_for_content(page)

                    # Take screenshot if enabled
                    if self.screenshot_enabled:
                        screenshot_path = await take_screenshot(page, f"{screenshot_prefix}_results", session_dir)
                        logger.debug(f"Screenshot saved to {screenshot_path}")

                    # Get the page content
                    html_content = await page.content()
                    logger.debug(f"Retrieved HTML content ({len(html_content)} bytes)")
                else:
                    logger.error(f"Error: HTTP {status}")
                    # Take error screenshot
                    if self.screenshot_enabled:
                        await take_screenshot(page, f"{screenshot_prefix}_error_{status}", session_dir)
            else:
                logger.error("No response received")
                # Take error screenshot
                if self.screenshot_enabled:
                    await take_screenshot(page, f"{screenshot_prefix}_error_no_response", session_dir)

        except Exception as e:
            logger.error(f"Error during Playwright execution: {type(e).__name__}: {e}")
            # Take error screenshot
            if self.screenshot_enabled:
                await take_screenshot(page, f"{screenshot_prefix}_error_exception", session_dir)

        finally:
            # Clean up the browser session
            await cleanup_session(p, browser, context, page, session_dir)

        return html_content

    async def _handle_cookie_consent(self, page, session_dir: Path, screenshot_prefix: str) -> None:
        """Handle cookie consent dialogs if they appear.

        Args:
            page: Playwright page object
            session_dir: Directory to save screenshots
            screenshot_prefix: Prefix for screenshot filenames
        """
        try:
            # Take screenshot before handling cookies
            if self.screenshot_enabled:
                await take_screenshot(page, f"{screenshot_prefix}_before_cookies", session_dir)

            # Common cookie consent selectors
            cookie_selectors = [
                "button[data-cmp-clickaccept]",  # Sourcepoint CMP
                "#onetrust-accept-btn-handler",  # OneTrust
                "button[aria-label='Accept all cookies']",
                "button[data-testid='cookieBanner-accept']",
                "button.cookie-notice__agree",
                "button[id*='cookie'][id*='accept']",
                "button.accept-cookies",
                ".cookie-banner .accept",
                "[data-testid='cookie-accept']",
                "[data-tracking-label='cookie-accept']",
                "button:has-text('Accept')",
                "button:has-text('Accept All')",
                "button:has-text('Accept Cookies')",
            ]

            # Try each selector
            for selector in cookie_selectors:
                try:
                    # Check if the element exists and is visible
                    is_visible = await page.is_visible(selector, timeout=2000)
                    if is_visible:
                        logger.info(f"Found cookie consent element with selector: {selector}")

                        # Take screenshot of the cookie dialog
                        if self.screenshot_enabled:
                            await take_screenshot(page, f"{screenshot_prefix}_cookie_dialog", session_dir)

                        # Click the button
                        await page.click(selector)
                        logger.info("Clicked cookie consent button")

                        # Wait a moment for the dialog to disappear
                        await page.wait_for_timeout(1000)

                        # Take screenshot after handling cookies
                        if self.screenshot_enabled:
                            await take_screenshot(page, f"{screenshot_prefix}_after_cookies", session_dir)

                        return
                except Exception as e:
                    # Just log and continue to the next selector
                    logger.debug(f"Cookie selector {selector} failed: {e}")

            logger.debug("No cookie consent dialog found or interacted with")

        except Exception as e:
            logger.error(f"Error handling cookie consent: {e}")

    async def _wait_for_content(self, page) -> None:
        """Wait for the page content to fully load.

        Args:
            page: Playwright page object
        """
        try:
            # Wait for search results to load - try different selectors
            result_selectors = [
                "article.product-card",
                "div.product-card",
                "div[data-testid='search-card']",
                "article[data-testid]",
                "li.search-page__result",
                "li.product-card",
                "li[data-testid*='search-card']",
                "article.advert-card",
                "div.search-results__result",
            ]

            for selector in result_selectors:
                try:
                    # Check if the selector exists on the page
                    is_visible = await page.is_visible(selector, timeout=2000)
                    if is_visible:
                        logger.debug(f"Found content with selector: {selector}")
                        # Wait for multiple items to appear (to ensure results have loaded)
                        await page.wait_for_selector(f"{selector}:nth-child(3)", timeout=5000)
                        return
                except Exception:
                    # Continue to next selector if this one doesn't work
                    continue

            # If no specific selector worked, wait a moment to ensure page has loaded
            logger.debug("No specific content selector found, waiting for page to settle")
            await page.wait_for_timeout(5000)

        except Exception as e:
            logger.error(f"Error waiting for content: {e}")
            # Just continue - we'll try to parse whatever content is available

    def _parse_search_results(self, html_content: str) -> List[CarListingData]:
        """Parse search results from HTML content.

        Args:
            html_content: HTML content to parse

        Returns:
            List of car listing data objects
        """
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        listings = []

        # Log page title for debugging
        title = soup.title.text if soup.title else "No title"
        logger.info(f"Page title: {title}")
        
        # Check for specific AutoTrader text that indicates the number of matches
        search_results_text = None
        for text_pattern in ["found", "cars for sale", "vehicles"]:
            elements = soup.find_all(string=re.compile(text_pattern, re.IGNORECASE))
            for el in elements:
                if re.search(r'\d+', el):
                    search_results_text = el.strip()
                    logger.info(f"Found search results text: {search_results_text}")
                    break
            if search_results_text:
                break
        
        # First, try to find main search results container
        main_container = None
        container_selectors = [
            "div[data-testid='search-results']",
            "div#search-results",
            "section.search-results",
            "ul.search-results",
            "div.search-page__results",
            "div[data-orientation='vertical']",
            "main"
        ]
        
        for selector in container_selectors:
            container = soup.select_one(selector)
            if container:
                logger.info(f"Found main results container with selector: {selector}")
                main_container = container
                break
                
        # If we found a main container, use it as the base for our search
        base = main_container if main_container else soup
        
        # Updated list of selectors to try for latest AutoTrader website
        # Try multiple selectors to find listing items
        selectors = [
            # Most specific selectors first - 2025 AutoTrader structure
            "div[data-testid='search-card']",
            "li[data-testid='search-card']", 
            "article[data-testid='search-card']",
            
            # Class-based selectors
            "div.search-result",
            "section.search-result",
            "article.search-result",
            "li.search-result",
            "div.advert-card",
            "article.advert-card",
            "div.product-card",
            "article.product-card",
            
            # More generic attribute-based selectors
            "div[id^='card-']",
            "div[data-testid*='advert']",
            "article[data-testid*='advert']",
            "div[data-item-index]",
            
            # Very generic selectors as last resort
            "div:has(a[href*='/car-details/'])",
            "div:has(a[href*='/classified/advert/'])",
            "li:has(a[href*='/car-details/'])",
            "article:has(a[href*='/car-details/'])",
            "div:has(h2, h3):has(a[href*='/car-details/'])"
        ]

        # Try each selector until we find listings
        for selector in selectors:
            # Use the main container as the base for our search if available
            listing_items = base.select(selector) if base != soup else soup.select(selector)
            
            if listing_items:
                logger.info(f"Found {len(listing_items)} listings with selector: {selector}")

                # Process listing items
                for item in listing_items:
                    car_data = self._extract_listing_data(item)
                    if car_data:
                        listings.append(car_data)

                # If we found any valid listings, break the loop
                if listings:
                    break

        # If we didn't find enough results, try a more direct approach
        if len(listings) < 10:
            logger.debug(f"Only found {len(listings)} listings with CSS selectors. Trying direct link extraction.")
            
            # Look for all links that might be car listings
            car_links = base.select("a[href*='/car-details/'], a[href*='/classified/advert/']")
            
            # Build a mapping of URLs to card elements
            url_to_card = {}
            
            for link in car_links:
                href = link.get('href', '')
                if href and href not in url_to_card:
                    # Find the parent "card" - typical pattern is a card with a link inside
                    # Try to find a parent within a reasonable depth (4 levels up)
                    card = link
                    for _ in range(4):
                        if card.parent:
                            card = card.parent
                            # Look for typical card attributes - classes or data attributes
                            card_attrs = card.get('class', [])
                            card_id = card.get('id', '')
                            card_data = [attr for attr in card.attrs.keys() if attr.startswith('data-')]
                            
                            # If it looks like a card element, use it
                            if (any(c for c in card_attrs if 'card' in c.lower() or 'result' in c.lower() or 'advert' in c.lower()) or
                                ('card' in card_id.lower()) or 
                                any('card' in d.lower() or 'result' in d.lower() or 'advert' in d.lower() for d in card_data)):
                                url_to_card[href] = card
                                break
                    
                    # If we couldn't find a card parent, use the link's immediate parent
                    if href not in url_to_card and link.parent:
                        url_to_card[href] = link.parent

            # Process these potential listings
            if url_to_card:
                logger.info(f"Found {len(url_to_card)} potential listings via direct link extraction")
                for href, element in url_to_card.items():
                    car_data = self._extract_listing_data(element)
                    if car_data:
                        # Only add if not a duplicate
                        if not any(listing.id == car_data.id for listing in listings):
                            listings.append(car_data)

        # Debug HTML structure if no listings found or very few
        if len(listings) < 5:
            self._debug_html_structure(soup)
            # Save HTML structure to a file for debugging
            debug_file = self.debug_dir / f"autotrader_html_structure_{int(time.time())}.html"
            try:
                sample_html = str(soup.body)[:10000] if soup.body else str(soup)[:10000]  # First 10000 chars
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(sample_html)
                logger.debug(f"Saved HTML structure sample to {debug_file}")
            except Exception as e:
                logger.error(f"Failed to save HTML structure: {e}")

        logger.info(f"Total listings found: {len(listings)}")
        # Return the listings found
        return listings

    def _debug_html_structure(self, soup: BeautifulSoup):
        """Extract and log information about the HTML structure for debugging.

        Args:
            soup: BeautifulSoup object
        """
        logger.debug("===== PAGE STRUCTURE ANALYSIS =====")

        # Check page title
        title = soup.title.text if soup.title else "No title"
        logger.debug(f"Page title: {title}")

        # Check for error indicators
        error_words = ["captcha", "access denied", "blocked", "too many requests"]
        if any(word in title.lower() for word in error_words):
            logger.warning(f"Title contains error indicators: {title}")

        # Look for search-related text
        search_text = soup.find(string=re.compile(r"(found|results|cars|vehicles)", re.IGNORECASE))
        if search_text:
            logger.debug(f"Found search-related text: {search_text.strip()}")

        # Find main content containers
        logger.debug("Main containers:")
        for tag in ["main", "div[role='main']", "div.container", "div.search-results"]:
            elements = soup.select(tag)
            if elements:
                logger.debug(f"  Found {len(elements)} '{tag}' elements")

        # Find lists that might contain results
        logger.debug("Potential result lists:")
        list_elements = soup.select("ul, ol")
        for i, ul in enumerate(list_elements[:5]):  # Check first 5 lists
            classes = ul.get("class", [])
            items = ul.select("li")
            logger.debug(f"  List {i + 1}: class='{' '.join(classes)}', items={len(items)}")

    def _extract_listing_data(self, listing_item) -> Optional[CarListingData]:
        """Extract car listing data from a listing item.

        Args:
            listing_item: BeautifulSoup object representing a listing item

        Returns:
            CarListingData object or None if extraction failed
        """
        try:
            # Deep debug - print HTML of the item for first few items
            debug_element_count = getattr(self, "_debug_element_count", 0)
            if debug_element_count < 3:
                logger.debug(f"Listing item HTML sample: {str(listing_item)[:200]}...")
                self._debug_element_count = debug_element_count + 1

            # Extract the listing URL
            all_links = listing_item.select("a[href]")
            link_element = None
            
            # First try to find car detail links
            for link in all_links:
                href = link.get("href", "")
                if '/car-details/' in href or '/classified/advert/' in href:
                    link_element = link
                    break
            
            # If no car detail link found, use the first link
            if not link_element and all_links:
                link_element = all_links[0]
                
            # If this is already a link element, use it directly
            if not link_element and listing_item.name == 'a' and listing_item.has_attr('href'):
                link_element = listing_item
                
            if not link_element:
                logger.debug("Could not find link element in listing item")
                return None

            href = link_element.get("href", "")
            if not href:
                logger.debug("Empty href in listing item")
                return None

            # Construct full URL if needed
            if href.startswith("/"):
                full_url = f"{self.base_url}{href}"
            else:
                full_url = href

            # Extract listing ID from URL
            listing_id = self._extract_id_from_url(full_url)
            if not listing_id:
                logger.debug(f"Could not extract ID from URL: {full_url}")
                return None

            # Extract all the text from the listing for backup parsing
            all_text = listing_item.get_text(strip=True)
            logger.debug(f"All text from listing: {all_text[:100]}...")

            # Extract the image URL if available
            image_url = None
            img_elements = listing_item.select("img[src]")
            if img_elements:
                for img in img_elements:
                    src = img.get("src", "")
                    if src and ('jpg' in src or 'jpeg' in src or 'png' in src):
                        # Convert to full URL if needed
                        if src.startswith("//"):
                            image_url = f"https:{src}"
                        elif src.startswith("/"):
                            image_url = f"{self.base_url}{src}"
                        else:
                            image_url = src
                        break
            
            # Extract title - try multiple patterns
            
            # 1. First look for heading elements
            title = ""
            for title_selector in ["h2", "h3", "h4", "[data-testid*='title']", ".title", ".vehicle-title", ".listing-title"]:
                title_elements = listing_item.select(title_selector)
                for title_element in title_elements:
                    # Check if the title element is not a button or hidden element
                    if not title_element.select_one("button") and not "hidden" in ' '.join(title_element.get('class', [])):
                        title_text = title_element.get_text(strip=True)
                        if title_text and len(title_text) > 5:  # Must be a reasonable title
                            title = title_text
                            break
                if title:
                    break
            
            # 2. Then look for title attribute on links or images
            if not title:
                for element in listing_item.select("[title]"):
                    title_attr = element.get("title", "")
                    if title_attr and len(title_attr) > 5:
                        title = title_attr
                        break
            
            # 3. If still no title, try link text from the main car link
            if not title and link_element:
                link_text = link_element.get_text(strip=True)
                if link_text and len(link_text) > 5:
                    title = link_text
            
            # 4. If still no title, check the alt text of images
            if not title:
                for img in img_elements:
                    alt_text = img.get("alt", "")
                    if alt_text and len(alt_text) > 5:
                        title = alt_text
                        break
            
            # Extract make, model, and year from title
            make, model, year = self._extract_make_model_year(title)
            
            # If we couldn't extract a reasonable make/model from the title, try extracting directly
            # Car makes are often in specific elements or classes
            if not make or make == "Unknown Make":
                for make_selector in [".make", "[data-testid*='make']", ".vehicle-make"]:
                    make_element = listing_item.select_one(make_selector)
                    if make_element:
                        make_text = make_element.get_text(strip=True)
                        if make_text:
                            make = make_text
                            break
            
            # Extract price - try multiple approaches
            
            # 1. Look for specific price elements with price formatting (£)
            price = 0
            price_text = ""
            
            price_selectors = [
                ".price", 
                "[data-testid*='price']", 
                ".vehicle-price", 
                "*[itemprop='price']",
                ".advert-price",
                ".product-card-pricing__price",
                ".atc-type-insignia", # Common AutoTrader price class
                "span:contains('£')"
            ]
            
            for price_selector in price_selectors:
                price_elements = listing_item.select(price_selector)
                for price_element in price_elements:
                    text = price_element.get_text(strip=True)
                    if '£' in text or 'GBP' in text:
                        price_text = text
                        break
                if price_text:
                    break
            
            # 2. If no price found with selectors, try regex on all text
            if not price_text:
                price_match = re.search(r'£([0-9,]+)', all_text)
                if price_match:
                    price_text = f"£{price_match.group(1)}"
            
            if price_text:
                price = self._extract_price(price_text)
            
            # Try to find a reasonable price if we still don't have one
            if price <= 0:
                # Look for any number sequence that might be a price
                price_match = re.search(r'(^|\s)(\d{1,3}(?:,\d{3})+|\d{4,})(\s|$)', all_text)
                if price_match:
                    price = float(price_match.group(2).replace(',', ''))
                    # Only use if it seems like a car price (between £500 and £100,000)
                    if not (500 <= price <= 100000):
                        price = 500  # Default
            
            # Extract mileage and other specs
            specs_texts = []
            
            # Try to find spec elements with multiple selectors
            for spec_selector in [".spec", "[data-testid*='spec']", ".key-specs", ".vehicle-attr", ".listing-key-specs"]:
                specs_elements = listing_item.select(spec_selector)
                if specs_elements:
                    specs_texts = [spec.get_text(strip=True) for spec in specs_elements]
                    break
            
            # If we couldn't find specific spec elements, try extracting from general text
            if not specs_texts:
                # Find mileage
                mileage_match = re.search(r"(\d{1,3}(?:,\d{3})*)\s*miles", all_text, re.IGNORECASE)
                if mileage_match:
                    specs_texts.append(f"{mileage_match.group(1)} miles")
                
                # Look for fuel type
                for fuel in ["Petrol", "Diesel", "Hybrid", "Electric"]:
                    if fuel.lower() in all_text.lower():
                        specs_texts.append(fuel)
                        break
                
                # Look for transmission
                for transmission in ["Manual", "Automatic"]:
                    if transmission.lower() in all_text.lower():
                        specs_texts.append(transmission)
                        break

            # Extract mileage, fuel type, transmission
            mileage, fuel_type, transmission = self._extract_specs(specs_texts)

            # Extract location - first try to find it in the listing
            location = ""
            for location_selector in [".seller-location", ".location", "[data-testid*='location']", 
                                     ".dealer-location", ".retailer-town"]:
                location_element = listing_item.select_one(location_selector)
                if location_element:
                    location = location_element.get_text(strip=True)
                    if location:
                        break

            # If no location found, try to extract from all text
            if not location:
                # Look for common location patterns in UK
                location_match = re.search(r"(in|near|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", all_text)
                if location_match:
                    location = location_match.group(2)
            
            # If still no location, use postcode from search parameters as fallback
            if not location:
                location = "Unknown location"

            # Ensure we have non-empty values for required fields
            if not make or make == "Unknown Make":
                make = "Unknown"
            
            if not model or model == "Unknown Model":
                model = "Car"
                
            if year <= 0:
                year = 2000  # Default year if none detected
                
            try:
                car_data = CarListingData(
                    id=listing_id,
                    title=title,
                    listing_url=full_url,
                    location=location,
                    price=price if price > 0 else 500,  # Default price of 500 if none found
                    mileage=mileage if mileage > 0 else 50000,  # Default mileage
                    make=make,
                    model=model,
                    year=year,
                    fuel_type=fuel_type or "Petrol",  # Default to Petrol if none found
                    transmission=transmission or "Manual",  # Default to Manual if none found
                )
                
                logger.info(f"Successfully extracted data for {make} {model}, £{price}")
                return car_data
            except Exception as e:
                logger.error(f"CarListingData validation error: {e}")
                # If we get validation errors, try with more defaults
                try:
                    car_data = CarListingData(
                        id=listing_id,
                        title=title or "Car Listing",
                        listing_url=full_url,
                        location=location or "Unknown location",
                        price=500,  # Default price
                        mileage=50000,  # Default mileage
                        make="Unknown", 
                        model="Car",
                        year=2000,  # Default year
                        fuel_type="Petrol",  # Default fuel
                        transmission="Manual",  # Default transmission
                    )
                    
                    logger.info(f"Created car data with defaults due to validation error")
                    return car_data
                except Exception as inner_e:
                    logger.error(f"Failed to create car data even with defaults: {inner_e}")
                    return None

        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None

    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract listing ID from URL.

        Args:
            url: URL to extract ID from

        Returns:
            Listing ID or None if extraction failed
        """
        # Pattern for AutoTrader URLs
        patterns = [
            r"/car-details/(\d+)",  # New format: /car-details/123456789
            r"/classified/advert/(\d+)",  # Old format: /classified/advert/123456789
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def _extract_make_model_year(self, title: str) -> tuple:
        """Extract make, model, and year from title.

        Args:
            title: Title to extract from

        Returns:
            Tuple of (make, model, year)
        """
        # Default values
        make = "Unknown Make"
        model = "Unknown Model"
        year = 0

        try:
            logger.debug(f"Extracting make/model/year from title: '{title}'")
            
            # Skip extraction if title is empty or too short
            if not title or len(title) < 3:
                return make, model, year
                
            # Common car makes to look for at the beginning of the title
            common_makes = [
                "ford",
                "vauxhall",
                "volkswagen",
                "vw",
                "bmw",
                "audi",
                "mercedes",
                "mercedes-benz",
                "toyota",
                "nissan",
                "honda",
                "mazda",
                "kia",
                "hyundai",
                "seat",
                "skoda",
                "renault",
                "peugeot",
                "citroen",
                "fiat",
                "volvo",
                "lexus",
                "mini",
                "land rover",
                "range rover",
                "jaguar",
                "mitsubishi",
                "suzuki",
                "dacia",
                "jeep",
                "porsche",
                "tesla",
                "mg",
            ]

            # Clean the title
            clean_title = title.lower()

            # Pattern for AutoTrader - they often use "View details of the {YEAR} {MAKE} {MODEL}"
            # or "New & used {MAKE} {MODEL} cars for sale"
            view_details_match = re.search(r"view details of the (\d{4}) ([a-zA-Z\-]+) (.+?)(?:\s|$)", clean_title)
            new_used_match = re.search(r"new & used ([a-zA-Z\-]+) (.+?) cars for sale", clean_title)
            
            if view_details_match:
                year = int(view_details_match.group(1))
                make = view_details_match.group(2).capitalize()
                model = view_details_match.group(3).strip().capitalize()
                return make, model, year
                
            if new_used_match:
                make = new_used_match.group(1).capitalize()
                model = new_used_match.group(2).strip().capitalize()
                # Year is unknown in this format
                return make, model, year

            # Extract the make - try to find a car make in the title
            found_make = False
            for car_make in common_makes:
                make_pattern = r'(^|\s)' + re.escape(car_make) + r'($|\s)'
                if re.search(make_pattern, clean_title, re.IGNORECASE):
                    make = car_make.capitalize()
                    # For special cases
                    if make.lower() == "vw":
                        make = "Volkswagen"
                    elif make.lower() == "mercedes" or make.lower() == "mercedes-benz":
                        make = "Mercedes-Benz"
                    found_make = True
                    break

            # Extract the year - look for 4-digit years between 1980 and current year
            import datetime

            current_year = datetime.datetime.now().year
            year_pattern = r"\b(19[89]\d|20[0-2]\d)\b"  # Years from 1980 to 2029
            year_match = re.search(year_pattern, title)
            if year_match:
                year = int(year_match.group(1))
                if year > current_year:
                    year = 0  # Invalid future year

            # Extract the model if we found a make
            if found_make:
                # Remove the make from the title to help extract the model
                without_make = re.sub(r'(^|\s)' + re.escape(make.lower()) + r'($|\s)', ' ', clean_title, flags=re.IGNORECASE)

                # Remove the year if found
                if year:
                    without_make = without_make.replace(str(year), " ").strip()

                # Remove common words
                words_to_remove = [
                    "new",
                    "used",
                    "for sale",
                    "automatic",
                    "manual",
                    "petrol",
                    "diesel",
                    "hybrid",
                    "electric",
                    "view",
                    "details",
                    "of",
                    "the",
                    "cars",
                ]
                for word in words_to_remove:
                    without_make = re.sub(r'(^|\s)' + re.escape(word) + r'($|\s)', ' ', without_make, flags=re.IGNORECASE)

                # Remove punctuation and clean up
                without_make = re.sub(r"[^\w\s]", " ", without_make)
                without_make = re.sub(r"\s+", " ", without_make).strip()

                # Take the first 2-3 words as the model if there's anything left
                if without_make:
                    model_parts = without_make.split()[:3]
                    model = " ".join(model_parts).title() if model_parts else "Unknown Model"
                else:
                    model = "Unknown Model"
            
            logger.debug(f"Extracted make='{make}', model='{model}', year={year}")

        except Exception as e:
            logger.error(f"Error extracting make/model/year from title: {e}")

        return make, model, year

    def _extract_price(self, price_text: str) -> float:
        """Extract price as float from price text.

        Args:
            price_text: Price text to extract from

        Returns:
            Price as float
        """
        try:
            # Extract numeric part using regex
            price_match = re.search(r"£([0-9,]+)", price_text)
            if price_match:
                # Remove commas and convert to float
                price_str = price_match.group(1).replace(",", "")
                return float(price_str)

            # Try alternative format
            price_match = re.search(r"([0-9,]+)\s*pounds", price_text, re.IGNORECASE)
            if price_match:
                price_str = price_match.group(1).replace(",", "")
                return float(price_str)

            return 0.0
        except Exception as e:
            logger.error(f"Error extracting price from text '{price_text}': {e}")
            return 0.0

    def _extract_mileage(self, mileage_text: str) -> int:
        """Extract mileage as integer from mileage text.

        Args:
            mileage_text: Mileage text to extract from

        Returns:
            Mileage as integer
        """
        try:
            # Extract numeric part using regex
            mileage_match = re.search(r"([0-9,]+)\s*miles", mileage_text, re.IGNORECASE)
            if mileage_match:
                # Remove commas and convert to int
                mileage_str = mileage_match.group(1).replace(",", "")
                return int(mileage_str)

            # For cases where just the number is provided
            number_only_match = re.match(r"^([0-9,]+)$", mileage_text.strip())
            if number_only_match:
                mileage_str = number_only_match.group(1).replace(",", "")
                return int(mileage_str)

            return 0
        except Exception as e:
            logger.error(f"Error extracting mileage from text '{mileage_text}': {e}")
            return 0

    def _extract_specs(self, specs: List[str]) -> tuple:
        """Extract specifications from a list of spec strings.

        Args:
            specs: List of specification strings

        Returns:
            Tuple of (mileage, fuel_type, transmission)
        """
        mileage = 0
        fuel_type = ""
        transmission = ""

        for spec in specs:
            spec_lower = spec.lower()

            # Extract mileage
            if "miles" in spec_lower and not mileage:
                mileage = self._extract_mileage(spec)

            # Extract fuel type
            fuel_types = ["petrol", "diesel", "hybrid", "electric", "plug-in hybrid"]
            for fuel in fuel_types:
                if fuel in spec_lower and not fuel_type:
                    fuel_type = fuel.capitalize()
                    break

            # Extract transmission
            if "manual" in spec_lower and not transmission:
                transmission = "Manual"
            elif "automatic" in spec_lower and not transmission:
                transmission = "Automatic"

        return mileage, fuel_type, transmission

    def _handle_rate_limit(self):
        """Handle rate limiting to avoid overloading the server."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _create_test_results(self, parameters: SearchParameters) -> List[CarListingData]:
        """Create test results for testing and development.

        Args:
            parameters: Search parameters

        Returns:
            List of test car listing data objects
        """
        # This method remains the same as the original, creating test data
        makes = ["Ford", "Vauxhall", "Volkswagen", "Toyota", "BMW"]
        models = {
            "Ford": ["Fiesta", "Focus", "Mondeo", "Puma", "Kuga"],
            "Vauxhall": ["Corsa", "Astra", "Insignia", "Mokka", "Crossland"],
            "Volkswagen": ["Golf", "Polo", "Passat", "Tiguan", "T-Roc"],
            "Toyota": ["Yaris", "Corolla", "Prius", "RAV4", "Aygo"],
            "BMW": ["1 Series", "3 Series", "5 Series", "X3", "X5"],
        }
        years = list(range(2010, 2024))
        fuel_types = ["Petrol", "Diesel", "Hybrid", "Electric"]
        transmissions = ["Manual", "Automatic"]

        import random

        test_results = []

        # Filter by make if specified
        available_makes = [parameters.make] if parameters.make and parameters.make.lower() != "any" else makes

        # Create 10-20 random listings
        num_listings = random.randint(10, 20)

        for i in range(num_listings):
            # Select a make
            make = random.choice(available_makes)

            # Select a model based on make
            model = random.choice(models.get(make, ["Model"]))

            # Generate random year within range
            min_year = parameters.min_year if parameters.min_year > 0 else 2010
            max_year = parameters.max_year if parameters.max_year < 2024 else 2023

            if min_year > max_year:
                min_year, max_year = max_year, min_year

            year = random.randint(min_year, max_year)

            # Generate random mileage based on age
            age = 2023 - year
            base_mileage = age * 10000  # 10k miles per year
            variation = random.uniform(0.7, 1.3)  # 30% variation
            mileage = int(base_mileage * variation)

            # Generate random price within range
            min_price = parameters.min_price if parameters.min_price > 0 else 1000
            max_price = parameters.max_price if parameters.max_price < 100000 else 30000

            if min_price > max_price:
                min_price, max_price = max_price, min_price

            # Adjust price based on age and model
            base_price = random.randint(min_price, max_price)
            model_factor = 1.0
            if "Series" in model or model in ["X3", "X5", "Mondeo", "Passat"]:
                model_factor = 1.2  # Premium models cost more

            price = base_price * model_factor

            # Select random fuel type and transmission
            # Respect transmission parameter if provided
            transmission_options = [parameters.transmission] if parameters.transmission else transmissions
            transmission = random.choice(transmission_options)

            fuel_type = random.choice(fuel_types)

            # Create a unique ID
            listing_id = f"test_{i}_{int(time.time())}"

            # Create title
            title = f"{year} {make} {model} {fuel_type} {transmission}"

            # Create URL
            url = f"https://www.autotrader.co.uk/car-details/{listing_id}"

            # Create car listing data
            car_data = CarListingData(
                id=listing_id,
                title=title,
                url=url,
                price=price,
                mileage=mileage,
                make=make,
                model=model,
                year=year,
                fuel_type=fuel_type,
                transmission=transmission,
            )

            test_results.append(car_data)

        logger.info(f"Created {len(test_results)} test results")
        return test_results
