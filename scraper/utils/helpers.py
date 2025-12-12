"""
Helper utilities for the mortgage rate scraper.

This module provides common functionality used across all scrapers:
- Retry logic with exponential backoff
- Rate string parsing (handling various formats like "6.5%", "6.50 %")
- Data formatting for output
"""

import asyncio
import re
import logging
from functools import wraps
from typing import Callable, Any, Optional, TypeVar, ParamSpec
from datetime import datetime

# Type hints for the retry decorator
P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for async functions that implements retry with exponential backoff.

    Why exponential backoff?
    - Gives servers time to recover from temporary issues
    - Avoids hammering a site that's already struggling
    - Increases chances of success on transient failures
    - Shows good citizenship to avoid IP blocks

    The formula: delay = min(base_delay * (2 ^ attempt), max_delay)
    - Attempt 1: 2s
    - Attempt 2: 4s
    - Attempt 3: 8s (capped at max_delay)

    Args:
        max_attempts: Maximum number of tries before giving up
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay cap to prevent excessive waits
        exceptions: Tuple of exception types to catch and retry

    Usage:
        @retry_async(max_attempts=3, exceptions=(TimeoutError, NetworkError))
        async def fetch_data():
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"[{func.__name__}] Failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate exponential backoff delay
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)

                    # Add jitter (10-20%) to prevent thundering herd
                    # If multiple scrapers fail at once, we don't want them
                    # all retrying at exactly the same moment
                    import random
                    jitter = delay * random.uniform(0.1, 0.2)
                    actual_delay = delay + jitter

                    logger.warning(
                        f"[{func.__name__}] Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {actual_delay:.1f}s..."
                    )
                    await asyncio.sleep(actual_delay)

            # Should never reach here, but satisfy type checker
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def parse_rate_string(rate_text: str) -> Optional[float]:
    """
    Parse a mortgage rate from various string formats.

    Financial sites display rates in inconsistent formats:
    - "6.5%"
    - "6.50 %"
    - "6.5% APR"
    - "Rate: 6.500%"
    - "6.5" (no percent sign)
    - "6,5%" (European format, rare but possible)

    This function handles all common variations and extracts the numeric rate.

    Args:
        rate_text: Raw rate string from the webpage

    Returns:
        Float rate value (e.g., 6.5 for "6.5%"), or None if parsing fails

    Examples:
        >>> parse_rate_string("6.5%")
        6.5
        >>> parse_rate_string("Rate: 6.500% APR")
        6.5
        >>> parse_rate_string("N/A")
        None
    """
    if not rate_text:
        return None

    # Clean up the string
    cleaned = rate_text.strip()

    # Handle European decimal format (6,5 -> 6.5)
    cleaned = cleaned.replace(",", ".")

    # Extract numeric portion using regex
    # This pattern matches:
    # - Optional leading characters (like "Rate: ")
    # - The actual number (integer or decimal)
    # - Optional trailing characters (like "% APR")
    pattern = r"(\d+\.?\d*)"
    match = re.search(pattern, cleaned)

    if not match:
        logger.debug(f"Could not parse rate from: '{rate_text}'")
        return None

    try:
        rate = float(match.group(1))

        # Sanity check: mortgage rates should be between 0 and 20
        # (historically never exceeded ~18% even in the 1980s)
        if not 0 < rate < 20:
            logger.warning(f"Parsed rate {rate} outside expected range from: '{rate_text}'")
            return None

        return rate
    except ValueError:
        logger.debug(f"ValueError parsing rate from: '{rate_text}'")
        return None


def format_rate(rate: Optional[float], decimals: int = 3) -> str:
    """
    Format a rate value for display.

    Args:
        rate: Numeric rate value or None
        decimals: Number of decimal places

    Returns:
        Formatted string like "6.500%" or "N/A" if None
    """
    if rate is None:
        return "N/A"
    return f"{rate:.{decimals}f}%"


def generate_timestamp_filename(prefix: str = "mortgage_rates", extension: str = "csv") -> str:
    """
    Generate a timestamped filename for data export.

    Format: prefix_YYYYMMDD_HHMMSS.extension

    Args:
        prefix: Filename prefix
        extension: File extension without dot

    Returns:
        Timestamped filename string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def clean_text(text: str) -> str:
    """
    Clean scraped text by removing excess whitespace and special characters.

    Web scraping often yields text with:
    - Multiple spaces from HTML formatting
    - Newlines from element structure
    - Non-breaking spaces (&nbsp;)
    - Zero-width characters

    Args:
        text: Raw scraped text

    Returns:
        Cleaned string with normalized whitespace
    """
    if not text:
        return ""

    # Replace various whitespace characters with standard space
    cleaned = re.sub(r"[\s\xa0\u200b]+", " ", text)

    # Strip leading/trailing whitespace
    return cleaned.strip()


class ScraperMetrics:
    """
    Simple metrics collector for monitoring scraper performance.

    Tracks:
    - Success/failure counts per source
    - Response times
    - Retry attempts

    Useful for identifying problematic sources and optimizing performance.
    """

    def __init__(self):
        self.results: dict[str, dict] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def start(self):
        """Mark the start of a scraping session."""
        self.start_time = datetime.now()

    def end(self):
        """Mark the end of a scraping session."""
        self.end_time = datetime.now()

    def record_success(self, source: str, duration_ms: float):
        """Record a successful scrape."""
        self.results[source] = {
            "status": "success",
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        }

    def record_failure(self, source: str, error: str, duration_ms: float):
        """Record a failed scrape."""
        self.results[source] = {
            "status": "failure",
            "error": error,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        }

    @property
    def total_duration_seconds(self) -> float:
        """Total session duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_count(self) -> int:
        """Number of successful scrapes."""
        return sum(1 for r in self.results.values() if r["status"] == "success")

    @property
    def failure_count(self) -> int:
        """Number of failed scrapes."""
        return sum(1 for r in self.results.values() if r["status"] == "failure")
