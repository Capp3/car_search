#!/usr/bin/env python3
"""
Playwright Utilities

This module provides utilities for working with Playwright, including:
- Installation management for Playwright and browsers
- Screenshot directory management
- Browser session setup and configuration
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Setup logging
logger = logging.getLogger(__name__)

# Constants
SCREENSHOT_DIR = Path("screenshots")
MAX_SCREENSHOTS = 100  # Maximum number of screenshots to keep
MAX_DIR_SIZE_MB = 100  # Maximum directory size in MB


def ensure_playwright_installed() -> bool:
    """
    Ensure that Playwright and its browsers are installed.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if playwright is in the Python path
        import playwright

        logger.info("Playwright package found in Python path")

        # Check if browsers are installed
        try:
            # Try importing a browser-specific module to see if browsers are installed
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                # Just check if we can access chromium
                _ = p.chromium
            logger.info("Playwright browsers already installed")
            return True
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                logger.warning("Playwright browsers not installed, installing now...")

                # Install browsers
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "playwright", "install", "chromium"],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    logger.info(f"Playwright browsers installation successful: {result.stdout}")
                    return True
                except subprocess.CalledProcessError as install_error:
                    logger.error(f"Failed to install Playwright browsers: {install_error.stderr}")
                    return False
            else:
                logger.error(f"Unexpected error when checking Playwright browsers: {e}")
                return False

    except ImportError:
        logger.error("Playwright not installed in Python environment")
        logger.info("Please install using: python -m pip install playwright")
        return False


def setup_screenshot_directory() -> Path:
    """
    Setup the screenshot directory with session subfolder and clean old screenshots if needed.

    Returns:
        Path: Path to the session screenshot directory
    """
    # Create main screenshot directory if it doesn't exist
    SCREENSHOT_DIR.mkdir(exist_ok=True)

    # Create a session-specific subfolder based on current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = SCREENSHOT_DIR / f"session_{timestamp}"
    session_dir.mkdir(exist_ok=True)

    # Clean up old screenshots if directory is too large
    cleanup_screenshots()

    return session_dir


def cleanup_screenshots() -> None:
    """
    Clean up old screenshots if there are too many or if the directory is too large.
    """
    try:
        # Check if directory exists
        if not SCREENSHOT_DIR.exists():
            return

        # Count files and calculate directory size
        all_files = []
        total_size = 0

        for file_path in SCREENSHOT_DIR.glob("**/*"):
            if file_path.is_file():
                file_stat = file_path.stat()
                all_files.append((file_path, file_stat.st_mtime))
                total_size += file_stat.st_size

        # Convert to MB
        total_size_mb = total_size / (1024 * 1024)

        # Check if cleanup is needed
        if len(all_files) <= MAX_SCREENSHOTS and total_size_mb <= MAX_DIR_SIZE_MB:
            logger.debug("Screenshot directory is within limits, no cleanup needed")
            return

        # Sort files by modification time (oldest first)
        all_files.sort(key=lambda x: x[1])

        # Remove oldest files until we're under the limits
        while all_files and (len(all_files) > MAX_SCREENSHOTS or total_size_mb > MAX_DIR_SIZE_MB):
            file_to_remove, _ = all_files.pop(0)
            file_size = file_to_remove.stat().st_size / (1024 * 1024)  # Size in MB

            logger.info(f"Removing old screenshot: {file_to_remove}")
            file_to_remove.unlink()

            total_size_mb -= file_size

        # Find and remove empty directories
        for dir_path in SCREENSHOT_DIR.glob("**/"):
            if dir_path != SCREENSHOT_DIR and dir_path.is_dir():
                # Check if directory is empty
                if not any(dir_path.iterdir()):
                    logger.info(f"Removing empty directory: {dir_path}")
                    dir_path.rmdir()

        logger.info(f"Screenshot cleanup complete. Current size: {total_size_mb:.2f} MB, Files: {len(all_files)}")

    except Exception as e:
        logger.error(f"Error during screenshot cleanup: {e}")


