# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev      # Start dev server at http://localhost:3000
npm run build    # Production build to dist/
npm run preview  # Preview production build
npm test         # Run all tests (Vitest)
```

Run a single test file:
```bash
npx vitest run tests/unit/calculator.spec.js
```

## Architecture

Vue 3 + Vite amortization calculator with optional external API integrations.

### Core Flow

`App.vue` orchestrates everything:
1. `LoanInputForm` collects loan parameters and emits `calculate` event
2. `computeLoanDetails()` in `loanProcessor.js` handles calculation pipeline:
   - Optionally fetches sales tax via `taxService.js` and adds to principal
   - Delegates math to pure functions in `calculator.js`
   - Returns `{ loanInfo, results, schedule }`
3. `LoanSummary` and `AmortizationTable` render the results
4. `MortgageRatesPanel` displays live/cached mortgage rates (30yr, 15yr, ARM)

### Key Modules

- **`src/utils/calculator.js`** - Pure calculation functions (monthly payment, amortization schedule generation, input validation)
- **`src/utils/loanProcessor.js`** - Orchestration layer that combines calculator functions with tax lookup; `normalizeTaxRate()` handles provider differences (decimal vs percentage)
- **`src/services/taxService.js`** - State sales tax lookup with static fallback; supports TaxJar provider via env vars
- **`src/services/mortgageRateService.js`** - Fetches 30yr/15yr/ARM rates from FRED API; falls back to sample data without API key

### Environment Variables

All optional (app works with static fallbacks):
- `VITE_FRED_API_KEY` - FRED API key for live mortgage rates
- `VITE_TAX_API_PROVIDER` - Set to `taxjar` to enable TaxJar
- `VITE_TAXJAR_API_KEY` - TaxJar API key

## Testing

Tests use Vitest with jsdom environment. Test structure mirrors source:
- `tests/unit/` - Unit tests for utils and components
- `tests/integration/` - Full app integration tests

Component tests use `@vue/test-utils`. Calculator tests verify numerical accuracy with `toBeCloseTo()`.

## Scraper CLI (Python)

Separate Python CLI tool in `scraper/` for scraping live mortgage rates from financial websites.

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium

python -m scraper scrape                    # Scrape all sources
python -m scraper scrape -s bankrate        # Specific source
python -m scraper scrape --zip 10001        # Custom ZIP code
python -m scraper list-sources              # List available sources
```

### Scraper Architecture

- **`scrapers/base.py`** - Abstract `MortgageScraper` class defining the scraping contract
- **`scrapers/*.py`** - Site-specific implementations (Bankrate, NerdWallet, Wells Fargo, Chase, Zillow)
- **`utils/stealth.py`** - Anti-detection: UA rotation, viewport randomization, humanized delays
- **`utils/helpers.py`** - Retry logic with exponential backoff, rate parsing utilities
- **`cli.py`** - Typer CLI with rich terminal output and CSV export

Scrapers run concurrently via `asyncio.gather()`. Each scraper manages its own Playwright browser instance with stealth configuration.
- to memorize