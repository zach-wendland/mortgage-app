"""
Mortgage Rate Scraper

An async CLI tool for scraping current mortgage rates from multiple
financial sources using Playwright browser automation.

Main components:
- scrapers/: Site-specific scraper implementations
- utils/: Stealth and helper utilities
- cli.py: Command-line interface

Usage:
    python -m scraper scrape              # Scrape all sources
    python -m scraper list-sources        # List available sources
    python -m scraper --help              # Show help
"""

__version__ = "1.0.0"
__author__ = "Mortgage App"

from .scrapers import (
    MortgageScraper,
    MortgageRates,
    BankrateScraper,
    NerdWalletScraper,
    WellsFargoScraper,
    ChaseScraper,
    ZillowScraper,
    SCRAPER_REGISTRY,
)

__all__ = [
    "MortgageScraper",
    "MortgageRates",
    "BankrateScraper",
    "NerdWalletScraper",
    "WellsFargoScraper",
    "ChaseScraper",
    "ZillowScraper",
    "SCRAPER_REGISTRY",
]
