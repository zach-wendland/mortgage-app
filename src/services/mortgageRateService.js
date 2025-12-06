const SERIES = [
  { id: 'MORTGAGE30US', label: '30-year fixed' },
  { id: 'MORTGAGE15US', label: '15-year fixed' },
  { id: 'MORTGAGE5US', label: '5/1 ARM' }
];

const FALLBACK_RATES = [
  { term: '30-year fixed', rate: 6.89, asOf: 'Sample data', source: 'Sample data' },
  { term: '15-year fixed', rate: 6.12, asOf: 'Sample data', source: 'Sample data' },
  { term: '5/1 ARM', rate: 5.95, asOf: 'Sample data', source: 'Sample data' }
];

const BASE_URL = 'https://api.stlouisfed.org/fred/series/observations';
const API_KEY = import.meta.env.VITE_FRED_API_KEY;

async function fetchLatestRate(seriesId, signal) {
  const params = new URLSearchParams({
    series_id: seriesId,
    sort_order: 'desc',
    limit: '5',
    api_key: API_KEY,
    file_type: 'json'
  });

  const response = await fetch(`${BASE_URL}?${params.toString()}`, { signal });
  if (!response.ok) {
    throw new Error(`Unable to reach mortgage rate service (${response.status})`);
  }

  const data = await response.json();

  // Filter for valid observations
  const observation = data.observations?.find((entry) => {
    // Must have a value
    if (!entry.value || entry.value === '.') return false;

    // Value must parse to a valid finite number
    const parsed = Number.parseFloat(entry.value);
    return Number.isFinite(parsed);
  });

  if (!observation) {
    throw new Error('Mortgage rate data is temporarily unavailable.');
  }

  // At this point, we know the value is valid
  const parsedRate = Number.parseFloat(observation.value);

  // Extra safety check (belt and suspenders)
  if (!Number.isFinite(parsedRate)) {
    throw new Error('Invalid mortgage rate data received from API.');
  }

  return {
    rate: parsedRate,
    asOf: observation.date
  };
}

export async function getMortgageRates(options = {}) {
  if (!API_KEY) {
    return FALLBACK_RATES;
  }

  try {
    const { signal } = options;
    const results = await Promise.all(
      SERIES.map(async (series) => {
        const latest = await fetchLatestRate(series.id, signal);
        return {
          term: series.label,
          rate: Number(latest.rate.toFixed(3)),
          asOf: latest.asOf,
          source: 'Federal Reserve Economic Data (FRED)'
        };
      })
    );

    return results;
  } catch (error) {
    console.error('[mortgageRateService]', error);
    return FALLBACK_RATES;
  }
}
