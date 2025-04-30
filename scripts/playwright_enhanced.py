#!/usr/bin/env python3
"""
Enhanced Playwright Debug Script

An advanced version of the debugging script with better extraction methods for
dynamic content on AutoTrader.
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
SNAPSHOT_PATH = OUTPUT_DIR / "dom_snapshot.html"
JSON_OUTPUT_PATH = OUTPUT_DIR / "extraction_results.json"
JSON_PRETTY_PATH = OUTPUT_DIR / "pretty_results.json"
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"

# Browser options
headless_mode = False
SLOW_MO = 100  # Milliseconds between actions
TIMEOUT = 60000  # 60 seconds timeout
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Selectors to try - more comprehensive and general
LISTING_SELECTORS = [
    # AutoTrader specific selectors
    "article.product-card",
    "div.product-card",
    "div[data-testid='search-card']",
    "article[data-testid]",
    "li.search-page__result",
    "li.product-card",
    "li[data-testid*='search-card']",
    "article.advert-card",
    "div.search-results__result",
    "div.search-page__results > *",
    # Generic selectors that might capture listings
    "div.vehicle-card",
    "li.search-result-item",
    "main li",
    "div.card",
    "[data-advert-id]",
    # Very general fallbacks
    "main > div > div > ul > li",
    "main > div > div > div > article",
    "main div[role='listitem']",
    "div[id*='search'] li",
    "div[id*='result'] li",
    "div[class*='listings'] > div",
    "div[class*='results'] > div",
]

# XPath selectors (often more flexible than CSS)
XPATH_SELECTORS = [
    "//article[contains(@class, 'product-card')]",
    "//div[contains(@class, 'product-card')]",
    "//div[@data-testid='search-card']",
    "//li[contains(@class, 'search-page__result')]",
    "//div[contains(@class, 'search-results')]//li",
    "//main//div[contains(@class, 'results')]//div[position() > 1]",
    "//ul/li[.//a[contains(@href, '/car-details') or contains(@href, '/classified/advert')]]",
    "//div[.//span[contains(text(), '£') and string-length(text()) < 15]]",
]


async def setup_browser():
    """Set up and return a Playwright browser session."""
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=headless_mode, slow_mo=SLOW_MO)
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1280, "height": 900},
        # Enable permissions
        permissions=["geolocation"],
    )
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
    """Navigate to URL and handle common interactions with better wait logic."""
    print(f"{BLUE}Navigating to: {url}{RESET}")

    try:
        # Navigate to the URL
        response = await page.goto(url, wait_until="domcontentloaded")
        if not response:
            print(f"{RED}No response received{RESET}")
            return False

        status = response.status
        print(f"{BLUE}Page loaded with status: {status}{RESET}")

        if status != 200:
            print(f"{RED}Error: HTTP {status}{RESET}")
            return False

        # Take initial screenshot
        await take_screenshot(page, "initial_page")

        # Handle cookie consent if present
        await handle_cookie_consent(page)

        # Wait for search results to appear
        print(f"{BLUE}Waiting for content to load...{RESET}")
        await wait_for_content(page)

        # Scroll down to ensure all content is loaded
        await scroll_page(page)

        # Take a screenshot after interactions
        await take_screenshot(page, "after_interaction")

        return True

    except Exception as e:
        print(f"{RED}Error during navigation: {e}{RESET}")
        await take_screenshot(page, "navigation_error")
        return False


async def handle_cookie_consent(page):
    """Handle cookie consent banners with multiple strategies."""
    try:
        # Try multiple cookie consent button selectors
        for selector in [
            "button[data-testid='sp_choice_type_11_label']",
            "#onetrust-accept-btn-handler",
            "button:has-text('Accept All')",
            "button:has-text('Accept Cookies')",
            "button[id*='accept']",
            "[data-testid*='cookie-consent']",
        ]:
            try:
                consent_button = await page.wait_for_selector(selector, timeout=5000)
                if consent_button:
                    await consent_button.click()
                    print(f"{GREEN}Clicked cookie consent button: {selector}{RESET}")
                    await page.wait_for_load_state("networkidle")
                    return
            except Exception:
                continue

        # Try XPath as fallback
        for xpath in [
            "//button[contains(., 'Accept') or contains(., 'allow') or contains(., 'agree')]",
            "//div[contains(@class, 'cookie') or contains(@id, 'cookie')]//button",
        ]:
            try:
                consent_button = await page.wait_for_selector(f"xpath={xpath}", timeout=2000)
                if consent_button:
                    await consent_button.click()
                    print(f"{GREEN}Clicked cookie consent button with XPath{RESET}")
                    await page.wait_for_load_state("networkidle")
                    return
            except Exception:
                continue

    except Exception as e:
        print(f"{YELLOW}Error handling cookie consent: {e}{RESET}")
        print(f"{YELLOW}Continuing without accepting cookies{RESET}")


async def wait_for_content(page):
    """Wait for content to load with multiple strategies."""
    try:
        # Wait for network to be idle
        await page.wait_for_load_state("networkidle", timeout=10000)

        # Try to wait for common selectors
        for selector in ["article", "div.product-card", "div.search-results", "li.search-page__result", "main li"]:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                print(f"{GREEN}Found content with selector: {selector}{RESET}")
                return
            except Exception:
                continue

        # If no specific content found, wait a fixed time
        print(f"{YELLOW}No specific content found, waiting additional time...{RESET}")
        await asyncio.sleep(5)

    except Exception as e:
        print(f"{YELLOW}Error waiting for content: {e}{RESET}")
        print(f"{YELLOW}Continuing anyway{RESET}")


async def scroll_page(page):
    """Scroll the page to ensure all content is loaded."""
    print(f"{BLUE}Scrolling page to load all content...{RESET}")

    try:
        # Get page height
        height = await page.evaluate("""
            () => document.documentElement.scrollHeight
        """)

        # Scroll in steps
        scroll_step = 300
        for i in range(0, height, scroll_step):
            await page.evaluate(f"window.scrollTo(0, {i})")
            await asyncio.sleep(0.1)  # Small delay between scrolls

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")

        # Wait a moment for any lazy-loaded content
        await asyncio.sleep(2)

        print(f"{GREEN}Finished scrolling{RESET}")

    except Exception as e:
        print(f"{YELLOW}Error during scrolling: {e}{RESET}")


async def extract_with_xpath(page) -> tuple[str | None, list[dict[str, Any]]]:
    """Extract listings using XPath for more flexibility."""
    print(f"\n{BOLD}{BLUE}Extracting with XPath{RESET}")

    for xpath in XPATH_SELECTORS:
        try:
            print(f"Trying XPath: {xpath}")
            elements = await page.query_selector_all(f"xpath={xpath}")

            if not elements:
                continue

            print(f"{GREEN}Found {len(elements)} elements with XPath: {xpath}{RESET}")

            listings = []
            # Process only first 5 for display
            for i, element in enumerate(elements[:5]):
                listing = {"xpath_used": xpath}

                # Get HTML for this element
                html = await page.evaluate("el => el.outerHTML", element)

                # Parse with BeautifulSoup to extract data
                soup = BeautifulSoup(html, "html.parser")

                # Extract title (try various patterns)
                title_elem = (
                    soup.select_one("h2, h3")
                    or soup.select_one("[data-testid*='title']")
                    or soup.select_one("a[href*='/car-details'], a[href*='/classified/advert']")
                )
                if title_elem:
                    listing["title"] = title_elem.get_text(strip=True)

                # Extract price (look for £ symbol)
                price_text = None
                price_elem = soup.find(string=re.compile(r"£[\d,]+"))
                if price_elem:
                    price_parent = price_elem.parent
                    price_text = price_parent.get_text(strip=True)
                    listing["price"] = price_text

                # Extract link
                link_elem = soup.select_one("a[href]")
                if link_elem and link_elem.has_attr("href"):
                    href = str(link_elem["href"])
                    full_url = href if href.startswith("http") else f"https://www.autotrader.co.uk{href}"
                    listing["url"] = full_url

                # Extract any specs
                specs_elems = soup.select("li, span.spec, div[class*='spec']")
                if specs_elems:
                    specs = [elem.get_text(strip=True) for elem in specs_elems if elem.get_text(strip=True)]
                    # Filter out very short or very long specs
                    specs = [s for s in specs if 3 <= len(s) <= 30]
                    if specs:
                        listing["specs"] = specs

                print(f"\n{BOLD}XPath Listing {i + 1}:{RESET}")
                if "title" in listing:
                    print(f"  Title: {listing['title']}")
                if "price" in listing:
                    print(f"  Price: {listing['price']}")
                if "specs" in listing:
                    print(f"  Specs: {', '.join(listing['specs'][:3])}" + ("..." if len(listing["specs"]) > 3 else ""))
                if "url" in listing:
                    print(f"  URL: {listing['url']}")

                listings.append(listing)

            if listings:
                return xpath, listings

        except Exception as e:
            print(f"{YELLOW}Error with XPath {xpath}: {e}{RESET}")

    print(f"{RED}No listings found with any XPath selector{RESET}")
    return None, []


async def extract_dom_snapshot(page) -> str:
    """Take a DOM snapshot to see what's actually in the page."""
    print(f"\n{BOLD}{BLUE}Taking DOM snapshot{RESET}")

    # Get a clean version of the DOM after JavaScript has executed
    html = await page.content()

    # Save the snapshot
    SNAPSHOT_PATH.parent.mkdir(exist_ok=True, parents=True)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"{GREEN}DOM snapshot saved to {SNAPSHOT_PATH}{RESET}")
    return html


