// Lightweight tax service with API-ready hooks and static fallback
// Usage: import { getStateSalesTax } from './services/taxService'
// Returns rate as a decimal (e.g., 0.065 for 6.5%)

const PROVIDER = import.meta.env.VITE_TAX_API_PROVIDER || 'static';
const TAXJAR_API_KEY = import.meta.env.VITE_TAXJAR_API_KEY;

// Basic base state sales tax rates (approximate; local taxes not included)
// Source note: For production use, replace with a provider like TaxJar or Avalara.
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

const STATE_NAMES = [
  { code: 'AL', name: 'Alabama' },
  { code: 'AK', name: 'Alaska' },
  { code: 'AZ', name: 'Arizona' },
  { code: 'AR', name: 'Arkansas' },
  { code: 'CA', name: 'California' },
  { code: 'CO', name: 'Colorado' },
  { code: 'CT', name: 'Connecticut' },
  { code: 'DE', name: 'Delaware' },
  { code: 'FL', name: 'Florida' },
  { code: 'GA', name: 'Georgia' },
  { code: 'HI', name: 'Hawaii' },
  { code: 'ID', name: 'Idaho' },
  { code: 'IL', name: 'Illinois' },
  { code: 'IN', name: 'Indiana' },
  { code: 'IA', name: 'Iowa' },
  { code: 'KS', name: 'Kansas' },
  { code: 'KY', name: 'Kentucky' },
  { code: 'LA', name: 'Louisiana' },
  { code: 'ME', name: 'Maine' },
  { code: 'MD', name: 'Maryland' },
  { code: 'MA', name: 'Massachusetts' },
  { code: 'MI', name: 'Michigan' },
  { code: 'MN', name: 'Minnesota' },
  { code: 'MS', name: 'Mississippi' },
  { code: 'MO', name: 'Missouri' },
  { code: 'MT', name: 'Montana' },
  { code: 'NE', name: 'Nebraska' },
  { code: 'NV', name: 'Nevada' },
  { code: 'NH', name: 'New Hampshire' },
  { code: 'NJ', name: 'New Jersey' },
  { code: 'NM', name: 'New Mexico' },
  { code: 'NY', name: 'New York' },
  { code: 'NC', name: 'North Carolina' },
  { code: 'ND', name: 'North Dakota' },
  { code: 'OH', name: 'Ohio' },
  { code: 'OK', name: 'Oklahoma' },
  { code: 'OR', name: 'Oregon' },
  { code: 'PA', name: 'Pennsylvania' },
  { code: 'RI', name: 'Rhode Island' },
  { code: 'SC', name: 'South Carolina' },
  { code: 'SD', name: 'South Dakota' },
  { code: 'TN', name: 'Tennessee' },
  { code: 'TX', name: 'Texas' },
  { code: 'UT', name: 'Utah' },
  { code: 'VT', name: 'Vermont' },
  { code: 'VA', name: 'Virginia' },
  { code: 'WA', name: 'Washington' },
  { code: 'WV', name: 'West Virginia' },
  { code: 'WI', name: 'Wisconsin' },
  { code: 'WY', name: 'Wyoming' },
  { code: 'DC', name: 'District of Columbia' }
];

export function listStates() {
  return STATE_NAMES;
}

export async function getStateSalesTax(stateCode) {
  const code = (stateCode || '').toUpperCase();
  if (!code) {
    return { rate: 0, source: 'none', updatedAt: new Date().toISOString() };
  }

  // Provider hook (not executed without proper env/config)
  if (PROVIDER === 'taxjar' && TAXJAR_API_KEY) {
    // Example TaxJar-like flow (placeholder; adjust per provider docs):
    // Note: State-level base rates are typically static; city/county rates vary by ZIP.
    try {
      const res = await fetch(`https://api.taxjar.com/v2/rates/00000?country=US&state=${code}`, {
        headers: {
          Authorization: `Bearer ${TAXJAR_API_KEY}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        // TaxJar returns rates in decimal format (0.065 for 6.5%)
        // Specify format explicitly since we know TaxJar uses decimals
        const rate = Number(data?.rate?.state_rate ?? data?.rate?.combined_rate ?? 0);
        return { rate, source: 'taxjar', updatedAt: new Date().toISOString() };
      }
    } catch (_) {
      // fall through to static
    }
  }

  // Static fallback
  const rate = STATE_BASE_SALES_TAX[code] ?? 0;
  return { rate, source: 'static', updatedAt: new Date().toISOString() };
}

