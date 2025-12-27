import { describe, it, expect } from 'vitest';
import { computeLoanDetails, normalizeTaxRate } from '../../src/utils/loanProcessor.js';

describe('normalizeTaxRate', () => {
  it('handles decimal input', () => {
    expect(normalizeTaxRate(0.07)).toBe(0.07);
  });

  it('converts percentage input', () => {
    expect(normalizeTaxRate(7)).toBeCloseTo(0.07, 4);
  });

  it('guards against invalid values', () => {
    expect(normalizeTaxRate(null)).toBe(0);
    expect(normalizeTaxRate(-1)).toBe(0);
  });
});

describe('computeLoanDetails', () => {
  const baseLoan = {
    principal: 200000,
    annualRate: 5,
    years: 30,
    stateCode: '',
    includeSalesTax: false
  };

  it('returns expected structure without tax', async () => {
    const result = await computeLoanDetails(baseLoan, () => Promise.resolve({ rate: 0 }));
    expect(result.loanInfo.financedPrincipal).toBeCloseTo(200000, 2);
    expect(result.results.monthlyPayment).toBeCloseTo(1073.64, 2);
    expect(result.schedule).toHaveLength(360);
  });

  it('adds tax when requested', async () => {
    const result = await computeLoanDetails(
      { ...baseLoan, includeSalesTax: true, stateCode: 'WA' },
      () => Promise.resolve({ rate: 0.065 })
    );

    expect(result.loanInfo.taxAmount).toBeCloseTo(13000, 2);
    expect(result.loanInfo.financedPrincipal).toBeCloseTo(213000, 2);
    expect(result.results.monthlyPayment).toBeGreaterThan(1073.64);
  });

  it('normalizes percent-based provider rates', async () => {
    const result = await computeLoanDetails(
      { ...baseLoan, includeSalesTax: true, stateCode: 'TX' },
      () => Promise.resolve({ rate: 6.25 })
    );

    expect(result.loanInfo.taxRate).toBeCloseTo(0.0625, 4);
  });

  it('falls back when tax lookup fails', async () => {
    const failingLookup = () => Promise.reject(new Error('fail'));
    const result = await computeLoanDetails(
      { ...baseLoan, includeSalesTax: true, stateCode: 'CA' },
      failingLookup
    );

    expect(result.loanInfo.taxAmount).toBe(0);
    expect(result.loanInfo.financedPrincipal).toBe(baseLoan.principal);
  });
});

describe('computeLoanDetails - PMI integration', () => {
  const baseLoan = {
    principal: 450000,
    propertyValue: 500000,
    annualRate: 6,
    years: 30,
    stateCode: '',
    includeSalesTax: false,
    pmiRate: 0.008, // 0.8% as decimal
    monthlyInsurance: 150
  };

  it('includes PMI when LTV > 80%', async () => {
    const result = await computeLoanDetails(baseLoan);

    // Verify LTV calculation
    expect(result.loanInfo.ltv).toBeCloseTo(0.90, 2);
    expect(result.loanInfo.pmiRequired).toBe(true);

    // Verify PMI is calculated
    expect(result.results.monthlyPMI).toBeGreaterThan(0);
    expect(result.results.monthlyPMI).toBeCloseTo(300, 2); // (450000 * 0.008) / 12

    // Verify PMI drop-off is calculated
    expect(result.results.pmiDropOffMonth).toBeGreaterThan(0);
    expect(result.results.totalPMIPaid).toBeGreaterThan(0);
  });

  it('excludes PMI when LTV <= 80%', async () => {
    const result = await computeLoanDetails({
      ...baseLoan,
      principal: 400000,
      propertyValue: 500000
    });

    // Verify LTV calculation
    expect(result.loanInfo.ltv).toBeCloseTo(0.80, 2);
    expect(result.loanInfo.pmiRequired).toBe(false);

    // Verify no PMI
    expect(result.results.monthlyPMI).toBe(0);
    expect(result.results.pmiDropOffMonth).toBeNull();
    expect(result.results.totalPMIPaid).toBe(0);
  });

  it('includes monthly insurance in total payment', async () => {
    const result = await computeLoanDetails(baseLoan);

    const expectedTotal = result.results.monthlyPayment + result.results.monthlyPMI + result.results.monthlyInsurance;
    expect(result.results.totalMonthlyPayment).toBeCloseTo(expectedTotal, 2);

    // Verify insurance is included
    expect(result.results.monthlyInsurance).toBe(150);
  });

  it('calculates down payment correctly', async () => {
    const result = await computeLoanDetails(baseLoan);

    expect(result.loanInfo.downPayment).toBe(50000); // 500k - 450k
    expect(result.loanInfo.propertyValue).toBe(500000);
  });

  it('handles property value defaulting to principal', async () => {
    const result = await computeLoanDetails({
      principal: 400000,
      annualRate: 6,
      years: 30
    });

    // When propertyValue is not provided, it should default to principal
    expect(result.loanInfo.propertyValue).toBe(400000);
    expect(result.loanInfo.ltv).toBe(1);
    expect(result.loanInfo.downPayment).toBe(0);
    expect(result.loanInfo.pmiRequired).toBe(true); // LTV > 80%
  });

  it('handles zero PMI rate', async () => {
    const result = await computeLoanDetails({
      ...baseLoan,
      pmiRate: 0
    });

    expect(result.loanInfo.pmiRequired).toBe(true); // LTV still > 80%
    expect(result.results.monthlyPMI).toBe(0); // But PMI is 0 due to 0% rate
  });

  it('handles zero monthly insurance', async () => {
    const result = await computeLoanDetails({
      ...baseLoan,
      monthlyInsurance: 0
    });

    expect(result.results.monthlyInsurance).toBe(0);
    const expectedTotal = result.results.monthlyPayment + result.results.monthlyPMI;
    expect(result.results.totalMonthlyPayment).toBeCloseTo(expectedTotal, 2);
  });

  it('properly calculates PMI drop-off month', async () => {
    const result = await computeLoanDetails(baseLoan);

    const dropOffMonth = result.results.pmiDropOffMonth;
    expect(dropOffMonth).toBeGreaterThan(0);
    expect(dropOffMonth).toBeLessThan(result.schedule.length);

    // Verify the balance at drop-off is at or below 78% of property value
    const dropOffPayment = result.schedule[dropOffMonth - 1];
    const targetBalance = result.loanInfo.propertyValue * 0.78;
    expect(dropOffPayment.remainingBalance).toBeLessThanOrEqual(targetBalance);
  });
});
