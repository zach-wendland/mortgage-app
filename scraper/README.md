# Mortgage Rate Scraper CLI

An asynchronous command-line tool for scraping current mortgage rates from multiple financial sources using Python and Playwright.

## Features

- **Multi-source scraping**: Bankrate, NerdWallet, Wells Fargo, Chase, Zillow
- **Parallel execution**: All sources scraped concurrently for speed
- **Anti-detection measures**: User-agent rotation, humanized delays, viewport randomization
- **Resilient**: Retry logic, graceful error handling, continues on individual failures
- **Beautiful output**: Rich terminal tables with color-coded status
- **Data export**: Timestamped CSV files with pandas

## Installation

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
# Scrape all sources
python -m scraper scrape

# Scrape specific sources
python -m scraper scrape -s bankrate -s chase

# Use custom ZIP code
python -m scraper scrape --zip 10001

# Show browser windows (for debugging)
python -m scraper scrape --no-headless -v

# List available sources
python -m scraper list-sources

# Show help
python -m scraper --help
```

## Configuration

Create a `.env` file (see `.env.example`):

```env
MORTGAGE_SCRAPER_ZIP=90210
```

## Architecture

```
scraper/
├── __init__.py          # Package exports
├── __main__.py          # Entry point for python -m
├── cli.py               # Typer CLI with rich output
├── scrapers/
│   ├── base.py          # Abstract MortgageScraper class
│   ├── bankrate.py      # Bankrate.com scraper
│   ├── nerdwallet.py    # NerdWallet.com scraper
│   ├── wellsfargo.py    # WellsFargo.com scraper
│   ├── chase.py         # Chase.com scraper
│   └── zillow.py        # Zillow.com scraper
└── utils/
    ├── stealth.py       # Anti-detection utilities
    └── helpers.py       # Retry logic, parsing helpers
```

## Anti-Detection Measures

The scraper implements several stealth techniques:

1. **User-Agent Rotation**: Dynamic generation via `fake-useragent`
2. **Viewport Randomization**: Varies window size per session
3. **Humanized Delays**: Random jitter between actions (2-5s)
4. **Mouse Simulation**: Bezier-curve mouse movements
5. **Popup Handling**: Auto-dismisses cookie banners and modals
6. **WebDriver Masking**: Removes automation indicators

## Output

Results are displayed in a formatted terminal table and saved to CSV:

```
mortgage_rates_20241201_143022.csv
```

Columns: source, 30_year_fixed, 15_year_fixed, 5_1_arm, scraped_at, duration_ms, error

## Notes

- Financial sites may block or rate-limit scrapers
- Selectors may need updates as sites change
- Use responsibly and respect robots.txt
