// API Proxy URL - calls backend proxy instead of exposing API keys client-side
const API_PROXY_URL = import.meta.env.VITE_API_PROXY_URL || 'http://localhost:3001';

const FALLBACK_RATES = [
  { term: '30-year fixed', rate: 6.89, asOf: 'Sample data', source: 'Sample data' },
  { term: '15-year fixed', rate: 6.12, asOf: 'Sample data', source: 'Sample data' },
  { term: '5/1 ARM', rate: 5.95, asOf: 'Sample data', source: 'Sample data' }
];

export async function getMortgageRates(options = {}) {
  // Call API proxy instead of directly calling FRED API
  // The proxy securely handles API keys server-side
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000); // 8s timeout (3 series to fetch)

    const res = await fetch(`${API_PROXY_URL}/api/mortgage-rates`, {
      signal: options.signal || controller.signal
    });

    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      // Proxy returns array of { term, rate, asOf, source }
      return data;
    }
  } catch (error) {
    console.warn('[mortgageRateService] Proxy unavailable, using fallback rates:', error.message);
    // Fall through to fallback
  }

  // Fallback (used when proxy is down or returns error)
  return FALLBACK_RATES;
}
