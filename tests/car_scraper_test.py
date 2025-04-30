#!/usr/bin/env python3
"""
Car Search Scraper Test Script

A simplified test script to experiment with web scraping for car listings using Playwright.
This script takes a URL and attempts to extract car listings using different selectors.
"""

import asyncio
import json
import os
import re

# Import our Playwright utilities
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.car_search.data.search_providers_playwright import PlaywrightAutoTraderProvider
from src.car_search.models.search_parameters import SearchParameters
from src.utils.playwright_utils import (
    cleanup_session,
    ensure_playwright_installed,
    setup_browser_session,
    setup_screenshot_directory,
    take_screenshot,
)

# ====================== CONFIGURATION OPTIONS ======================
# Set your test URL here (copy and paste from browser)
TEST_URL = "https://www.autotrader.co.uk/car-search?postcode=BT73fn&radius=10&make=Ford&price-to=2500&homeDeliveryAdverts=exclude&advertising-location=at_cars&page=1"

# Output configuration
OUTPUT_DIR = Path("autotrader_output")
JSON_OUTPUT_PATH = OUTPUT_DIR / "car_listings.json"

# Request Configuration
REQUEST_DELAY = 1.5  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds before timeout
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Browser options
HEADLESS = False  # Run browser in headless mode (no visible UI) - False for debugging
SLOW_MO = 50  # Slow down execution by 50ms (useful for debugging)
SCREENSHOT = True  # Take screenshots of pages

# Debug options
SAVE_HTML = True  # Save the raw HTML for debugging
HTML_OUTPUT_FILE = "scraper_debug.html"
PRINT_PAGE_STRUCTURE = True  # Print the basic page structure

# Search Parameters for testing
TEST_POSTCODE = "BT73FN"
TEST_RADIUS = 10
TEST_MIN_PRICE = 0
TEST_MAX_PRICE = 2500
TEST_MAKE = "Ford"
TEST_TRANSMISSION = None

# ====================== HELPER FUNCTIONS ======================


async def fetch_with_playwright(url: str, session_dir: Path) -> Optional[str]:
    """Fetch content from a URL using Playwright browser automation."""
    print(f"Fetching URL with Playwright: {url}")
    html_content = None

    # Make sure Playwright is installed
    if not ensure_playwright_installed():
        print("Error: Playwright or its browsers are not installed")
        return None

    # Set up browser session
    p, browser, context, page = await setup_browser_session(
        headless=HEADLESS, slow_mo=SLOW_MO, user_agent=USER_AGENT, session_dir=session_dir, debug=True
    )

    try:
        # Set timeout
        page.set_default_timeout(REQUEST_TIMEOUT * 1000)  # Convert to ms

        # Go to the URL and wait for network to be idle
        print(f"Navigating to URL: {url}")
        response = await page.goto(url, wait_until="networkidle")

        if response:
            status = response.status
            print(f"Page loaded with status: {status}")

            if status == 200:
                # Take screenshot if enabled
                if SCREENSHOT:
                    await take_screenshot(page, "search_results", session_dir)
                    print(f"Screenshot saved to {session_dir}")

                # Get the page content
                html_content = await page.content()
                print(f"Retrieved HTML content ({len(html_content)} bytes)")
            else:
                print(f"Error: HTTP {status}")
                # Take error screenshot
                await take_screenshot(page, f"error_{status}", session_dir)
        else:
            print("No response received")
            # Take error screenshot
            await take_screenshot(page, "error_no_response", session_dir)

    except Exception as e:
        print(f"Error during Playwright execution: {type(e).__name__}: {e}")
        # Take error screenshot
        await take_screenshot(page, "error_exception", session_dir)

    finally:
        # Clean up the browser session
        await cleanup_session(p, browser, context, page, session_dir)

    return html_content


