// API Proxy Server - Securely handles external API calls
// This server keeps API keys server-side and provides safe endpoints for the frontend

const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
require('dotenv').config({ path: './server/.env' });

const app = express();
const PORT = process.env.PORT || 3001;

// ============================================
// MIDDLEWARE
// ============================================

// Rate limiting: 10 requests per minute per IP
const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again later.' }
});

// CORS - allow frontend origin
app.use(cors({
  origin: process.env.ALLOWED_ORIGIN || 'http://localhost:3000',
  credentials: true
}));

app.use(express.json());
app.use(limiter);

// ============================================
// STATIC FALLBACK DATA
// ============================================

// Base state sales tax rates (used when TaxJar unavailable)
const STATE_BASE_SALES_TAX = {
  AL: 0.04, AK: 0.0,  AZ: 0.056, AR: 0.065, CA: 0.0725,
  CO: 0.029, CT: 0.0635, DE: 0.0,  FL: 0.06,  GA: 0.04,
  HI: 0.04,  ID: 0.06,  IL: 0.0625, IN: 0.07,  IA: 0.06,
  KS: 0.065, KY: 0.06,  LA: 0.0445, ME: 0.055, MD: 0.06,
  MA: 0.0625, MI: 0.06,  MN: 0.06875, MS: 0.07, MO: 0.04225,
  MT: 0.0,  NE: 0.055, NV: 0.0685, NH: 0.0,  NJ: 0.06625,
  NM: 0.05125, NY: 0.04,  NC: 0.0475, ND: 0.05,  OH: 0.0575,
  OK: 0.045, OR: 0.0,  PA: 0.06,  RI: 0.07,  SC: 0.06,
  SD: 0.045, TN: 0.07,  TX: 0.0625, UT: 0.0485, VT: 0.06,
  VA: 0.043, WA: 0.065, WV: 0.06,  WI: 0.05,  WY: 0.04,
  DC: 0.06
};

const FALLBACK_MORTGAGE_RATES = [
  { term: '30-year fixed', rate: 6.89, asOf: 'Sample data', source: 'Sample data' },
  { term: '15-year fixed', rate: 6.12, asOf: 'Sample data', source: 'Sample data' },
  { term: '5/1 ARM', rate: 5.95, asOf: 'Sample data', source: 'Sample data' }
];

// ============================================
// API ENDPOINTS
// ============================================

/**
 * GET /api/tax-rate/:stateCode
 * Returns sales tax rate for the given state
 * Proxies to TaxJar if configured, falls back to static data
 */
app.get('/api/tax-rate/:stateCode', async (req, res) => {
  const { stateCode } = req.params;
  const code = stateCode.toUpperCase();

  // Input validation
  if (!/^[A-Z]{2}$/.test(code)) {
    return res.status(400).json({
      error: 'Invalid state code. Must be 2-letter state abbreviation.'
    });
  }

  // Try TaxJar API if configured
  if (process.env.TAX_API_PROVIDER === 'taxjar' && process.env.TAXJAR_API_KEY) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

      const response = await fetch(
        `https://api.taxjar.com/v2/rates/00000?country=US&state=${code}`,
        {
          headers: {
            Authorization: `Bearer ${process.env.TAXJAR_API_KEY}`,
            'Content-Type': 'application/json'
          },
          signal: controller.signal
        }
      );

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        const rate = Number(data?.rate?.state_rate ?? data?.rate?.combined_rate ?? 0);

        console.log(`[TaxJar] Fetched rate for ${code}: ${rate}`);

        return res.json({
          rate,
          source: 'taxjar',
          updatedAt: new Date().toISOString()
        });
      } else {
        console.warn(`[TaxJar] API returned ${response.status}, falling back to static`);
      }
    } catch (error) {
      console.error('[TaxJar] API Error:', error.message);
      // Fall through to static fallback
    }
  }

  // Static fallback
  const rate = STATE_BASE_SALES_TAX[code] ?? 0;
  console.log(`[Static] Returning tax rate for ${code}: ${rate}`);

  res.json({
    rate,
    source: 'static',
    updatedAt: new Date().toISOString()
  });
});

/**
 * GET /api/mortgage-rates
 * Returns current mortgage rates from FRED API
 * Falls back to sample data if API unavailable
 */
app.get('/api/mortgage-rates', async (req, res) => {
  // Return fallback if no API key configured
  if (!process.env.FRED_API_KEY) {
    console.log('[FRED] No API key, returning fallback rates');
    return res.json(FALLBACK_MORTGAGE_RATES);
  }

  try {
    const SERIES = [
      { id: 'MORTGAGE30US', label: '30-year fixed' },
      { id: 'MORTGAGE15US', label: '15-year fixed' },
      { id: 'MORTGAGE5US', label: '5/1 ARM' }
    ];

    // Fetch all series in parallel
    const results = await Promise.all(
      SERIES.map(async (series) => {
        const params = new URLSearchParams({
          series_id: series.id,
          sort_order: 'desc',
          limit: '5',
          api_key: process.env.FRED_API_KEY,
          file_type: 'json'
        });

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

        const response = await fetch(
          `https://api.stlouisfed.org/fred/series/observations?${params.toString()}`,
          { signal: controller.signal }
        );

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`FRED API returned ${response.status} for ${series.id}`);
        }

        const data = await response.json();

        // Find first valid observation
        const observation = data.observations?.find(entry => {
          if (!entry.value || entry.value === '.') return false;
          const parsed = Number.parseFloat(entry.value);
          return Number.isFinite(parsed);
        });

        if (!observation) {
          throw new Error(`No valid observations for ${series.id}`);
        }

        const rate = Number.parseFloat(observation.value);

        return {
          term: series.label,
          rate: Number(rate.toFixed(3)),
          asOf: observation.date,
          source: 'Federal Reserve Economic Data (FRED)'
        };
      })
    );

    console.log(`[FRED] Successfully fetched ${results.length} mortgage rates`);
    res.json(results);

  } catch (error) {
    console.error('[FRED] API Error:', error.message);
    console.log('[FRED] Returning fallback rates due to error');
    res.json(FALLBACK_MORTGAGE_RATES);
  }
});

/**
 * GET /health
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    config: {
      taxProvider: process.env.TAX_API_PROVIDER || 'static',
      fredEnabled: !!process.env.FRED_API_KEY
    }
  });
});

// ============================================
// START SERVER
// ============================================

app.listen(PORT, () => {
  console.log('='.repeat(50));
  console.log(`API Proxy Server running on http://localhost:${PORT}`);
  console.log('='.repeat(50));
  console.log(`Tax API Provider: ${process.env.TAX_API_PROVIDER || 'static'}`);
  console.log(`FRED API: ${process.env.FRED_API_KEY ? '✓ Enabled' : '✗ Disabled (using fallback)'}`);
  console.log(`TaxJar API: ${process.env.TAXJAR_API_KEY ? '✓ Enabled' : '✗ Disabled (using static)'}`);
  console.log(`Allowed Origin: ${process.env.ALLOWED_ORIGIN || 'http://localhost:3000'}`);
  console.log('='.repeat(50));
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  app.close(() => {
    console.log('HTTP server closed');
  });
});