async def extract_with_direct_js(page) -> tuple[str | None, list[dict[str, Any]]]:
    """Extract data with direct JavaScript that tries multiple approaches."""
    print(f"\n{BOLD}{BLUE}Extracting with Direct JavaScript{RESET}")

    js_extract = """
    () => {
        // Helper functions
        const getText = (el) => el ? el.textContent.trim() : '';
        const getPrice = (el) => {
            if (!el) return null;
            const text = el.textContent;
            const match = text.match(/£[\\d,]+/);
            return match ? match[0] : null;
        };
        
        // Find all elements that might be car listings
        const findPotentialListings = () => {
            // Strategy 1: Look for elements with price in £
            const priceElements = Array.from(document.querySelectorAll('*')).filter(el => {
                return el.textContent && el.textContent.includes('£') && 
                       /£[\\d,]+/.test(el.textContent) &&
                       el.textContent.length < 100;
            });
            
            // Find potential container elements that could be listings
            let containers = [];
            for (const priceEl of priceElements) {
                // Try to find a parent container (4 levels up max)
                let el = priceEl;
                for (let i = 0; i < 4; i++) {
                    el = el.parentElement;
                    if (!el) break;
                    
                    // If this element has a link and title-like text, it might be a listing
                    const hasLink = el.querySelector('a[href*="/car-details"], a[href*="/classified/advert"]');
                    const hasChildText = Array.from(el.children).some(child => {
                        const text = child.textContent?.trim();
                        return text && text.length > 10 && text.length < 100;
                    });
                    
                    if (hasLink && hasChildText) {
                        containers.push(el);
                        break;
                    }
                }
            }
            
            // Deduplicate containers
            const uniqueContainers = [];
            const seen = new Set();
            for (const container of containers) {
                if (!seen.has(container)) {
                    uniqueContainers.push(container);
                    seen.add(container);
                }
            }
            
            return uniqueContainers;
        };
        
        // Main extraction logic
        const listings = [];
        const containers = findPotentialListings();
        
        for (let i = 0; i < Math.min(containers.length, 10); i++) {
            const container = containers[i];
            
            // Extract data from this container
            const titleEl = container.querySelector('h2, h3, [data-testid*="title"]') || 
                           container.querySelector('a');
            const priceEl = Array.from(container.querySelectorAll('*')).find(el => {
                return el.textContent && el.textContent.includes('£') && 
                       /£[\\d,]+/.test(el.textContent) &&
                       el.textContent.length < 100;
            });
            const linkEl = container.querySelector('a[href*="/car-details"], a[href*="/classified/advert"]') ||
                          container.querySelector('a[href]');
            
            // Get specs (small text elements that might be specs)
            const specsEls = Array.from(container.querySelectorAll('li, span, div'))
                .filter(el => {
                    const text = el.textContent?.trim();
                    return text && text.length > 3 && text.length < 30 && 
                           !text.includes('£') && !el.querySelector('*');
                });
            
            // Build listing object
            const listing = {
                index: i,
                selector: container.tagName + (container.className ? '.' + container.className.replace(/\\s+/g, '.') : '')
            };
            
            if (titleEl) {
                listing.title = getText(titleEl);
            }
            
            if (priceEl) {
                listing.price = getPrice(priceEl);
            }
            
            if (linkEl && linkEl.href) {
                listing.url = linkEl.href;
            }
            
            if (specsEls.length > 0) {
                listing.specs = specsEls.map(el => getText(el)).filter(Boolean);
            }
            
            // Get container dimensions
            const rect = container.getBoundingClientRect();
            listing.dimensions = {
                width: rect.width,
                height: rect.height,
                top: rect.top,
                left: rect.left
            };
            
            listings.push(listing);
        }
        
        return {
            method: "direct-js",
            count: containers.length,
            listings: listings
        };
    }
    """

    try:
        result = await page.evaluate(js_extract)

        print(f"{GREEN}Found {result['count']} potential listings with Direct JavaScript{RESET}")

        # Print details of extracted listings
        for i, listing in enumerate(result["listings"]):
            print(f"\n{BOLD}JS Direct Listing {i + 1}:{RESET}")

            if "title" in listing:
                print(f"  Title: {listing['title']}")

            if "price" in listing:
                print(f"  Price: {listing['price']}")

            if listing.get("specs"):
                print(f"  Specs: {', '.join(listing['specs'][:3])}" + ("..." if len(listing["specs"]) > 3 else ""))

            if "url" in listing:
                print(f"  URL: {listing['url']}")

            if "dimensions" in listing:
                d = listing["dimensions"]
                print(f"  Size: {d['width']}×{d['height']} at ({d['left']},{d['top']})")

        return "direct-js", result["listings"]

    except Exception as e:
        print(f"{RED}Error executing Direct JavaScript extraction: {e}{RESET}")
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
    parser = argparse.ArgumentParser(description="Enhanced Playwright scraping for AutoTrader")
    parser.add_argument("--url", help="Direct URL to scrape")
    parser.add_argument("--postcode", help="Postcode for search")
    parser.add_argument("--radius", type=int, default=10, help="Search radius in miles")
    parser.add_argument("--make", help="Car make")
    parser.add_argument("--model", help="Car model")
    parser.add_argument("--min-price", type=int, help="Minimum price")
    parser.add_argument("--max-price", type=int, help="Maximum price")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--json-only", action="store_true", help="Only output JSON, no HTML")
    parser.add_argument("--wait", type=int, default=0, help="Additional wait time in seconds")

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

        # Optional additional wait
        if args.wait > 0:
            print(f"{BLUE}Waiting additional {args.wait} seconds...{RESET}")
            await asyncio.sleep(args.wait)
            await take_screenshot(page, f"after_wait_{args.wait}s")

        # Take DOM snapshot
        html_content = await extract_dom_snapshot(page)

        # Extract with XPath
        xpath_selector, xpath_listings = await extract_with_xpath(page)

        # Extract with direct JavaScript
        js_selector, js_listings = await extract_with_direct_js(page)

        # Save results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": timestamp,
            "url": url,
            "xpath": {"selector": xpath_selector, "listings": xpath_listings},
            "direct_js": {"selector": js_selector, "listings": js_listings},
            "count": {
                "xpath": len(xpath_listings),
                "direct_js": len(js_listings),
            },
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
        print(f"  - DOM Snapshot: {SNAPSHOT_PATH}")
        print(f"\n{BOLD}Summary:{RESET}")
        print(f"XPath: Found {len(xpath_listings)} listings")
        print(f"Direct JS: Found {len(js_listings)} listings")

        # Take final screenshot
        await take_screenshot(page, "final_state")

    finally:
        # Clean up browser
        await cleanup_browser(p, browser, context, page)


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
