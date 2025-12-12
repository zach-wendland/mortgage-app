"""
Stealth utilities for avoiding bot detection during web scraping.

This module implements various anti-detection techniques to make automated
browser sessions appear more human-like. Financial sites often employ
sophisticated bot detection (Cloudflare, PerimeterX, DataDome), so these
measures are critical for reliable scraping.

Key techniques:
1. User-Agent rotation - Prevents fingerprinting based on static UA strings
2. Viewport randomization - Avoids detection of common automation viewport sizes
3. Humanized delays - Mimics natural human browsing patterns with random jitter
4. Mouse movement simulation - Some sites track mouse patterns for bot detection
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional, Tuple
from fake_useragent import UserAgent


# Initialize UserAgent once to avoid repeated network calls
# FakeUserAgent fetches real UA strings from browsers in the wild
_ua_generator = UserAgent(browsers=["chrome", "firefox", "edge"])


@dataclass
class StealthConfig:
    """
    Configuration container for stealth browser settings.

    Why these defaults?
    - viewport: Common desktop sizes, avoiding exact 1920x1080 which is too "perfect"
    - locale: US English for US financial sites
    - timezone: US timezone to match target audience
    - geolocation: Optional, some sites check for consistency with IP
    """

    # Viewport dimensions - randomized within reasonable desktop ranges
    # Avoiding perfectly round numbers (1920x1080) which scream "automation"
    viewport_width: int = field(default_factory=lambda: random.randint(1280, 1920))
    viewport_height: int = field(default_factory=lambda: random.randint(800, 1080))

    # Browser locale and timezone - must be consistent to avoid red flags
    locale: str = "en-US"
    timezone_id: str = "America/New_York"

    # User agent - dynamically generated
    user_agent: str = field(default_factory=lambda: _ua_generator.random)

    # Geolocation (optional) - set to None to skip
    # If used, should match IP geolocation roughly
    geolocation: Optional[dict] = None

    # Color scheme preference - "light" is most common
    color_scheme: str = "light"

    # Device scale factor - 1 for standard, 2 for retina
    # Randomizing helps avoid fingerprinting
    device_scale_factor: float = field(default_factory=lambda: random.choice([1, 1.25, 1.5, 2]))

    def to_context_options(self) -> dict:
        """
        Convert config to Playwright browser context options.

        These options are passed to browser.new_context() to configure
        the browser environment before any navigation occurs.
        """
        options = {
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "locale": self.locale,
            "timezone_id": self.timezone_id,
            "user_agent": self.user_agent,
            "color_scheme": self.color_scheme,
            "device_scale_factor": self.device_scale_factor,
            # Disable WebDriver flag - major bot detection vector
            # Sites check navigator.webdriver which Playwright sets to true by default
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
                # DNT header makes us look more like a privacy-conscious human
                "DNT": "1",
                # Upgrade-Insecure-Requests is sent by real browsers
                "Upgrade-Insecure-Requests": "1",
            },
        }

        if self.geolocation:
            options["geolocation"] = self.geolocation
            options["permissions"] = ["geolocation"]

        return options


def get_random_viewport() -> Tuple[int, int]:
    """
    Generate a randomized viewport size within common desktop ranges.

    Why randomize?
    - Default automation viewports (800x600, 1280x720) are known signatures
    - Real users have diverse screen sizes
    - Adding slight randomness (+/- 50px) makes each session unique

    Returns:
        Tuple of (width, height) in pixels
    """
    # Common desktop breakpoints with small random offsets
    base_widths = [1366, 1440, 1536, 1600, 1680, 1920]
    base_heights = [768, 900, 864, 1024, 1050, 1080]

    width = random.choice(base_widths) + random.randint(-50, 50)
    height = random.choice(base_heights) + random.randint(-30, 30)

    return width, height


async def humanized_delay(
    min_seconds: float = 2.0,
    max_seconds: float = 5.0,
    operation_name: str = "action"
) -> None:
    """
    Introduce a random delay to mimic human browsing behavior.

    Why humanized delays matter:
    1. Real humans don't click instantly - they read, think, move mouse
    2. Bot detection systems track timing patterns
    3. Perfectly consistent delays are themselves a red flag
    4. Too-fast navigation triggers rate limiting

    The delay uses a slightly weighted distribution favoring the middle
    of the range, as humans tend toward consistent but not identical timing.

    Args:
        min_seconds: Minimum delay (default 2s - typical human reaction time)
        max_seconds: Maximum delay (default 5s - accounts for reading/thinking)
        operation_name: For logging purposes

    Implementation note:
        We use triangular distribution instead of uniform because human
        reaction times follow a roughly normal distribution. The mode
        (peak) is set at 40% of the range for slight bias toward faster.
    """
    # Triangular distribution gives more natural timing variance
    # Mode at 40% of range mimics how humans are usually ready but occasionally slow
    mode = min_seconds + (max_seconds - min_seconds) * 0.4
    delay = random.triangular(min_seconds, max_seconds, mode)

    await asyncio.sleep(delay)


async def simulate_mouse_movement(page, start: Tuple[int, int], end: Tuple[int, int]) -> None:
    """
    Simulate natural mouse movement between two points.

    Why simulate mouse movement?
    - Some anti-bot systems (PerimeterX, Kasada) track mouse patterns
    - Instant teleportation to click targets is inhuman
    - Real mouse paths have slight curves and speed variations

    This uses a simple bezier-like curve with random control points
    to create organic-looking paths.

    Args:
        page: Playwright page object
        start: Starting (x, y) coordinates
        end: Ending (x, y) coordinates
    """
    steps = random.randint(10, 25)  # Number of intermediate points

    # Generate a slight curve by adding random offset to midpoint
    mid_x = (start[0] + end[0]) / 2 + random.randint(-50, 50)
    mid_y = (start[1] + end[1]) / 2 + random.randint(-30, 30)

    for i in range(steps + 1):
        # Quadratic bezier curve calculation
        t = i / steps

        # B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
        x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * mid_x + t ** 2 * end[0]
        y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * mid_y + t ** 2 * end[1]

        await page.mouse.move(x, y)

        # Variable speed - slower at start and end (acceleration/deceleration)
        # This mimics how humans actually move mice
        speed_factor = 1 - abs(2 * t - 1)  # Peaks at t=0.5
        delay = 0.01 + 0.02 * (1 - speed_factor)
        await asyncio.sleep(delay)


async def random_scroll(page, direction: str = "down", pixels: Optional[int] = None) -> None:
    """
    Perform a natural-looking scroll action.

    Why randomize scrolling?
    - Bots often scroll in exact increments (100px, 500px)
    - Humans scroll in varied amounts based on content
    - Scroll patterns can be fingerprinted

    Args:
        page: Playwright page object
        direction: "up" or "down"
        pixels: Specific amount to scroll, or None for random
    """
    if pixels is None:
        # Humans typically scroll between 200-800px depending on content density
        pixels = random.randint(200, 600)

    if direction == "up":
        pixels = -pixels

    # Smooth scroll in chunks to look natural
    chunks = random.randint(3, 6)
    chunk_size = pixels // chunks

    for _ in range(chunks):
        await page.mouse.wheel(0, chunk_size)
        await asyncio.sleep(random.uniform(0.05, 0.15))


def generate_fresh_config() -> StealthConfig:
    """
    Generate a completely fresh stealth configuration.

    Call this for each new browser context to ensure unique fingerprints.
    Reusing configs across sessions can create detectable patterns.

    Returns:
        New StealthConfig instance with randomized values
    """
    width, height = get_random_viewport()

    return StealthConfig(
        viewport_width=width,
        viewport_height=height,
        user_agent=_ua_generator.random,
        device_scale_factor=random.choice([1, 1.25, 1.5, 2]),
    )
