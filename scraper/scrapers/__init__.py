# Scrapers package for mortgage rate extraction
from .base import MortgageScraper, MortgageRates
from .bankrate import BankrateScraper
from .nerdwallet import NerdWalletScraper
from .wellsfargo import WellsFargoScraper
from .chase import ChaseScraper
from .zillow import ZillowScraper

__all__ = [
    "MortgageScraper",
    "MortgageRates",
    "BankrateScraper",
    "NerdWalletScraper",
    "WellsFargoScraper",
    "ChaseScraper",
    "ZillowScraper",
]

# Registry of all available scrapers for easy iteration
SCRAPER_REGISTRY: dict[str, type[MortgageScraper]] = {
    "bankrate": BankrateScraper,
    "nerdwallet": NerdWalletScraper,
    "wellsfargo": WellsFargoScraper,
    "chase": ChaseScraper,
    "zillow": ZillowScraper,
}


def get_all_scrapers() -> list[type[MortgageScraper]]:
    """Return list of all scraper classes."""
    return list(SCRAPER_REGISTRY.values())


def get_scraper_by_name(name: str) -> type[MortgageScraper]:
    """Get a specific scraper class by name."""
    name_lower = name.lower()
    if name_lower not in SCRAPER_REGISTRY:
        raise ValueError(f"Unknown scraper: {name}. Available: {list(SCRAPER_REGISTRY.keys())}")
    return SCRAPER_REGISTRY[name_lower]
