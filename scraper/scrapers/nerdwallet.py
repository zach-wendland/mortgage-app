"""
NerdWallet.com mortgage rate scraper.

NerdWallet is a popular personal finance site that displays current
mortgage rates with good data visualization. They aggregate rates
from partner lenders.

Site characteristics:
- Clean, modern design
- Rates update frequently
- May show personalized rates based on location
- Heavy use of React components
"""

import logging
from playwright.async_api import Page

from .base import MortgageScraper, MortgageRates
from ..utils.stealth import humanized_delay

logger = logging.getLogger(__name__)


class NerdWalletScraper(MortgageScraper):
    """
    Scraper for NerdWallet.com mortgage rates.

    NerdWallet displays "Today's Mortgage Rates" on their rates page.
    The site uses React and loads rates dynamically.
    """

    @property
    def source_name(self) -> str:
        return "NerdWallet"

    @property
    def base_url(self) -> str:
        # NerdWallet's mortgage rates comparison page
        return "https://www.nerdwallet.com/mortgages/mortgage-rates"

    async def navigate(self, page: Page) -> None:
        """
        Navigate to NerdWallet's mortgage rates page.

        NerdWallet uses React with server-side rendering, so initial
        content should be available quickly. However, rate values
        may be hydrated client-side.
        """
        logger.debug(f"[{self.source_name}] Navigating to {self.base_url}")

        await page.goto(self.base_url, wait_until="networkidle")

        # NerdWallet sometimes shows a location prompt
        # Try to dismiss or skip it
        try:
            skip_btn = await page.wait_for_selector(
                'button:has-text("Skip"), button:has-text("Continue without")',
                timeout=3000
            )
            if skip_btn:
                await skip_btn.click()
                await humanized_delay(1.0, 2.0, "skip location")
        except Exception:
            pass  # No location prompt, continue

        # Wait for rate cards to load
        await humanized_delay(2.0, 3.0, "page settle")

        try:
            await page.wait_for_selector(
                '[class*="RateCard"], [class*="rate-card"], [data-testid*="rate"]',
                timeout=self.timeout_ms
            )
        except Exception as e:
            logger.warning(f"[{self.source_name}] Rate cards not found: {e}")

    async def extract_rates(self, page: Page) -> MortgageRates:
        """
        Extract mortgage rates from NerdWallet's page.

        NerdWallet uses card-based layout for different loan types.
        Rates are displayed prominently within each card.
        """
        rates = MortgageRates(source=self.source_name)

        # NerdWallet selector patterns
        # They use semantic naming but the exact classes may vary
        selectors = {
            "thirty_year_fixed": [
                # Card-based display
                '[data-testid="30-year-fixed-card"] [class*="rate"]',
                '[class*="RateCard"]:has-text("30-year") [class*="percentage"]',
                # Table fallback
                'tr:has-text("30-year fixed") [class*="rate"]',
                # Text-based matching
                ':text("30-year fixed") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
            "fifteen_year_fixed": [
                '[data-testid="15-year-fixed-card"] [class*="rate"]',
                '[class*="RateCard"]:has-text("15-year") [class*="percentage"]',
                'tr:has-text("15-year fixed") [class*="rate"]',
                ':text("15-year fixed") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
            "arm_5_1": [
                '[data-testid="5-1-arm-card"] [class*="rate"]',
                '[class*="RateCard"]:has-text("5/1 ARM") [class*="percentage"]',
                'tr:has-text("5/1 ARM") [class*="rate"]',
                ':text("5/1 ARM") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
        }

        for rate_type, selector_list in selectors.items():
            for selector in selector_list:
                rate = await self.safe_parse_rate(page, selector, rate_type, timeout_ms=3000)
                if rate is not None:
                    setattr(rates, rate_type, rate)
                    break

        # NerdWallet sometimes displays rates in a different format
        # Try alternative extraction if primary failed
        if not rates.is_valid:
            await self._try_alternative_extraction(page, rates)

        return rates

    async def _try_alternative_extraction(self, page: Page, rates: MortgageRates) -> None:
        """
        Alternative extraction for NerdWallet's secondary rate display.

        NerdWallet sometimes shows rates in a comparison table or
        inline text format that requires different selectors.
        """
        try:
            # Look for rate summary section
            summary_selectors = [
                '[class*="RateSummary"]',
                '[class*="rate-summary"]',
                '[aria-label*="mortgage rates"]',
            ]

            for selector in summary_selectors:
                try:
                    section = await page.wait_for_selector(selector, timeout=2000)
                    if section:
                        text = await section.text_content()
                        logger.debug(f"[{self.source_name}] Found summary section: {text[:100]}...")
                        # Parse rates from text if needed
                        break
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"[{self.source_name}] Alternative extraction failed: {e}")
