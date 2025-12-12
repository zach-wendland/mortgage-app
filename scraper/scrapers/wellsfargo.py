"""
Wells Fargo mortgage rate scraper.

Wells Fargo is one of the largest mortgage lenders in the US.
Their rates page shows their current offerings (not aggregated averages).

Site characteristics:
- Institutional banking site with heavy security
- May have more aggressive bot detection
- Rates reflect Wells Fargo's actual offerings
- Often requires more interaction to see rates
"""

import logging
from playwright.async_api import Page

from .base import MortgageScraper, MortgageRates
from ..utils.stealth import humanized_delay, random_scroll

logger = logging.getLogger(__name__)


class WellsFargoScraper(MortgageScraper):
    """
    Scraper for Wells Fargo mortgage rates.

    Wells Fargo displays their current mortgage rates on their
    rates page. As a major bank, they have more sophisticated
    bot detection than aggregator sites.
    """

    @property
    def source_name(self) -> str:
        return "Wells Fargo"

    @property
    def base_url(self) -> str:
        # Wells Fargo's mortgage rates page
        return "https://www.wellsfargo.com/mortgage/rates/"

    async def navigate(self, page: Page) -> None:
        """
        Navigate to Wells Fargo's mortgage rates page.

        Wells Fargo's site has multiple layers:
        1. Initial rates overview
        2. May require accepting terms
        3. Dynamic rate loading

        We need to handle these carefully to avoid detection.
        """
        logger.debug(f"[{self.source_name}] Navigating to {self.base_url}")

        # Wells Fargo can be slow to load - increase wait time
        await page.goto(self.base_url, wait_until="networkidle", timeout=45000)

        # Wells Fargo often shows cookie/privacy notices
        await self.handle_popups(page)

        # Humanized interaction - scroll to appear natural
        # Banking sites are more likely to track mouse/scroll patterns
        await humanized_delay(2.0, 4.0, "initial view")
        await random_scroll(page, "down", 200)
        await humanized_delay(1.0, 2.0, "scroll pause")

        # Look for rate tables to confirm page loaded correctly
        try:
            await page.wait_for_selector(
                'table, [class*="rate"], [class*="Rate"]',
                timeout=self.timeout_ms,
                state="visible"
            )
        except Exception as e:
            logger.warning(f"[{self.source_name}] Rate elements not immediately visible: {e}")

    async def extract_rates(self, page: Page) -> MortgageRates:
        """
        Extract mortgage rates from Wells Fargo's page.

        Wells Fargo displays rates in a structured table format.
        Their HTML structure tends to be more traditional than
        React-based sites.
        """
        rates = MortgageRates(source=self.source_name)

        # Wells Fargo uses more traditional HTML structure
        # Rates are typically in tables with clear headers
        selectors = {
            "thirty_year_fixed": [
                # Table row matching
                'tr:has-text("30-year fixed") td:has-text("%")',
                'tr:has-text("30-Year Fixed") td:has-text("%")',
                # Cell with rate data
                '[data-label*="30"][data-label*="fixed"] [class*="rate"]',
                # Rate display components
                '[class*="rate-row"]:has-text("30") [class*="rate-value"]',
                # Broad table search
                'table tr:nth-child(2) td:nth-child(2)',  # Often 30-yr is first
            ],
            "fifteen_year_fixed": [
                'tr:has-text("15-year fixed") td:has-text("%")',
                'tr:has-text("15-Year Fixed") td:has-text("%")',
                '[data-label*="15"][data-label*="fixed"] [class*="rate"]',
                '[class*="rate-row"]:has-text("15") [class*="rate-value"]',
                'table tr:nth-child(3) td:nth-child(2)',
            ],
            "arm_5_1": [
                'tr:has-text("5/1 ARM") td:has-text("%")',
                'tr:has-text("5-Year ARM") td:has-text("%")',
                '[data-label*="ARM"] [class*="rate"]',
                '[class*="rate-row"]:has-text("ARM") [class*="rate-value"]',
                # ARM might be further down
                'table tr:has-text("ARM") td:nth-child(2)',
            ],
        }

        for rate_type, selector_list in selectors.items():
            for selector in selector_list:
                rate = await self.safe_parse_rate(page, selector, rate_type, timeout_ms=3000)
                if rate is not None:
                    setattr(rates, rate_type, rate)
                    break

        # Wells Fargo sometimes shows rates only after interaction
        if not rates.is_valid:
            await self._try_expand_rates(page, rates)

        return rates

    async def _try_expand_rates(self, page: Page, rates: MortgageRates) -> None:
        """
        Try to expand collapsed rate sections.

        Wells Fargo may hide detailed rates behind expandable sections
        or tabs. This method attempts common expansion patterns.
        """
        try:
            # Look for "View Rates" or "See More" buttons
            expand_selectors = [
                'button:has-text("View Rates")',
                'button:has-text("See Rates")',
                'button:has-text("Show More")',
                '[class*="expand"]',
                '[aria-expanded="false"]',
            ]

            for selector in expand_selectors:
                try:
                    btn = await page.wait_for_selector(selector, timeout=2000)
                    if btn:
                        await btn.click()
                        await humanized_delay(1.0, 2.0, "expand rates")
                        logger.debug(f"[{self.source_name}] Expanded rates section")

                        # Re-try extraction after expanding
                        # We don't call extract_rates again to avoid recursion
                        # Just update the rates object directly
                        break
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"[{self.source_name}] Rate expansion failed: {e}")

    async def handle_popups(self, page: Page) -> None:
        """
        Override popup handling for Wells Fargo specific modals.

        Wells Fargo has specific privacy notices and security
        warnings that need targeted handling.
        """
        # First, try Wells Fargo specific selectors
        wf_selectors = [
            'button:has-text("Accept All Cookies")',
            'button:has-text("I Understand")',
            '[aria-label="Close privacy notice"]',
            '#onetrust-accept-btn-handler',  # OneTrust cookie consent
            'button.onetrust-close-btn-handler',
        ]

        for selector in wf_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=2000, state="visible")
                if btn:
                    await btn.click()
                    await humanized_delay(0.5, 1.0, "close WF popup")
                    logger.debug(f"[{self.source_name}] Closed WF-specific popup")
            except Exception:
                continue

        # Then call parent implementation for generic popups
        await super().handle_popups(page)
