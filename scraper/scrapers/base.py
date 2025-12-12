"""
Abstract base class for mortgage rate scrapers.

This module defines the contract that all site-specific scrapers must follow.
Using an abstract base class ensures:
1. Consistent interface across all scrapers
2. Shared functionality (popup handling, stealth setup) in one place
3. Easy addition of new sources without modifying existing code
4. Type safety and IDE support
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from ..utils.stealth import StealthConfig, generate_fresh_config, humanized_delay
from ..utils.helpers import retry_async, parse_rate_string, clean_text

logger = logging.getLogger(__name__)


@dataclass
class MortgageRates:
    """
    Data container for mortgage rate information from a single source.

    All rates are stored as floats (e.g., 6.5 for 6.5%).
    None indicates the rate was not available or could not be parsed.
    """

    source: str  # Name of the financial institution/website
    thirty_year_fixed: Optional[float] = None
    fifteen_year_fixed: Optional[float] = None
    arm_5_1: Optional[float] = None  # 5/1 Adjustable Rate Mortgage
    scraped_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None  # Error message if scrape failed
    duration_ms: float = 0.0  # How long the scrape took

    @property
    def is_valid(self) -> bool:
        """Check if we got at least one valid rate."""
        return any([
            self.thirty_year_fixed is not None,
            self.fifteen_year_fixed is not None,
            self.arm_5_1 is not None,
        ])

    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame creation."""
        return {
            "source": self.source,
            "30_year_fixed": self.thirty_year_fixed,
            "15_year_fixed": self.fifteen_year_fixed,
            "5_1_arm": self.arm_5_1,
            "scraped_at": self.scraped_at.isoformat(),
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


class MortgageScraper(ABC):
    """
    Abstract base class for mortgage rate scrapers.

    Each subclass targets a specific financial website and implements
    the site-specific extraction logic while inheriting common functionality
    like popup handling and stealth configuration.

    Lifecycle:
    1. __init__() - Store configuration (zip code, etc.)
    2. scrape() - Public entry point, manages browser lifecycle
    3. navigate() - Go to the rates page, handle redirects
    4. handle_popups() - Dismiss modals, cookie banners
    5. extract_rates() - Parse rates from the DOM

    Subclasses MUST implement:
    - source_name: Property returning the display name
    - base_url: Property returning the starting URL
    - navigate(): Site-specific navigation logic
    - extract_rates(): Site-specific DOM parsing
    """

    # Common popup/modal dismiss button selectors
    # These cover the vast majority of cookie banners and signup modals
    COMMON_POPUP_SELECTORS: List[str] = [
        # Cookie consent buttons (GDPR/CCPA)
        'button:has-text("Accept")',
        'button:has-text("Accept All")',
        'button:has-text("Accept Cookies")',
        'button:has-text("I Accept")',
        'button:has-text("Got it")',
        'button:has-text("Agree")',
        # Modal close buttons
        'button:has-text("Close")',
        'button:has-text("No Thanks")',
        'button:has-text("No, Thanks")',
        'button:has-text("Not Now")',
        'button:has-text("Maybe Later")',
        'button:has-text("Skip")',
        # Generic close buttons (X icons)
        '[aria-label="Close"]',
        '[aria-label="close"]',
        '[aria-label="Dismiss"]',
        'button.close',
        '.modal-close',
        '.popup-close',
        # Common class patterns
        '[class*="cookie"] button',
        '[class*="consent"] button',
        '[class*="modal"] [class*="close"]',
    ]

    def __init__(
        self,
        zip_code: str = "90210",
        headless: bool = True,
        timeout_ms: int = 30000,
    ):
        """
        Initialize the scraper with configuration.

        Args:
            zip_code: US ZIP code for location-specific rates (default: Beverly Hills)
            headless: Run browser without visible window (default: True)
            timeout_ms: Maximum wait time for page loads/elements (default: 30s)
        """
        self.zip_code = zip_code
        self.headless = headless
        self.timeout_ms = timeout_ms

        # These are set during scrape()
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._stealth_config: Optional[StealthConfig] = None

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Human-readable name of this data source.

        Example: "Bankrate", "NerdWallet", "Wells Fargo"
        """
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """
        Starting URL for the scraper.

        This should be the page where mortgage rates are displayed,
        or the closest publicly accessible page to it.
        """
        pass

    @abstractmethod
    async def navigate(self, page: Page) -> None:
        """
        Navigate to the rates page and prepare for extraction.

        This method should:
        1. Go to base_url (or start there)
        2. Handle any required interactions (zip code entry, dropdowns)
        3. Wait for rate data to load
        4. Leave the page ready for extract_rates()

        Args:
            page: Playwright Page object

        Raises:
            TimeoutError: If page doesn't load in time
            Exception: For site-specific navigation failures
        """
        pass

    @abstractmethod
    async def extract_rates(self, page: Page) -> MortgageRates:
        """
        Extract mortgage rate data from the current page.

        This method should:
        1. Locate rate elements using site-specific selectors
        2. Parse the text into numeric values
        3. Return a MortgageRates object with available data

        Args:
            page: Playwright Page object (should already be on rates page)

        Returns:
            MortgageRates object with extracted data
        """
        pass

    async def handle_popups(self, page: Page) -> None:
        """
        Attempt to dismiss common popups, modals, and cookie banners.

        This method tries multiple common selectors to close overlays.
        It's designed to be non-blocking - if no popups exist, it returns quickly.

        Why this is important:
        - Popups can block rate elements, causing extraction to fail
        - Cookie consent banners are legally required in many jurisdictions
        - Signup modals are common on financial sites

        The method uses a short timeout per selector to avoid waiting
        too long when popups don't exist.
        """
        logger.debug(f"[{self.source_name}] Checking for popups...")

        for selector in self.COMMON_POPUP_SELECTORS:
            try:
                # Short timeout - we don't want to wait long for each selector
                button = await page.wait_for_selector(selector, timeout=1000, state="visible")
                if button:
                    await button.click()
                    logger.debug(f"[{self.source_name}] Closed popup using: {selector}")
                    # Brief delay to let modal animation complete
                    await asyncio.sleep(0.5)
            except PlaywrightTimeoutError:
                # No popup found with this selector - expected and fine
                continue
            except Exception as e:
                # Log but don't fail - popup handling is best-effort
                logger.debug(f"[{self.source_name}] Error with selector {selector}: {e}")
                continue

    async def _setup_browser(self) -> tuple[Browser, BrowserContext, Page]:
        """
        Initialize Playwright browser with stealth configuration.

        This method:
        1. Launches Chromium (most compatible with financial sites)
        2. Creates a context with randomized fingerprint
        3. Configures anti-detection measures
        4. Returns ready-to-use browser objects

        Returns:
            Tuple of (Browser, BrowserContext, Page)
        """
        # Generate fresh stealth config for this session
        # Each scrape gets unique fingerprint to avoid detection patterns
        self._stealth_config = generate_fresh_config()

        logger.debug(
            f"[{self.source_name}] Launching browser with viewport "
            f"{self._stealth_config.viewport_width}x{self._stealth_config.viewport_height}"
        )

        # Start Playwright and launch browser
        playwright = await async_playwright().start()

        # Use Chromium - best compatibility with modern sites
        # Firefox and WebKit have more detection vectors
        browser = await playwright.chromium.launch(
            headless=self.headless,
            # Slow down operations slightly in non-headless mode for debugging
            slow_mo=50 if not self.headless else 0,
        )

        # Create context with stealth settings
        context = await browser.new_context(
            **self._stealth_config.to_context_options()
        )

        # Set default timeout for all operations
        context.set_default_timeout(self.timeout_ms)

        # Create page
        page = await context.new_page()

        # Additional stealth: remove automation indicators
        # This script runs before any page JavaScript
        await page.add_init_script("""
            // Remove webdriver property - major bot detection vector
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override plugins to look like real browser
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // Chrome-specific: add chrome object
            window.chrome = {
                runtime: {}
            };
        """)

        return browser, context, page

    async def _cleanup(self) -> None:
        """
        Clean up browser resources.

        Always called in finally block to prevent memory leaks.
        Playwright browsers are heavyweight - failing to close them
        can exhaust system resources quickly.
        """
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()

        self._page = None
        self._context = None
        self._browser = None

    @retry_async(max_attempts=3, exceptions=(PlaywrightTimeoutError, Exception))
    async def scrape(self) -> MortgageRates:
        """
        Main entry point - scrape mortgage rates from this source.

        This method orchestrates the full scraping flow:
        1. Set up browser with stealth config
        2. Navigate to rates page
        3. Handle any popups/modals
        4. Extract rate data
        5. Clean up browser resources

        The method is decorated with @retry_async for resilience against
        transient failures (network issues, temporary blocks, etc.).

        Returns:
            MortgageRates object with scraped data

        Raises:
            Exception: If scraping fails after all retry attempts
        """
        start_time = time.time()

        try:
            logger.info(f"[{self.source_name}] Starting scrape...")

            # Set up browser
            self._browser, self._context, self._page = await self._setup_browser()

            # Navigate to rates page
            await self.navigate(self._page)

            # Small delay after navigation for dynamic content
            await humanized_delay(1.0, 2.0, "post-navigation")

            # Handle any popups
            await self.handle_popups(self._page)

            # Extract rates
            rates = await self.extract_rates(self._page)
            rates.duration_ms = (time.time() - start_time) * 1000

            if rates.is_valid:
                logger.info(f"[{self.source_name}] Successfully scraped rates")
            else:
                logger.warning(f"[{self.source_name}] Scrape completed but no valid rates found")

            return rates

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[{self.source_name}] Scrape failed: {e}")

            return MortgageRates(
                source=self.source_name,
                error=str(e),
                duration_ms=duration_ms,
            )

        finally:
            # ALWAYS clean up browser resources
            # This runs even if an exception is raised
            await self._cleanup()

    async def safe_get_text(
        self,
        page: Page,
        selector: str,
        timeout_ms: int = 5000
    ) -> Optional[str]:
        """
        Safely extract text from an element, returning None on failure.

        This helper prevents extraction failures from crashing the whole scrape.
        If one rate isn't found, we still want to get the others.

        Args:
            page: Playwright Page object
            selector: CSS selector for the element
            timeout_ms: How long to wait for element

        Returns:
            Cleaned text content or None if element not found
        """
        try:
            element = await page.wait_for_selector(selector, timeout=timeout_ms)
            if element:
                text = await element.text_content()
                return clean_text(text) if text else None
        except PlaywrightTimeoutError:
            logger.debug(f"[{self.source_name}] Element not found: {selector}")
        except Exception as e:
            logger.debug(f"[{self.source_name}] Error getting text from {selector}: {e}")

        return None

    async def safe_parse_rate(
        self,
        page: Page,
        selector: str,
        rate_name: str,
        timeout_ms: int = 5000
    ) -> Optional[float]:
        """
        Safely extract and parse a rate from an element.

        Combines element location, text extraction, and rate parsing
        with comprehensive error handling.

        Args:
            page: Playwright Page object
            selector: CSS selector for the rate element
            rate_name: Human-readable name for logging
            timeout_ms: How long to wait for element

        Returns:
            Parsed rate as float or None if extraction/parsing fails
        """
        text = await self.safe_get_text(page, selector, timeout_ms)
        if text:
            rate = parse_rate_string(text)
            if rate:
                logger.debug(f"[{self.source_name}] Found {rate_name}: {rate}%")
            return rate
        return None