def debug_html_structure(soup: BeautifulSoup) -> None:
    """Extract and print information about the HTML structure for debugging."""
    print("\n===== PAGE STRUCTURE ANALYSIS =====")

    # Check page title
    title = soup.title.text if soup.title else "No title"
    print(f"Page title: {title}")

    # Check for error indicators
    error_words = ["captcha", "access denied", "blocked", "too many requests"]
    if any(word in title.lower() for word in error_words):
        print(f"WARNING: Title contains error indicators: {title}")

    # Look for search-related text
    search_text_element = soup.find(string=re.compile(r"(found|results|cars|vehicles)", re.IGNORECASE))
    if search_text_element:
        if hasattr(search_text_element, "strip"):
            print(f"Found search-related text: {search_text_element.strip()}")
        else:
            print("Found search-related text element (cannot strip)")

    # Find main content containers
    print("\nMain containers:")
    for tag in ["main", "div[role='main']", "div.container", "div.search-results"]:
        elements = soup.select(tag)
        if elements:
            print(f"  Found {len(elements)} '{tag}' elements")

    # Find lists that might contain results
    print("\nPotential result lists:")
    list_elements = soup.select("ul, ol")
    for i, ul in enumerate(list_elements[:5]):  # Check first 5 lists
        classes = ul.get("class")
        class_str = " ".join(classes) if classes else ""
        items = ul.select("li")
        print(f"  List {i + 1}: class='{class_str}', items={len(items)}")

        # If list has items, check the first one
        if items and i < 3:  # Only check first 3 lists in detail
            first_item = items[0]
            item_classes = first_item.get("class")
            item_class_str = " ".join(item_classes) if item_classes else ""
            links = first_item.select("a[href]")
            images = first_item.select("img")
            print(f"    First item: class='{item_class_str}', links={len(links)}, images={len(images)}")

            # Check for car-related content
            text = first_item.get_text(" ", strip=True)
            if len(text) > 100:
                text = text[:100] + "..."
            print(f"    Text: {text}")


