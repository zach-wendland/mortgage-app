// Global test setup
import { vi } from 'vitest';

// Mock requestAnimationFrame for synchronous animations in tests
global.requestAnimationFrame = (cb) => {
  setTimeout(cb, 0);
  return 0;
};

global.cancelAnimationFrame = () => {};

// Mock performance.now() for consistent timing
global.performance = {
  now: () => Date.now()
};

// Mock fetch for API proxy calls
global.fetch = vi.fn((url) => {
  // Mock tax service proxy responses
  if (url.includes('/api/tax-rate/')) {
    const stateCode = url.split('/').pop();
    const staticRates = {
      'CA': 0.0725,
      'WA': 0.065,
      'TX': 0.0625
    };
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        rate: staticRates[stateCode] || 0,
        source: 'static',
        updatedAt: new Date().toISOString()
      })
    });
  }

  // Mock mortgage rates proxy responses
  if (url.includes('/api/mortgage-rates')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve([
        { term: '30-year fixed', rate: 6.89, asOf: 'Sample data', source: 'Sample data' },
        { term: '15-year fixed', rate: 6.12, asOf: 'Sample data', source: 'Sample data' },
        { term: '5/1 ARM', rate: 5.95, asOf: 'Sample data', source: 'Sample data' }
      ])
    });
  }

  // Default fallback for any other fetch calls
  return Promise.reject(new Error(`Unmocked fetch call to: ${url}`));
});
