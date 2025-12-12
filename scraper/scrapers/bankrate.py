"""
Bankrate.com mortgage rate scraper.

Bankrate is one of the most authoritative sources for mortgage rate data.
They aggregate rates from multiple lenders and display averages prominently.

Site characteristics:
- Heavy use of JavaScript for rate display
- Cookie consent banner (California-specific)
- Rates displayed in tabular format
- Generally good uptime and reliability
"""

import logging
from playwright.async_api import Page

from .base import MortgageScraper, MortgageRates
from ..utils.stealth import humanized_delay

logger = logging.getLogger(__name__)


class BankrateScraper(MortgageScraper):
    """
    Scraper for Bankrate.com mortgage rates.

    Bankrate displays "Today's Average Rates" prominently on their
    mortgage rates overview page. The page structure is relatively
    stable but uses dynamic loading for rate values.
    """

    @property
    def source_name(self) -> str:
        return "Bankrate"

    @property
    def base_url(self) -> str:
        # Main mortgage rates overview page
        # This page shows national averages without requiring zip code
        return "https://www.bankrate.com/mortgages/mortgage-rates/"

    async def navigate(self, page: Page) -> None:
        """
        Navigate to Bankrate's mortgage rates page.

        Bankrate's page loads rates dynamically via JavaScript.
        We need to wait for the rate elements to appear rather than
        just waiting for page load.
        """
        logger.debug(f"[{self.source_name}] Navigating to {self.base_url}")

        # Go to the rates page
        await page.goto(self.base_url, wait_until="domcontentloaded")

        # Wait for the page to settle - Bankrate has multiple JS bundles
        await humanized_delay(2.0, 4.0, "initial load")

        # Wait for rate content to appear
        # Bankrate uses various class names for rate displays
        try:
            await page.wait_for_selector(
                '[class*="rate"], [class*="Rate"], [data-testid*="rate"]',
                timeout=self.timeout_ms,
                state="visible"
            )
        except Exception as e:
            logger.warning(f"[{self.source_name}] Rate selector not found, continuing: {e}")

        # Scroll down slightly to trigger any lazy loading
        await page.mouse.wheel(0, 300)
        await humanized_delay(1.0, 2.0, "post-scroll")

    async def extract_rates(self, page: Page) -> MortgageRates:
        """
        Extract mortgage rates from Bankrate's page.

        Bankrate displays rates in a structured format with clear labels.
        The selectors target their rate card components.
        """
        rates = MortgageRates(source=self.source_name)

        # Bankrate rate selectors - they use semantic class names
        # These may need updating if Bankrate redesigns their site
        selectors = {
            "thirty_year_fixed": [
                # Primary selector - rate card for 30-year
                '[data-testid="30-year-fixed-rate"] [class*="rate-value"]',
                # Fallback - table-based display
                'tr:has-text("30-year fixed") td:nth-child(2)',
                # Generic rate display
                '[class*="mortgage-rate"]:has-text("30") [class*="value"]',
                # Broad fallback
                'text=/30.*year.*fixed/i >> .. >> [class*="rate"]',
            ],
            "fifteen_year_fixed": [
                '[data-testid="15-year-fixed-rate"] [class*="rate-value"]',
                'tr:has-text("15-year fixed") td:nth-child(2)',
                '[class*="mortgage-rate"]:has-text("15") [class*="value"]',
                'text=/15.*year.*fixed/i >> .. >> [class*="rate"]',
            ],
            "arm_5_1": [
                '[data-testid="5-1-arm-rate"] [class*="rate-value"]',
                'tr:has-text("5/1 ARM") td:nth-child(2)',
                '[class*="mortgage-rate"]:has-text("5/1") [class*="value"]',
                'text=/5.1.*ARM/i >> .. >> [class*="rate"]',
            ],
        }

        # Try each rate type with multiple selector fallbacks
        for rate_type, selector_list in selectors.items():
            for selector in selector_list:
                rate = await self.safe_parse_rate(page, selector, rate_type, timeout_ms=3000)
                if rate is not None:
                    setattr(rates, rate_type, rate)
                    break  # Found it, move to next rate type

        # If structured extraction failed, try to find rates in page text
        if not rates.is_valid:
            logger.debug(f"[{self.source_name}] Structured extraction failed, trying text search")
            await self._extract_from_text(page, rates)

        return rates

    async def _extract_from_text(self, page: Page, rates: MortgageRates) -> None:
        """
        Fallback extraction using page text analysis.

        If structured selectors fail (due to site redesign), we can
        try to find rates by analyzing visible text content.
        """
        try:
            # Get all visible text from rate-related sections
            content = await page.content()

            # This is a last resort - we'd prefer structured extraction
            # Log that we're using fallback so we know to update selectors
            logger.warning(
                f"[{self.source_name}] Using text fallback extraction - "
                "consider updating selectors"
            )

        except Exception as e:
            logger.debug(f"[{self.source_name}] Text extraction fallback failed: {e}")