def parse_search_results(html_content: str) -> List[Dict[str, Any]]:
    """Parse search results from HTML content using multiple selectors."""
    soup = BeautifulSoup(html_content, "html.parser")
    listings = []

    # Save HTML content for debugging if enabled
    if SAVE_HTML:
        with open(HTML_OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Saved HTML content to {HTML_OUTPUT_FILE}")

    # Print debug info about page structure if enabled
    if PRINT_PAGE_STRUCTURE:
        debug_html_structure(soup)

    # Try multiple selectors for search results
    selectors = [
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
    ]

    for selector in selectors:
        listing_items = soup.select(selector)
        if listing_items:
            print(f"\nFound {len(listing_items)} listings with selector: '{selector}'")

            # Process first few items (limit to 5 for readable output)
            for i, item in enumerate(listing_items[:5]):
                try:
                    # Extract basic info
                    listing = {}

                    # Try to find the link to details
                    link_element = item.select_one("a[href]")
                    if link_element:
                        href = link_element.get("href", "")
                        if isinstance(href, str) and href:
                            listing["url"] = href if href.startswith("http") else f"https://www.autotrader.co.uk{href}"

                    # Try to find the title
                    title_candidates = [
                        item.select_one("h2, h3"),
                        item.select_one("[data-testid*='title']"),
                        item.select_one(".title, .vehicle-title"),
                        link_element,
                    ]
                    for candidate in title_candidates:
                        if candidate and candidate.get_text(strip=True):
                            listing["title"] = candidate.get_text(strip=True)
                            break

                    # Try to find the price
                    price_candidates = [
                        item.select_one("[data-testid*='price'], .price, .vehicle-price, .advert-price"),
                        item.select_one("p:contains('£'), span:contains('£')"),
                    ]
                    for candidate in price_candidates:
                        if candidate and "£" in candidate.get_text():
                            price_text = candidate.get_text(strip=True)
                            # Extract price number
                            price_match = re.search(r"£([0-9,]+)", price_text)
                            if price_match:
                                price_value = price_match.group(1).replace(",", "")
                                listing["price"] = f"£{price_value}"
                            else:
                                listing["price"] = price_text
                            break

                    # Try to find the key specs
                    specs_candidates = [
                        item.select(".specs li, .key-specs li, .specification-item, [data-testid*='spec']"),
                        item.select(".product-card-details__specification li, .vehicle-attributes__text, div.spec"),
                    ]
                    for candidates in specs_candidates:
                        if candidates:
                            specs = [spec.get_text(strip=True) for spec in candidates]
                            listing["specs"] = specs
                            break

                    # Add to listings
                    if listing.get("title") and listing.get("url"):
                        listings.append(listing)
                        print(f"  {i + 1}. {listing.get('title', 'No Title')} - {listing.get('price', 'No Price')}")
                        if "specs" in listing:
                            print(
                                f"     Specs: {', '.join(listing['specs'][:3])}{'...' if len(listing['specs']) > 3 else ''}"
                            )

                except Exception as e:
                    print(f"Error extracting listing {i}: {e}")

            # If we found any listings with this selector, stop trying others
            if listings:
                break

    return listings


async def extract_with_js(page) -> List[Dict[str, Any]]:
    """Extract data using JavaScript directly in the browser context."""
    print("Extracting data from page using browser JavaScript execution")

    # This JavaScript extracts car listing data directly from the DOM
    js_extract = """
    () => {
        const getTextContent = (element, selector) => {
            if (!element) return null;
            const el = selector ? element.querySelector(selector) : element;
            return el ? el.textContent.trim() : null;
        };
        
        // Try multiple selectors for car listings
        const selectors = [
            'li.search-page__result',
            'article.product-card',
            'div.search-result',
            'div.car-details',
            'div.advert-card',
            'li[data-testid*=product-card]',
            '[data-testid="search-results"] > div',
            '.search-page__results > div',
            'main li'
        ];
        
        let listingElements = [];
        
        // Try each selector
        for (const selector of selectors) {
            const elements = document.querySelectorAll(selector);
            if (elements && elements.length > 0) {
                console.log(`Found ${elements.length} elements with selector: ${selector}`);
                listingElements = Array.from(elements);
                break;
            }
        }
        
        // Extract data from each listing
        return listingElements.map(listing => {
            // Try various selectors for title
            const titleSelectors = ['h3', 'h2', '[data-testid*="title"]', '.product-card-details__title'];
            let title = null;
            for (const selector of titleSelectors) {
                title = getTextContent(listing, selector);
                if (title) break;
            }
            
            // Try various selectors for price
            const priceSelectors = ['[data-testid*="price"]', '.product-card-pricing__price', '.vehicle-price'];
            let price = null;
            for (const selector of priceSelectors) {
                price = getTextContent(listing, selector);
                if (price) break;
            }
            
            // Extract details/specs
            const specSelectors = ['.key-specifications__item', '.key-specs', '.listing-key-specs'];
            let details = [];
            for (const selector of specSelectors) {
                const specs = listing.querySelectorAll(selector);
                if (specs && specs.length) {
                    details = Array.from(specs).map(spec => spec.textContent.trim());
                    break;
                }
            }
            
            // Extract URL
            let url = null;
            const link = listing.querySelector('a');
            if (link && link.hasAttribute('href')) {
                const href = link.getAttribute('href');
                url = href.startsWith('/') ? 
                    `https://www.autotrader.co.uk${href}` : href;
            }
            
            // Get all text for fallback
            const fullText = listing.textContent.trim();
            
            return {
                title: title || 'Unknown',
                price: price || 'Unknown',
                details: details,
                url: url || 'Unknown',
                fullText: fullText
            };
        });
    }
    """

    try:
        return await page.evaluate(js_extract)
    except Exception as e:
        print(f"Error executing JavaScript extraction: {e}")
        return []


async def main():
    """Run the main scraper test with PlaywrightAutoTraderProvider."""
    print("==== CAR SCRAPER TEST SCRIPT (PLAYWRIGHT VERSION) ====")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create instance of PlaywrightAutoTraderProvider
    provider = PlaywrightAutoTraderProvider()

    # Create test search parameters
    params = SearchParameters(
        postcode=TEST_POSTCODE,
        radius=TEST_RADIUS,
        min_price=TEST_MIN_PRICE,
        max_price=TEST_MAX_PRICE,
        make=TEST_MAKE,
        transmission=TEST_TRANSMISSION,
    )

    print(f"\nUsing search parameters: {params}")

    try:
        # Method 1: Test direct URL construction and fetching
        print("\n----- METHOD 1: Direct URL Test -----")
        session_dir = setup_screenshot_directory()
        print(f"Created screenshot directory: {session_dir}")

        url = provider.construct_search_url(params)
        print(f"Using URL: {url}")

        html_content = await fetch_with_playwright(url, session_dir)

        if html_content:
            print(f"Retrieved HTML content ({len(html_content)} bytes)")
            raw_listings = parse_search_results(html_content)
            print(f"\nFound {len(raw_listings)} listings with direct URL approach")

            # Save results to JSON
            method1_json = OUTPUT_DIR / f"method1_results_{timestamp}.json"
            with open(method1_json, "w", encoding="utf-8") as f:
                json.dump(
                    {"url": url, "timestamp": timestamp, "count": len(raw_listings), "listings": raw_listings},
                    f,
                    indent=2,
                )
            print(f"Saved results to {method1_json}")
        else:
            print("Failed to retrieve HTML content")

        # Method 2: Test JavaScript extraction approach (similar to playwright_scraper.py)
        print("\n----- METHOD 2: JavaScript Extraction Test -----")
        try:
            # Set up new browser session for JS extraction
            p, browser, context, page = await setup_browser_session(
                headless=HEADLESS, slow_mo=SLOW_MO, user_agent=USER_AGENT, session_dir=session_dir, debug=True
            )

            try:
                # Go to the URL
                await page.goto(url, wait_until="networkidle")

                # Handle cookie consent if needed
                try:
                    consent_button = await page.wait_for_selector(
                        "button[data-testid='sp_choice_type_11_label']", timeout=5000
                    )
                    if consent_button:
                        await consent_button.click()
                        print("Accepted cookies")
                except Exception:
                    print("No cookie banner found or already accepted")

                # Take screenshot
                await take_screenshot(page, f"method2_page_{timestamp}", session_dir)

                # Extract data using JavaScript
                js_listings = await extract_with_js(page)
                print(f"\nFound {len(js_listings)} listings with JavaScript extraction")

                # Save results to JSON
                method2_json = OUTPUT_DIR / f"method2_results_{timestamp}.json"
                with open(method2_json, "w", encoding="utf-8") as f:
                    json.dump(
                        {"url": url, "timestamp": timestamp, "count": len(js_listings), "listings": js_listings},
                        f,
                        indent=2,
                    )
                print(f"Saved results to {method2_json}")

                # Display a few results
                for i, listing in enumerate(js_listings[:3]):
                    print(f"  {i + 1}. {listing.get('title')} - {listing.get('price')}")
                    print(f"     URL: {listing.get('url')}")
                    if listing.get("details"):
                        print(f"     Details: {', '.join(listing['details'][:3])}")

            finally:
                # Clean up the browser session
                await cleanup_session(p, browser, context, page, session_dir)

        except Exception as e:
            print(f"Error in JavaScript extraction test: {e}")

        # Method 3: Test the PlaywrightAutoTraderProvider's search method
        print("\n----- METHOD 3: Provider Search Method Test -----")
        try:
            # Set provider to use debugging settings
            provider.headless = HEADLESS
            provider.slow_mo = SLOW_MO
            provider.debug_mode = True

            # Call the provider's search method
            listings = await provider.search(params)

            # Save results to JSON
            method3_json = OUTPUT_DIR / f"method3_results_{timestamp}.json"
            with open(method3_json, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "url": url,
                        "timestamp": timestamp,
                        "count": len(listings),
                        "listings": [listing.model_dump() for listing in listings],
                    },
                    f,
                    indent=2,
                )
            print(f"Saved results to {method3_json}")

            # Print results
            print(f"\nFound {len(listings)} listings with provider search method")
            for i, listing in enumerate(listings[:5]):  # Show first 5 listings
                print(f"  {i + 1}. {listing.title} - £{listing.price}")
                print(f"     Make: {listing.make}, Model: {listing.model}, Year: {listing.year}")
                print(
                    f"     Mileage: {listing.mileage} miles, Fuel: {listing.fuel_type}, Transmission: {listing.transmission}"
                )
                print(f"     Details URL: {listing.details_url}")
                print()

        except Exception as e:
            print(f"Error testing provider search method: {e}")

    except Exception as e:
        print(f"Error in main test: {e}")

    print("\n==== TEST SCRIPT COMPLETED ====")
    print(f"All results saved to: {OUTPUT_DIR}")
    print(f"Screenshots saved to: {session_dir}")


if __name__ == "__main__":
    # Check if asyncio is already running (for Jupyter notebooks)
    try:
        asyncio.get_running_loop()
        print("Asyncio already running - need nest_asyncio")
        try:
            import nest_asyncio

            nest_asyncio.apply()
        except ImportError:
            print("nest_asyncio not installed. Install with: pip install nest_asyncio")
            sys.exit(1)
    except RuntimeError:
        pass  # No running event loop, we're good

    # Run the main function
    asyncio.run(main())
