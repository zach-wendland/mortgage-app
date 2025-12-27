import { afterEach, describe, expect, it, vi } from 'vitest';

const loadService = () => import('../../src/services/taxService.js');

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe('taxService', () => {
  it('returns list of state metadata', async () => {
    const { listStates } = await loadService();
    const states = listStates();
    expect(states.length).toBeGreaterThan(40);
    expect(states.find((s) => s.code === 'CA')?.name).toBe('California');
  });

  it('returns static rate for known state', async () => {
    const { getStateSalesTax } = await loadService();
    const result = await getStateSalesTax('CA');
    expect(result.rate).toBeCloseTo(0.0725, 4);
    expect(result.source).toBe('static');
  });

  it('defaults to zero for unknown state', async () => {
    const { getStateSalesTax } = await loadService();
    const result = await getStateSalesTax('ZZ');
    expect(result.rate).toBe(0);
  });

  it('uses proxy when available', async () => {
    // Mock the API proxy response (simulating what the backend returns)
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        rate: 0.07,
        source: 'taxjar',
        updatedAt: '2025-01-01T00:00:00Z'
      })
    });
    vi.stubGlobal('fetch', fetchMock);

    const { getStateSalesTax } = await loadService();
    const result = await getStateSalesTax('TX');

    // Verify it called the proxy endpoint
    expect(fetchMock).toHaveBeenCalled();
    const callUrl = fetchMock.mock.calls[0][0];
    expect(callUrl).toContain('/api/tax-rate/TX');

    expect(result.rate).toBeCloseTo(0.07, 4);
    expect(result.source).toBe('taxjar');
  });
});

