"""
Chase.com mortgage rate scraper.

Chase is another major US bank with significant mortgage presence.
Their rates page shows their current offerings.

Site characteristics:
- Heavy JavaScript application
- Likely has sophisticated bot detection
- May require location/zip input
- Clean, modern design
"""

import logging
from playwright.async_api import Page

from .base import MortgageScraper, MortgageRates
from ..utils.stealth import humanized_delay, random_scroll

logger = logging.getLogger(__name__)


class ChaseScraper(MortgageScraper):
    """
    Scraper for Chase.com mortgage rates.

    Chase displays mortgage rates on their home lending pages.
    As a major bank, they have enterprise-grade security measures.
    """

    @property
    def source_name(self) -> str:
        return "Chase"

    @property
    def base_url(self) -> str:
        # Chase mortgage rates page
        return "https://www.chase.com/personal/mortgage/mortgage-rates"

    async def navigate(self, page: Page) -> None:
        """
        Navigate to Chase's mortgage rates page.

        Chase uses a modern SPA architecture with heavy client-side
        rendering. We need to wait for the JavaScript to hydrate.
        """
        logger.debug(f"[{self.source_name}] Navigating to {self.base_url}")

        # Chase can have slow initial load due to heavy JS
        await page.goto(self.base_url, wait_until="domcontentloaded", timeout=45000)

        # Handle Chase-specific popups first
        await self._handle_chase_popups(page)

        # Allow time for React/Angular hydration
        await humanized_delay(3.0, 5.0, "JS hydration")

        # Simulate natural browsing - scroll and pause
        await random_scroll(page, "down", 150)
        await humanized_delay(1.0, 2.0, "browse pause")

        # Wait for rate content
        try:
            await page.wait_for_selector(
                '[class*="rate"], [class*="Rate"], [data-module*="rate"]',
                timeout=self.timeout_ms
            )
        except Exception as e:
            logger.warning(f"[{self.source_name}] Rate elements not found: {e}")

    async def _handle_chase_popups(self, page: Page) -> None:
        """
        Handle Chase-specific popups and overlays.

        Chase has:
        - Cookie consent (OneTrust)
        - Security notices
        - Chat widgets
        - Location prompts
        """
        chase_selectors = [
            # OneTrust cookie consent (common on Chase)
            '#onetrust-accept-btn-handler',
            'button:has-text("Accept All")',
            # Chase-specific modals
            '[class*="modal"] button:has-text("Close")',
            '[class*="Modal"] button:has-text("OK")',
            # Chat widget dismiss
            '[aria-label="Close chat"]',
            'button:has-text("No thanks")',
            # Security/disclaimer acceptance
            'button:has-text("I understand")',
            'button:has-text("Continue")',
        ]

        for selector in chase_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=2000, state="visible")
                if btn:
                    await btn.click()
                    await humanized_delay(0.5, 1.0, "chase popup")
                    logger.debug(f"[{self.source_name}] Dismissed Chase popup")
            except Exception:
                continue

    async def extract_rates(self, page: Page) -> MortgageRates:
        """
        Extract mortgage rates from Chase's page.

        Chase displays rates in cards or table format.
        Their structure tends to be component-based.
        """
        rates = MortgageRates(source=self.source_name)

        # Chase selector patterns
        selectors = {
            "thirty_year_fixed": [
                # Card/component based
                '[data-testid*="30"][data-testid*="rate"]',
                '[class*="rate-card"]:has-text("30") [class*="rate-value"]',
                # Table structure
                'tr:has-text("30-Year Fixed") td:has-text("%")',
                'tr:has-text("30-year") td:nth-child(2)',
                # Module-based layout
                '[data-module*="rate"]:has-text("30") [class*="value"]',
                # Generic percentage near 30-year text
                ':text("30-Year") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
            "fifteen_year_fixed": [
                '[data-testid*="15"][data-testid*="rate"]',
                '[class*="rate-card"]:has-text("15") [class*="rate-value"]',
                'tr:has-text("15-Year Fixed") td:has-text("%")',
                'tr:has-text("15-year") td:nth-child(2)',
                '[data-module*="rate"]:has-text("15") [class*="value"]',
                ':text("15-Year") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
            "arm_5_1": [
                '[data-testid*="arm"][data-testid*="rate"]',
                '[class*="rate-card"]:has-text("ARM") [class*="rate-value"]',
                'tr:has-text("ARM") td:has-text("%")',
                '[data-module*="rate"]:has-text("ARM") [class*="value"]',
                ':text("ARM") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
        }

        for rate_type, selector_list in selectors.items():
            for selector in selector_list:
                rate = await self.safe_parse_rate(page, selector, rate_type, timeout_ms=3000)
                if rate is not None:
                    setattr(rates, rate_type, rate)
                    break

        # Chase may require clicking to reveal rates
        if not rates.is_valid:
            await self._try_reveal_rates(page, rates)

        return rates

    async def _try_reveal_rates(self, page: Page, rates: MortgageRates) -> None:
        """
        Try to reveal rates that might be hidden behind interactions.

        Chase sometimes requires:
        - Selecting a loan type
        - Entering location
        - Clicking "View Rates"
        """
        try:
            # Look for rate reveal buttons
            reveal_selectors = [
                'button:has-text("See Rates")',
                'button:has-text("View Rates")',
                'button:has-text("Get Started")',
                '[class*="cta"]:has-text("Rates")',
            ]

            for selector in reveal_selectors:
                try:
                    btn = await page.wait_for_selector(selector, timeout=2000, state="visible")
                    if btn:
                        await btn.click()
                        await humanized_delay(2.0, 3.0, "reveal rates")
                        logger.debug(f"[{self.source_name}] Clicked rate reveal button")
                        break
                except Exception:
                    continue

            # If there's a zip code input, try entering it
            zip_input = await page.query_selector('input[placeholder*="ZIP"], input[name*="zip"]')
            if zip_input:
                await zip_input.fill(self.zip_code)
                await humanized_delay(0.5, 1.0, "zip entry")

                # Submit the form
                submit = await page.query_selector('button[type="submit"], button:has-text("Submit")')
                if submit:
                    await submit.click()
                    await humanized_delay(2.0, 3.0, "zip submit")

        except Exception as e:
            logger.debug(f"[{self.source_name}] Rate reveal attempt failed: {e}")

    async def handle_popups(self, page: Page) -> None:
        """Override to include Chase-specific handling."""
        await self._handle_chase_popups(page)
        await super().handle_popups(page)
