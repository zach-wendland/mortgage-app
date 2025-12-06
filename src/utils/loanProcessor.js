import {
  calculateMonthlyPayment,
  calculateTotalPaid,
  calculateTotalInterest,
  generateAmortizationSchedule
} from './calculator.js';
import { getStateSalesTax } from '../services/taxService.js';

/**
 * Normalizes a tax rate from various provider formats to decimal form.
 *
 * @param {number|string} rawRate - The tax rate from the provider
 * @param {string} format - 'decimal', 'percent', or 'auto' (default)
 * @returns {number} - Tax rate as decimal (0.065 for 6.5%)
 *
 * Examples:
 *   normalizeTaxRate(6.5, 'percent')  -> 0.065
 *   normalizeTaxRate(0.065, 'decimal') -> 0.065
 *   normalizeTaxRate(6.5, 'auto')     -> 0.065 (auto-detected as percent)
 *   normalizeTaxRate(0.5, 'auto')     -> 0.5   (auto-detected as decimal - edge case!)
 */
export function normalizeTaxRate(rawRate, format = 'auto') {
  const rateNum = Number(rawRate);

  // Validate input
  if (!Number.isFinite(rateNum) || rateNum <= 0) {
    return 0;
  }

  // Explicit format when known from provider
  if (format === 'decimal') {
    return rateNum;
  }

  if (format === 'percent') {
    return rateNum / 100;
  }

  // Auto-detection with safer threshold
  // Real US sales tax rates rarely exceed 12%, never exceed 20%
  // If value > 1, clearly a percentage (e.g., 6.5 means 6.5%, not 650%)
  // If value ≤ 1, treat as decimal (e.g., 0.065 = 6.5%, 0.5 = 50%)
  //
  // This handles:
  //   6.5 -> 0.065 ✅ (clearly percentage)
  //   0.065 -> 0.065 ✅ (clearly decimal)
  //   0.5 -> 0.5 ⚠️  (treated as 50% decimal, ambiguous but safer than 0.5%)
  //
  // Edge case: If an API returns 0.5 meaning "0.5% tax", use explicit 'percent' format
  // to convert correctly: normalizeTaxRate(0.5, 'percent') -> 0.005
  return rateNum > 1 ? rateNum / 100 : rateNum;
}

export async function computeLoanDetails(loanData, taxLookup = getStateSalesTax) {
  const principal = Number(loanData.principal);
  const annualRate = Number(loanData.annualRate);
  const years = Number(loanData.years);
  const stateCode = loanData.stateCode || '';
  const includeSalesTax = !!loanData.includeSalesTax;

  let taxRate = 0;
  let taxAmount = 0;

  if (includeSalesTax && stateCode && typeof taxLookup === 'function') {
    try {
      const taxInfo = await taxLookup(stateCode);
      taxRate = normalizeTaxRate(taxInfo?.rate);
      taxAmount = principal * taxRate;
    } catch (error) {
      taxRate = 0;
      taxAmount = 0;
    }
  }

  const financedPrincipal = principal + taxAmount;
  const monthlyPayment = calculateMonthlyPayment(financedPrincipal, annualRate, years);
  const totalPaid = calculateTotalPaid(monthlyPayment, years);
  const totalInterest = calculateTotalInterest(totalPaid, financedPrincipal);
  const schedule = generateAmortizationSchedule(financedPrincipal, annualRate, years, monthlyPayment);

  return {
    loanInfo: {
      principal,
      financedPrincipal,
      annualRate,
      years,
      stateCode,
      includeSalesTax,
      taxRate,
      taxAmount
    },
    results: {
      monthlyPayment,
      totalPaid,
      totalInterest
    },
    schedule
  };
}

