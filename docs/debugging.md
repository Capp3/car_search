# Playwright Debugging Guide

This guide explains how to use the Playwright debugging tool to help diagnose and fix issues with web scraping in the Car Search application.

## Overview

The Playwright debugging tool (`scripts/playwright_debug.py`) is designed to help you understand what Playwright is receiving from websites and test different selectors to extract data. It provides:

1. Detailed console output showing what's happening during page loading
2. Screenshots of the page at different stages
3. Extraction using both BeautifulSoup and JavaScript approaches
4. Saved HTML content for manual inspection
5. JSON results with all extracted data

## Running the Debug Tool

You can run the debug tool using the provided convenience script:

```bash
# Direct URL method
./scripts/run_debug.sh --url "https://www.autotrader.co.uk/car-search?postcode=BT73fn&radius=10&make=Ford"

# Quick format (make, postcode, max-price)
./scripts/run_debug.sh ford bt73fn 2500

# Full parameters
./scripts/run_debug.sh --make ford --postcode bt73fn --max-price 2500 --radius 15

# Headless mode (no browser UI)
./scripts/run_debug.sh --headless --make ford --postcode bt73fn --max-price 2500

# JSON-only mode (skip HTML output)
./scripts/run_debug.sh --json-only --make ford --postcode bt73fn --max-price 2500
```

## Understanding the Output

When you run the debug tool, it will:

1. Launch a browser and navigate to the specified URL
2. Take screenshots (saved to `debug_output/screenshots/`)
3. Try to extract listings using different selector strategies
4. Print detailed information about what it finds
5. Save results to:
   - `debug_output/extraction_results.json` (compact JSON)
   - `debug_output/pretty_results.json` (formatted JSON for easy reading)
   - `debug_output/page_content.html` (raw HTML, unless using --json-only)

## Key Files

- `scripts/playwright_debug.py`: The main debugging script
- `scripts/run_debug.sh`: Convenience script to run the debugger
- `debug_output/`: Directory containing all output files
  - `screenshots/`: Directory containing all screenshots
  - `page_content.html`: Complete HTML of the retrieved page
  - `extraction_results.json`: Compact JSON with extraction results
  - `pretty_results.json`: Pretty-printed JSON for easy reading

## Using the Results

After running the debug tool, you can:

1. **Examine the HTML**: Open `debug_output/page_content.html` in your browser to inspect the page structure and elements
2. **Review screenshots**: Check the screenshots in `debug_output/screenshots/` to see what the page looks like at different stages
3. **Analyze JSON results**: Review `debug_output/pretty_results.json` to see what data was extracted in a readable format
4. **Update selectors**: Based on your findings, you can update the selectors in the script or in your application code

## Customizing the Debug Tool

You can modify the debug tool to add new selector strategies or change its behavior:

1. Open `scripts/playwright_debug.py` in your editor
2. Modify the selector lists at the top of the file (e.g., `LISTING_SELECTORS`, `TITLE_SELECTORS`, etc.)
3. Add custom extraction logic for specific websites
4. Change browser options like delay time, viewport size, etc.

## Troubleshooting

If the tool doesn't find any listings:

1. Check the screenshots to see if the page is loading correctly
2. Inspect the HTML to see if the expected content is present
3. Try different selectors based on your inspection
4. Check if the website has anti-bot measures that might be blocking Playwright
5. Try adding additional wait steps or interaction steps (like scrolling) if needed

## Next Steps

After identifying the correct selectors and approach:

1. Update your application's extraction code with the working selectors
2. Add handling for any special cases or anti-bot measures you discovered
3. Implement error checking based on the patterns you observed
4. Consider adding periodic debugging runs to catch website changes early 