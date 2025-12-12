"""
Zillow.com mortgage rate scraper.

Zillow is a major real estate platform that also displays current
mortgage rates from their lender network. They acquired Zillow Home
Loans and display competitive rates.

Site characteristics:
- React-based SPA
- Aggressive bot detection (PerimeterX)
- Rates may be personalized by location
- Modern, responsive design
"""

import logging
from playwright.async_api import Page

from .base import MortgageScraper, MortgageRates
from ..utils.stealth import humanized_delay, random_scroll, simulate_mouse_movement

logger = logging.getLogger(__name__)


class ZillowScraper(MortgageScraper):
    """
    Scraper for Zillow.com mortgage rates.

    Zillow has one of the more aggressive anti-bot systems.
    This scraper includes extra stealth measures to improve
    success rates.
    """

    @property
    def source_name(self) -> str:
        return "Zillow"

    @property
    def base_url(self) -> str:
        # Zillow's mortgage rates page
        return "https://www.zillow.com/mortgage-rates/"

    async def navigate(self, page: Page) -> None:
        """
        Navigate to Zillow's mortgage rates page.

        Zillow uses PerimeterX for bot detection. We need to:
        1. Navigate slowly and naturally
        2. Handle CAPTCHA challenges (by failing gracefully)
        3. Wait for React to render
        """
        logger.debug(f"[{self.source_name}] Navigating to {self.base_url}")

        # Navigate with longer timeout - Zillow can be slow
        await page.goto(self.base_url, wait_until="networkidle", timeout=60000)

        # Check for bot detection challenge page
        is_blocked = await self._check_for_block(page)
        if is_blocked:
            logger.warning(f"[{self.source_name}] Bot detection triggered - rates may be unavailable")
            # Don't raise - let extraction try anyway

        # Extra humanization for Zillow
        await self._humanize_session(page)

        # Handle Zillow-specific overlays
        await self._handle_zillow_popups(page)

        # Wait for rate content
        try:
            await page.wait_for_selector(
                '[class*="rate"], [data-testid*="rate"], [class*="Rate"]',
                timeout=self.timeout_ms
            )
        except Exception as e:
            logger.warning(f"[{self.source_name}] Rate elements not found: {e}")

    async def _check_for_block(self, page: Page) -> bool:
        """
        Check if we've been blocked by bot detection.

        Signs of blocking:
        - CAPTCHA challenge
        - "Please verify you're human" text
        - PerimeterX challenge page
        """
        block_indicators = [
            'text=Please verify',
            'text=checking your browser',
            'text=Access Denied',
            '[class*="captcha"]',
            '#px-captcha',
        ]

        for indicator in block_indicators:
            try:
                element = await page.query_selector(indicator)
                if element:
                    return True
            except Exception:
                continue

        return False

    async def _humanize_session(self, page: Page) -> None:
        """
        Add extra humanization for Zillow's aggressive detection.

        Zillow tracks:
        - Mouse movements
        - Scroll patterns
        - Time on page
        - Interaction sequences
        """
        # Initial delay - humans don't act instantly
        await humanized_delay(2.0, 4.0, "initial delay")

        # Natural mouse movement to center of viewport
        viewport = page.viewport_size
        if viewport:
            center_x = viewport["width"] // 2
            center_y = viewport["height"] // 2

            # Move mouse naturally to center area
            await simulate_mouse_movement(
                page,
                start=(100, 100),
                end=(center_x, center_y)
            )

        # Scroll down slowly as if reading
        await random_scroll(page, "down", 150)
        await humanized_delay(1.5, 2.5, "read content")
        await random_scroll(page, "down", 200)
        await humanized_delay(1.0, 2.0, "continue reading")

    async def _handle_zillow_popups(self, page: Page) -> None:
        """
        Handle Zillow-specific popups and modals.

        Zillow shows:
        - Sign-in prompts
        - Location permission requests
        - Newsletter signup
        - Cookie consent
        """
        zillow_selectors = [
            # Sign-in/signup dismissal
            'button:has-text("Maybe later")',
            'button:has-text("Not now")',
            '[aria-label="Close modal"]',
            'button[aria-label="Close"]',
            # Cookie/privacy
            'button:has-text("Accept")',
            '#cookie-consent-accept',
            # Notification prompts
            'button:has-text("No thanks")',
            '[class*="modal"] [class*="close"]',
            # Location prompt
            'button:has-text("Skip")',
        ]

        for selector in zillow_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=1500, state="visible")
                if btn:
                    # Move mouse to button before clicking (more human-like)
                    box = await btn.bounding_box()
                    if box:
                        await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                        await humanized_delay(0.2, 0.5, "pre-click")

                    await btn.click()
                    await humanized_delay(0.5, 1.0, "post-popup")
                    logger.debug(f"[{self.source_name}] Dismissed Zillow popup")
            except Exception:
                continue

    async def extract_rates(self, page: Page) -> MortgageRates:
        """
        Extract mortgage rates from Zillow's page.

        Zillow displays rates in a modern card/grid layout.
        The exact structure depends on their A/B testing.
        """
        rates = MortgageRates(source=self.source_name)

        # Zillow selector patterns
        # They use various React component structures
        selectors = {
            "thirty_year_fixed": [
                # Data test IDs (most reliable if present)
                '[data-testid="30-year-fixed-rate"]',
                '[data-testid*="rate-30"]',
                # Component class patterns
                '[class*="RateCard"]:has-text("30-year") [class*="rate"]',
                '[class*="mortgage-rate"]:has-text("30") [class*="value"]',
                # Table/list patterns
                'tr:has-text("30-year") td:has-text("%")',
                '[class*="rate-row"]:has-text("30") [class*="percentage"]',
                # Text-based fallback
                ':text("30-Year Fixed") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
            "fifteen_year_fixed": [
                '[data-testid="15-year-fixed-rate"]',
                '[data-testid*="rate-15"]',
                '[class*="RateCard"]:has-text("15-year") [class*="rate"]',
                '[class*="mortgage-rate"]:has-text("15") [class*="value"]',
                'tr:has-text("15-year") td:has-text("%")',
                '[class*="rate-row"]:has-text("15") [class*="percentage"]',
                ':text("15-Year Fixed") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
            "arm_5_1": [
                '[data-testid*="arm-rate"]',
                '[data-testid*="rate-arm"]',
                '[class*="RateCard"]:has-text("ARM") [class*="rate"]',
                '[class*="mortgage-rate"]:has-text("ARM") [class*="value"]',
                'tr:has-text("ARM") td:has-text("%")',
                '[class*="rate-row"]:has-text("ARM") [class*="percentage"]',
                ':text("ARM") >> .. >> :text-matches("\\d+\\.\\d+%")',
            ],
        }

        for rate_type, selector_list in selectors.items():
            for selector in selector_list:
                rate = await self.safe_parse_rate(page, selector, rate_type, timeout_ms=3000)
                if rate is not None:
                    setattr(rates, rate_type, rate)
                    break

        # Zillow may require zip code to show rates
        if not rates.is_valid:
            await self._try_zip_code_entry(page, rates)

        return rates

    async def _try_zip_code_entry(self, page: Page, rates: MortgageRates) -> None:
        """
        Try entering zip code to reveal personalized rates.

        Zillow often shows a zip code prompt before displaying
        actual rate data.
        """
        try:
            # Look for zip code input
            zip_selectors = [
                'input[placeholder*="ZIP"]',
                'input[placeholder*="zip"]',
                'input[name*="zip"]',
                'input[aria-label*="ZIP"]',
                '[data-testid="zip-input"]',
            ]

            for selector in zip_selectors:
                try:
                    zip_input = await page.wait_for_selector(selector, timeout=2000, state="visible")
                    if zip_input:
                        # Clear any existing value
                        await zip_input.fill("")
                        await humanized_delay(0.3, 0.5, "clear input")

                        # Type zip code with human-like timing
                        await zip_input.type(self.zip_code, delay=100)  # 100ms between keys
                        await humanized_delay(0.5, 1.0, "post-type")

                        # Submit
                        await zip_input.press("Enter")
                        await humanized_delay(2.0, 3.0, "rate load")

                        logger.debug(f"[{self.source_name}] Entered zip code {self.zip_code}")
                        break
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"[{self.source_name}] Zip code entry failed: {e}")

    async def handle_popups(self, page: Page) -> None:
        """Override to include Zillow-specific handling."""
        await self._handle_zillow_popups(page)
        await super().handle_popups(page)
