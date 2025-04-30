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
import time
from pathlib import Path
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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

# Request Configuration
REQUEST_DELAY = 1.5  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds before timeout
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"

# Browser options
HEADLESS = True  # Run browser in headless mode (no visible UI)
SLOW_MO = 50  # Slow down execution by 50ms (useful for debugging)
SCREENSHOT = True  # Take screenshots of pages

# Debug options
SAVE_HTML = True  # Save the raw HTML for debugging
HTML_OUTPUT_FILE = "scraper_debug.html"
PRINT_PAGE_STRUCTURE = True  # Print the basic page structure

# Alternative URLs to try (leave empty if not needed)
ALTERNATIVE_FORMATS = [
    # Add alternative URL formats here if needed
    # Example: "https://www.autotrader.co.uk/cars/results?..."
]

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
    search_text = soup.find(string=re.compile(r"(found|results|cars|vehicles)", re.IGNORECASE))
    if search_text:
        print(f"Found search-related text: {search_text.strip()}")

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
        classes = ul.get("class", [])
        items = ul.select("li")
        print(f"  List {i + 1}: class='{' '.join(classes)}', items={len(items)}")

        # If list has items, check the first one
        if items and i < 3:  # Only check first 3 lists in detail
            first_item = items[0]
            item_classes = first_item.get("class", [])
            links = first_item.select("a[href]")
            images = first_item.select("img")
            print(f"    First item: class='{' '.join(item_classes)}', links={len(links)}, images={len(images)}")

            # Check for car-related content
            text = first_item.get_text(" ", strip=True)
            if len(text) > 100:
                text = text[:100] + "..."
            print(f"    Text: {text}")


def parse_search_results(html_content: str) -> List[Dict]:
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

                    # Extract any additional details we can find
                    specs = []
                    spec_elements = item.select("li, p, span, div.spec, [data-testid*='spec']")
                    for spec in spec_elements:
                        text = spec.get_text(strip=True)
                        if text and len(text) < 50 and text not in specs:  # Avoid duplicates and long text
                            specs.append(text)

                    if specs:
                        listing["specs"] = specs[:5]  # Limit to first 5 specs for readability

                    # Add to results if we have at least some basic info
                    if "url" in listing or "title" in listing:
                        listings.append(listing)
                        print(f"  Item {i + 1}: {json.dumps(listing, indent=2)}")

                except Exception as e:
                    print(f"  Error parsing item {i + 1}: {type(e).__name__}: {e}")

            # If we found any valid listings, no need to try other selectors
            if listings:
                break

    # If no listings found with selectors, try a fallback approach with links
    if not listings:
        print("\nNo listings found with standard selectors, trying fallback with links...")
        car_links = soup.select("a[href*='/car-details'], a[href*='/classified/advert']")
        if car_links:
            print(f"Found {len(car_links)} car links in fallback mode")
            # Process first few links
            for i, link in enumerate(car_links[:5]):
                href = link.get("href", "")
                if href:
                    listing = {
                        "url": href if href.startswith("http") else f"https://www.autotrader.co.uk{href}",
                        "title": link.get_text(strip=True) or "Unknown Car",
                    }
                    listings.append(listing)
                    print(f"  Fallback item {i + 1}: {json.dumps(listing, indent=2)}")

    return listings


async def main():
    """Run the main scraper test with Playwright."""
    print("==== CAR SCRAPER TEST SCRIPT (PLAYWRIGHT VERSION) ====")
    print(f"Testing URL: {TEST_URL}")

    # Set up screenshot directory
    session_dir = setup_screenshot_directory()
    print(f"Screenshots will be saved to: {session_dir}")

    # Apply rate limiting if needed
    if REQUEST_DELAY > 0:
        print(f"Waiting {REQUEST_DELAY} seconds before request...")
        time.sleep(REQUEST_DELAY)

    # First try the main URL
    html_content = await fetch_with_playwright(TEST_URL, session_dir)

    if html_content:
        print(f"Successfully retrieved HTML content ({len(html_content)} bytes)")
        listings = parse_search_results(html_content)

        if listings:
            print(f"\nSUCCESS: Found {len(listings)} car listings!")
            # Save results to JSON file
            with open("car_listings.json", "w") as f:
                json.dump(listings, f, indent=2)
            print("Results saved to car_listings.json")
        else:
            print("\nNO LISTINGS FOUND in the main URL")

            # Try alternative URL formats if provided
            if ALTERNATIVE_FORMATS:
                print("\nTrying alternative URL formats...")
                for i, alt_url in enumerate(ALTERNATIVE_FORMATS):
                    print(f"\nTrying alternative URL format {i + 1}: {alt_url}")

                    # Apply rate limiting
                    if REQUEST_DELAY > 0:
                        print(f"Waiting {REQUEST_DELAY} seconds before request...")
                        time.sleep(REQUEST_DELAY)

                    alt_html = await fetch_with_playwright(alt_url, session_dir)
                    if alt_html:
                        alt_listings = parse_search_results(alt_html)
                        if alt_listings:
                            print(f"\nSUCCESS: Found {len(alt_listings)} car listings with alternative URL!")
                            # Save results to JSON file
                            with open(f"car_listings_alt{i + 1}.json", "w") as f:
                                json.dump(alt_listings, f, indent=2)
                            print(f"Results saved to car_listings_alt{i + 1}.json")
                            break
                    else:
                        print("Failed to fetch alternative URL")
    else:
        print("Failed to fetch URL content")


if __name__ == "__main__":
    asyncio.run(main())