async def setup_browser_session(
    headless: bool = True,
    slow_mo: Optional[int] = None,
    user_agent: Optional[str] = None,
    viewport: Optional[Dict[str, int]] = None,
    locale: str = "en-GB",
    session_dir: Optional[Path] = None,
    debug: bool = False,
) -> Tuple:
    """
    Set up a Playwright browser session with custom configuration.

    Args:
        headless: Whether to run in headless mode
        slow_mo: Slow down execution by specified milliseconds
        user_agent: Custom user agent string
        viewport: Custom viewport dimensions
        locale: Browser locale
        session_dir: Directory to save screenshots and other artifacts
        debug: Whether to enable debug mode

    Returns:
        Tuple containing (playwright, browser, context, page)
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Please run ensure_playwright_installed() first")
        raise

    # Create screenshot directory if not provided
    if not session_dir:
        session_dir = setup_screenshot_directory()

    # Default viewport if not specified
    if not viewport:
        viewport = {"width": 1280, "height": 800}

    # Default user agent if not specified
    if not user_agent:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"

    # Setup browser
    p = await async_playwright().start()
    browser_args = []

    logger.info(f"Starting browser: headless={headless}, slow_mo={slow_mo}, debug={debug}")

    # Launch browser
    browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo, args=browser_args)

    # Create context
    context = await browser.new_context(user_agent=user_agent, viewport=viewport, locale=locale)

    # Load cookies if available
    cookie_file = Path("cookies.json")
    if cookie_file.exists():
        try:
            cookies = json.loads(cookie_file.read_text())
            await context.add_cookies(cookies)
            logger.info("Loaded cookies from cookies.json")
        except Exception as e:
            logger.warning(f"Failed to load cookies: {e}")

    # Create page
    page = await context.new_page()

    # Set default timeout (30 seconds)
    page.set_default_timeout(30000)

    # Add event listeners for debugging
    if debug:
        page.on("console", lambda msg: logger.debug(f"Browser console: {msg.text}"))
        page.on("request", lambda request: logger.debug(f"Request: {request.method} {request.url}"))
        page.on("response", lambda response: logger.debug(f"Response: {response.status} {response.url}"))

    # Configure page for screenshots
    await page.context.tracing.start(screenshots=True, snapshots=True)

    return p, browser, context, page


async def take_screenshot(page, name: str, session_dir: Optional[Path] = None) -> Path:
    """
    Take a screenshot of the current page.

    Args:
        page: Playwright page object
        name: Screenshot name (without extension)
        session_dir: Directory to save screenshot

    Returns:
        Path: Path to the screenshot file
    """
    if not session_dir:
        session_dir = setup_screenshot_directory()

    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = session_dir / filename

    await page.screenshot(path=str(filepath))
    logger.info(f"Screenshot saved to {filepath}")

    return filepath


async def cleanup_session(playwright, browser, context, page, session_dir: Optional[Path] = None) -> None:
    """
    Clean up browser session and save artifacts.

    Args:
        playwright: Playwright instance
        browser: Browser instance
        context: Browser context
        page: Page instance
        session_dir: Directory to save artifacts
    """
    if not session_dir:
        session_dir = SCREENSHOT_DIR

    try:
        # Save traces if needed
        trace_path = session_dir / "trace.zip"
        await context.tracing.stop(path=trace_path)
        logger.info(f"Trace saved to {trace_path}")

        # Save cookies for future sessions
        cookies = await context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)

        # Close everything
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

        logger.info("Browser session cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during browser session cleanup: {e}")


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()]
    )

    # Check if Playwright is installed
    if not ensure_playwright_installed():
        print("Please install Playwright and its dependencies first")
        sys.exit(1)

    # Set up screenshot directory and clean old screenshots
    screenshot_dir = setup_screenshot_directory()
    print(f"Screenshot directory set up at: {screenshot_dir}")

    print("Playwright utilities test complete")
