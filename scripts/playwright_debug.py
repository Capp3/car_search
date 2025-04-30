#!/usr/bin/env python3
"""
Playwright Debug Script

A simplified script to debug and test various extraction methods from AutoTrader.
This tool helps you see exactly what Playwright receives and test different selectors.

Usage:
  python scripts/playwright_debug.py --url "https://www.autotrader.co.uk/car-search?postcode=BT73fn&radius=10"
  python scripts/playwright_debug.py --make Ford --max-price 2500 --postcode BT73fn
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Add parent directory to path so we can import project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Console formatting
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Output configuration
OUTPUT_DIR = Path("debug_output")
HTML_OUTPUT_PATH = OUTPUT_DIR / "page_content.html"
JSON_OUTPUT_PATH = OUTPUT_DIR / "extraction_results.json"
JSON_PRETTY_PATH = OUTPUT_DIR / "pretty_results.json"  # New file for pretty-printed JSON
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"

# Browser options - Change these for your debugging needs
headless_mode = False  # Changed from uppercase to avoid linter errors
SLOW_MO = 100  # Milliseconds between actions - increase for slower execution
TIMEOUT = 30000  # Milliseconds before timeout
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Selectors to try - add your own to test different extraction methods
LISTING_SELECTORS = [
    # Current AutoTrader selectors (2025)
    "article.product-card",
    "div.product-card",
    "div[data-testid='search-card']",
    "article[data-testid]",
    "li.search-page__result",
    # Older AutoTrader selectors
    "li.product-card",
    "li[data-testid*='search-card']",
    "article.advert-card",
    "div.search-results__result",
    # Generic fallbacks
    "div.vehicle-card",
    "li.search-result-item",
    "main li",
    "div.card",
    "[data-advert-id]",
]

# Selectors for specific data points within a listing
TITLE_SELECTORS = ["h2", "h3", "[data-testid*='title']", ".product-card-details__title", ".vehicle-title"]

PRICE_SELECTORS = ["[data-testid*='price']", ".product-card-pricing__price", ".vehicle-price", ".advert-price"]

SPECS_SELECTORS = [
    ".specs li",
    ".key-specs li",
    ".specification-item",
    "[data-testid*='spec']",
    ".product-card-details__specification li",
]

LINK_SELECTORS = ["a[href*='/car-details']", "a[href*='/classified/advert']", "a[href]"]


async def setup_browser():
    """Set up and return a Playwright browser session."""
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=headless_mode, slow_mo=SLOW_MO)
    context = await browser.new_context(user_agent=USER_AGENT, viewport={"width": 1280, "height": 800})
    page = await context.new_page()
    page.set_default_timeout(TIMEOUT)

    # Enable console logging
    page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))

    return p, browser, context, page


async def cleanup_browser(p, browser, context, page):
    """Clean up Playwright browser resources."""
    await page.close()
    await context.close()
    await browser.close()
    await p.stop()


async def take_screenshot(page, name):
    """Take a screenshot of the current page."""
    SCREENSHOTS_DIR.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    path = SCREENSHOTS_DIR / filename
    await page.screenshot(path=str(path), full_page=True)
    print(f"{GREEN}Screenshot saved to {path}{RESET}")
    return path


async def navigate_to_url(page, url):
    """Navigate to URL and handle common interactions."""
    print(f"{BLUE}Navigating to: {url}{RESET}")

    try:
        # Navigate to the URL
        response = await page.goto(url, wait_until="networkidle")
        if not response:
            print(f"{RED}No response received{RESET}")
            return False

        status = response.status
        print(f"{BLUE}Page loaded with status: {status}{RESET}")

        if status != 200:
            print(f"{RED}Error: HTTP {status}{RESET}")
            return False

        # Handle cookie consent if present
        try:
            # Try multiple cookie consent button selectors
            for selector in [
                "button[data-testid='sp_choice_type_11_label']",
                "#onetrust-accept-btn-handler",
                "button:has-text('Accept All')",
                "button:has-text('Accept Cookies')",
            ]:
                consent_button = await page.wait_for_selector(selector, timeout=5000)
                if consent_button:
                    await consent_button.click()
                    print(f"{GREEN}Clicked cookie consent button: {selector}{RESET}")
                    await page.wait_for_load_state("networkidle")
                    break
        except Exception as e:
            print(f"{YELLOW}No cookie banner found or already accepted: {e}{RESET}")

        # Take a screenshot
        await take_screenshot(page, "after_navigation")

        return True

    except Exception as e:
        print(f"{RED}Error during navigation: {e}{RESET}")
        await take_screenshot(page, "navigation_error")
        return False


def extract_with_beautiful_soup(html):
    """Extract listings using BeautifulSoup."""
    print(f"\n{BOLD}{BLUE}Extracting with BeautifulSoup{RESET}")
    soup = BeautifulSoup(html, "html.parser")

    # Save the HTML for examination
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{GREEN}HTML saved to {HTML_OUTPUT_PATH}{RESET}")

    # Page title for diagnostics
    title = soup.title.text if soup.title else "No title"
    print(f"{BLUE}Page title: {title}{RESET}")

    # Find search stats text (often indicates how many results)
    search_stats = soup.find(string=re.compile(r"found \d+ cars|showing \d+ results|cars for sale", re.I))
    if search_stats:
        stats_text = str(search_stats).strip() if hasattr(search_stats, "strip") else str(search_stats)
        print(f"{BLUE}Search stats: {stats_text}{RESET}")

    # Try each selector to find listings
    for selector in LISTING_SELECTORS:
        listing_items = soup.select(selector)
        if not listing_items:
            continue

        print(f"\n{GREEN}Found {len(listing_items)} items with selector: '{selector}'{RESET}")

        # Extract key details from first few listings
        listings = []
        for i, item in enumerate(listing_items[:3]):  # Limit to first 3 for brevity
            print(f"\n{BOLD}Listing {i + 1}:{RESET}")
            listing = {"selector_used": selector}

            # Try to extract title
            for title_selector in TITLE_SELECTORS:
                title_elem = item.select_one(title_selector)
                if title_elem and title_elem.get_text(strip=True):
                    title_text = title_elem.get_text(strip=True)
                    listing["title"] = title_text
                    print(f"  Title ({title_selector}): {title_text}")
                    break

            # Try to extract price
            for price_selector in PRICE_SELECTORS:
                price_elem = item.select_one(price_selector)
                if price_elem and "£" in price_elem.get_text():
                    price_text = price_elem.get_text(strip=True)
                    listing["price"] = price_text
                    print(f"  Price ({price_selector}): {price_text}")
                    break

            # Try to extract specifications
            for specs_selector in SPECS_SELECTORS:
                specs_elems = item.select(specs_selector)
                if specs_elems:
                    specs = [spec.get_text(strip=True) for spec in specs_elems]
                    # Convert the listing dict to use Any type to avoid type issues
                    listing_any: dict[str, Any] = listing
                    listing_any["specs"] = specs
                    print(f"  Specs ({specs_selector}): {', '.join(specs[:3])}" + ("..." if len(specs) > 3 else ""))
                    break

            # Try to extract link
            for link_selector in LINK_SELECTORS:
                link_elem = item.select_one(link_selector)
                if link_elem and link_elem.has_attr("href"):
                    href = str(link_elem["href"])
                    full_url = href if href.startswith("http") else f"https://www.autotrader.co.uk{href}"
                    listing["url"] = full_url
                    print(f"  URL ({link_selector}): {full_url}")
                    break

            listings.append(listing)

        # If we found listings, return them
        if listings:
            return selector, listings

    print(f"{RED}No listings found with any selector{RESET}")
    return None, []


async def extract_with_javascript(page):
    """Extract listings using JavaScript evaluation in the page context."""
    print(f"\n{BOLD}{BLUE}Extracting with JavaScript{RESET}")

    # JavaScript to extract listings
    js_extract = """
    () => {
        // Helper function to get text content
        const getText = (element, selector) => {
            if (!element) return null;
            const el = selector ? element.querySelector(selector) : element;
            return el ? el.textContent.trim() : null;
        };
        
        // Listing selectors to try
        const listingSelectors = [
            'article.product-card',
            'div.product-card',
            'div[data-testid="search-card"]',
            'li.search-page__result',
            'li.product-card',
            'article[data-testid]',
            'main li',
            'div.card',
            '[data-advert-id]'
        ];
        
        // Try each selector
        let foundElements = [];
        let usedSelector = '';
        
        for (const selector of listingSelectors) {
            const elements = document.querySelectorAll(selector);
            console.log(`Selector ${selector}: ${elements.length} elements`);
            
            if (elements && elements.length > 0) {
                foundElements = Array.from(elements);
                usedSelector = selector;
                break;
            }
        }
        
        if (foundElements.length === 0) {
            return { selector: null, listings: [] };
        }
        
        // Extract data from first 3 listings
        const maxListings = Math.min(foundElements.length, 3);
        const listings = [];
        
        for (let i = 0; i < maxListings; i++) {
            const item = foundElements[i];
            const listing = {};
            
            // Title selectors
            const titleSelectors = ['h2', 'h3', '[data-testid*="title"]', '.product-card-details__title'];
            for (const selector of titleSelectors) {
                const title = getText(item, selector);
                if (title) {
                    listing.title = title;
                    listing.title_selector = selector;
                    break;
                }
            }
            
            // Price selectors
            const priceSelectors = ['[data-testid*="price"]', '.product-card-pricing__price', '.vehicle-price'];
            for (const selector of priceSelectors) {
                const price = getText(item, selector);
                if (price && price.includes('£')) {
                    listing.price = price;
                    listing.price_selector = selector;
                    break;
                }
            }
            
            // Specs selectors
            const specsSelectors = ['.specs li', '.key-specs li', '.specification-item'];
            for (const selector of specsSelectors) {
                const specs = item.querySelectorAll(selector);
                if (specs && specs.length) {
                    listing.specs = Array.from(specs).map(spec => spec.textContent.trim());
                    listing.specs_selector = selector;
                    break;
                }
            }
            
            // Link selectors
            const linkSelectors = ['a[href*="/car-details"]', 'a[href*="/classified/advert"]', 'a[href]'];
            for (const selector of linkSelectors) {
                const link = item.querySelector(selector);
                if (link && link.hasAttribute('href')) {
                    const href = link.getAttribute('href');
                    listing.url = href.startsWith('/') ? 
                        `https://www.autotrader.co.uk${href}` : href;
                    listing.link_selector = selector;
                    break;
                }
            }
            
            listings.push(listing);
        }
        
        return { selector: usedSelector, listings: listings };
    }
    """

    try:
        result = await page.evaluate(js_extract)

        if not result["selector"]:
            print(f"{RED}No listings found with JavaScript extraction{RESET}")
            return None, []

        print(f"{GREEN}Found listings with selector: '{result['selector']}'{RESET}")

        # Print details of extracted listings
        for i, listing in enumerate(result["listings"]):
            print(f"\n{BOLD}JS Listing {i + 1}:{RESET}")

            if "title" in listing:
                print(f"  Title ({listing.get('title_selector', 'unknown')}): {listing['title']}")

            if "price" in listing:
                print(f"  Price ({listing.get('price_selector', 'unknown')}): {listing['price']}")

            if "specs" in listing:
                print(
                    f"  Specs ({listing.get('specs_selector', 'unknown')}): "
                    + f"{', '.join(listing['specs'][:3])}"
                    + ("..." if len(listing["specs"]) > 3 else "")
                )

            if "url" in listing:
                print(f"  URL ({listing.get('link_selector', 'unknown')}): {listing['url']}")

        return result["selector"], result["listings"]

    except Exception as e:
        print(f"{RED}Error executing JavaScript extraction: {e}{RESET}")
        return None, []


def construct_autotrader_url(postcode, radius=10, make=None, model=None, min_price=None, max_price=None):
    """Construct an AutoTrader search URL from parameters."""
    base_url = "https://www.autotrader.co.uk/car-search"
    params = [f"postcode={postcode}", f"radius={radius}"]

    if make:
        params.append(f"make={make}")

    if model:
        params.append(f"model={model}")

    if min_price:
        params.append(f"price-from={min_price}")

    if max_price:
        params.append(f"price-to={max_price}")

    # Add standard parameters
    params.append("homeDeliveryAdverts=exclude")
    params.append("advertising-location=at_cars")
    params.append("page=1")

    return f"{base_url}?{'&'.join(params)}"


async def main():
    """Main function to run the debug script."""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Debug Playwright scraping for AutoTrader")
    parser.add_argument("--url", help="Direct URL to scrape")
    parser.add_argument("--postcode", help="Postcode for search")
    parser.add_argument("--radius", type=int, default=10, help="Search radius in miles")
    parser.add_argument("--make", help="Car make")
    parser.add_argument("--model", help="Car model")
    parser.add_argument("--min-price", type=int, help="Minimum price")
    parser.add_argument("--max-price", type=int, help="Maximum price")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--json-only", action="store_true", help="Only output JSON, no HTML")

    args = parser.parse_args()

    # Update headless mode if specified
    global headless_mode
    if args.headless:
        headless_mode = True

    # Determine URL to use
    url = args.url
    if not url and args.postcode:
        url = construct_autotrader_url(
            args.postcode, args.radius, args.make, args.model, args.min_price, args.max_price
        )

    if not url:
        print(f"{RED}Error: No URL provided. Use --url or provide search parameters.{RESET}")
        parser.print_help()
        return

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    # Setup browser
    p, browser, context, page = await setup_browser()

    try:
        # Navigate to URL
        if not await navigate_to_url(page, url):
            return

        # Get HTML content
        html_content = await page.content()
        print(f"{GREEN}Retrieved HTML content ({len(html_content)} bytes){RESET}")

        # Skip HTML output if json-only mode
        if not args.json_only:
            with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"{GREEN}HTML saved to {HTML_OUTPUT_PATH}{RESET}")

        # Extract with BeautifulSoup
        bs_selector, bs_listings = extract_with_beautiful_soup(html_content)

        # Extract with JavaScript
        js_selector, js_listings = await extract_with_javascript(page)

        # Save results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": timestamp,
            "url": url,
            "beautiful_soup": {"selector": bs_selector, "listings": bs_listings},
            "javascript": {"selector": js_selector, "listings": js_listings},
        }

        # Save compact JSON
        with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f)

        # Save pretty-printed JSON
        with open(JSON_PRETTY_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"\n{GREEN}Results saved to:{RESET}")
        print(f"  - Compact JSON: {JSON_OUTPUT_PATH}")
        print(f"  - Pretty JSON: {JSON_PRETTY_PATH}")
        print(f"\n{BOLD}Summary:{RESET}")
        print(f"BeautifulSoup: Found {len(bs_listings)} listings with selector '{bs_selector}'")
        print(f"JavaScript: Found {len(js_listings)} listings with selector '{js_selector}'")

        # Take final screenshot
        await take_screenshot(page, "final_state")

    finally:
        # Clean up browser
        await cleanup_browser(p, browser, context, page)


if __name__ == "__main__":
    # Check if asyncio is already running (for Jupyter notebooks)
    try:
        asyncio.get_running_loop()
        print("Asyncio already running - need nest_asyncio")
        try:
            # We don't actually need this import since we're just checking
            # this is just a convenience for Jupyter notebook users
            pass
        except ImportError:
            print("nest_asyncio not installed. Install with: pip install nest_asyncio")
            sys.exit(1)
    except RuntimeError:
        pass  # No running event loop, we're good

    # Run the main function
    asyncio.run(main())
