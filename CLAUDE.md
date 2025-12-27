# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev      # Start dev server at http://localhost:3000
npm run build    # Production build to dist/
npm run preview  # Preview production build
npm test         # Run all tests (Vitest)
npm run server   # Start API proxy server at http://localhost:3001
```

Run a single test file:
```bash
npx vitest run tests/unit/calculator.spec.js
```

For development with live FRED mortgage rates, run both servers:
```bash
npm run dev:all  # Runs both frontend (3000) and API proxy (3001) concurrently
```

## Architecture

Vue 3 + Vite amortization calculator with optional external API integrations.

### Core Flow

`App.vue` orchestrates everything:
1. `LoanInputForm` collects loan parameters (principal, property value, rate, term, PMI rate, insurance) and emits `calculate` event
2. `computeLoanDetails()` in `loanProcessor.js` handles calculation pipeline:
   - Calculates LTV (Loan-to-Value) ratio from principal and property value
   - Determines if PMI is required (LTV > 80%)
   - Optionally fetches sales tax via `taxService.js` (calls API proxy) and adds to principal
   - Delegates math to pure functions in `calculator.js`
   - Calculates PMI drop-off point (when balance reaches 78% of property value)
   - Returns `{ loanInfo, results, schedule }` with complete payment breakdown
3. `LoanSummary` and `AmortizationTable` render the results with PMI/insurance columns
4. `MortgageRatesPanel` displays live/cached mortgage rates (30yr, 15yr, ARM) from FRED via API proxy

### Key Modules

- **`src/utils/calculator.js`** - Pure calculation functions (monthly payment, amortization schedule, LTV, PMI calculations, PMI drop-off detection, input validation)
- **`src/utils/loanProcessor.js`** - Orchestration layer that combines calculator functions with tax lookup; `normalizeTaxRate()` handles provider differences (decimal vs percentage)
- **`src/utils/sanitize.js`** - Input sanitization to prevent XSS/injection attacks; validates ranges for all numeric inputs
- **`src/services/taxService.js`** - State sales tax lookup; calls API proxy for live data, falls back to static rates
- **`src/services/mortgageRateService.js`** - Fetches 30yr/15yr/ARM rates; calls API proxy for FRED data
- **`server/api-proxy.js`** - Express server that securely proxies external API calls (FRED, TaxJar), keeps API keys server-side, includes rate limiting (10 req/min)

### Environment Variables

**Backend API Proxy** (`server/.env`):
- `FRED_API_KEY` - FRED API key for live mortgage rates (required for real data)
- `TAXJAR_API_KEY` - TaxJar API key (optional, uses static fallback if not set)
- `PORT` - API proxy port (default: 3001)
- `ALLOWED_ORIGIN` - CORS allowed origin (default: http://localhost:3000)

**Frontend** (`.env` - not currently used):
- All external API calls now go through the backend proxy for security
- Frontend uses `VITE_API_PROXY_URL` (defaults to http://localhost:3001)

## Testing

Tests use Vitest with jsdom environment. Test structure mirrors source:
- `tests/unit/` - Unit tests for utils and components
- `tests/integration/` - Full app integration tests

Component tests use `@vue/test-utils`. Calculator tests verify numerical accuracy with `toBeCloseTo()`.