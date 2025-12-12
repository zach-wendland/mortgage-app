"""
Entry point for running the scraper as a module.

Usage:
    python -m scraper scrape
    python -m scraper list-sources
    python -m scraper --help

This allows the package to be executed directly with `python -m scraper`.
"""

from cli import main

if __name__ == "__main__":
    main()
