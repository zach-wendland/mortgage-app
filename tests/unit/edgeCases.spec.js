import { describe, it, expect } from 'vitest';
import { normalizeTaxRate } from '../../src/utils/loanProcessor.js';
import { calculateMonthlyPayment, generateAmortizationSchedule } from '../../src/utils/calculator.js';

describe('Edge Cases from Code Review', () => {

  describe('Tax Normalization Ambiguity', () => {
    it('handles decimal format explicitly', () => {
      expect(normalizeTaxRate(0.065, 'decimal')).toBe(0.065);
      expect(normalizeTaxRate(0.5, 'decimal')).toBe(0.5);
      expect(normalizeTaxRate(0.10, 'decimal')).toBe(0.10);
    });

    it('handles percent format explicitly', () => {
      expect(normalizeTaxRate(6.5, 'percent')).toBe(0.065);
      expect(normalizeTaxRate(0.5, 'percent')).toBe(0.005);
      expect(normalizeTaxRate(10, 'percent')).toBe(0.10);
    });

    it('auto-detects rates > 0.20 as percentages', () => {
      expect(normalizeTaxRate(6.5)).toBe(0.065);
      expect(normalizeTaxRate(10)).toBe(0.10);
      expect(normalizeTaxRate(7.25)).toBe(0.0725);
    });

    it('auto-detects rates ≤ 0.20 as decimals', () => {
      expect(normalizeTaxRate(0.065)).toBe(0.065);
      expect(normalizeTaxRate(0.10)).toBe(0.10);
      expect(normalizeTaxRate(0.0725)).toBe(0.0725);
    });

    it('documents ambiguous edge case at 0.5', () => {
      // Without explicit format, 0.5 treated as decimal (50%)
      expect(normalizeTaxRate(0.5)).toBe(0.5);

      // Correct handling requires explicit format
      expect(normalizeTaxRate(0.5, 'percent')).toBe(0.005);
    });

    it('returns 0 for invalid inputs', () => {
      expect(normalizeTaxRate(NaN)).toBe(0);
      expect(normalizeTaxRate(Infinity)).toBe(0);
      expect(normalizeTaxRate(-1)).toBe(0);
      expect(normalizeTaxRate(0)).toBe(0);
    });
  });

  describe('Final Payment Precision', () => {
    it('ensures sum of principal payments equals original principal', () => {
      const testCases = [
        { principal: 200000, rate: 6, years: 30 },
        { principal: 100000, rate: 5.5, years: 15 },
        { principal: 500000, rate: 7.25, years: 30 },
        { principal: 75000, rate: 4.5, years: 10 }
      ];

      testCases.forEach(({ principal, rate, years }) => {
        const monthlyPayment = calculateMonthlyPayment(principal, rate, years);
        const schedule = generateAmortizationSchedule(principal, rate, years, monthlyPayment);

        // Sum all principal payments
        const totalPrincipal = schedule.reduce((sum, payment) => {
          return sum + payment.principalPayment;
        }, 0);

        // Should equal original principal to 2 decimal places (penny-perfect)
        expect(totalPrincipal).toBeCloseTo(principal, 2);
      });
    });

    it('final balance is exactly zero', () => {
      const monthlyPayment = calculateMonthlyPayment(200000, 6, 30);
      const schedule = generateAmortizationSchedule(200000, 6, 30, monthlyPayment);

      const finalPayment = schedule[schedule.length - 1];
      expect(finalPayment.remainingBalance).toBe(0);
    });

    it('final payment may differ from regular payment', () => {
      const monthlyPayment = calculateMonthlyPayment(200000, 6, 30);
      const schedule = generateAmortizationSchedule(200000, 6, 30, monthlyPayment);

      const regularPayment = schedule[100].paymentAmount;
      const finalPayment = schedule[schedule.length - 1].paymentAmount;

      // Difference should be small (< $1.00 typically < $0.50)
      expect(Math.abs(finalPayment - regularPayment)).toBeLessThan(1.00);
    });

    it('all intermediate balances are positive', () => {
      const monthlyPayment = calculateMonthlyPayment(200000, 6, 30);
      const schedule = generateAmortizationSchedule(200000, 6, 30, monthlyPayment);

      schedule.forEach((payment, index) => {
        if (index < schedule.length - 1) {
          expect(payment.remainingBalance).toBeGreaterThan(0);
        }
      });
    });
  });

  describe('NaN Prevention', () => {
    it('Number.isFinite correctly identifies valid numbers', () => {
      expect(Number.isFinite(6.89)).toBe(true);
      expect(Number.isFinite(0)).toBe(true);
      expect(Number.isFinite(-5.5)).toBe(true);

      expect(Number.isFinite(NaN)).toBe(false);
      expect(Number.isFinite(Infinity)).toBe(false);
      expect(Number.isFinite(-Infinity)).toBe(false);
      expect(Number.isFinite(undefined)).toBe(false);
      expect(Number.isFinite(null)).toBe(false);
    });

    it('parseFloat returns NaN for invalid strings', () => {
      const invalidStrings = ['N/A', 'ND', '', ' ', 'abc', '.'];

      invalidStrings.forEach(str => {
        const result = Number.parseFloat(str);
        expect(Number.isNaN(result) || !Number.isFinite(result)).toBe(true);
      });
    });
  });
});
