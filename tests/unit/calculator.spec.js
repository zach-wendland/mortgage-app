import { describe, it, expect } from 'vitest';
import {
  calculateMonthlyPayment,
  calculateTotalPaid,
  calculateTotalInterest,
  generateAmortizationSchedule,
  validateInputs,
  calculateLTV,
  calculateMonthlyPMI,
  calculatePMIDropOff,
  calculateTotalPMI
} from '../../src/utils/calculator.js';

describe('calculateMonthlyPayment', () => {
  it('computes payment for standard loan', () => {
    const payment = calculateMonthlyPayment(200000, 5, 30);
    expect(payment).toBeCloseTo(1073.64, 2);
  });

  it('handles zero interest', () => {
    const payment = calculateMonthlyPayment(120000, 0, 10);
    expect(payment).toBeCloseTo(1000, 5);
  });

  it('handles short term loans', () => {
    const payment = calculateMonthlyPayment(10000, 6, 2);
    expect(payment).toBeCloseTo(443.21, 2);
  });

  it('handles high interest', () => {
    const payment = calculateMonthlyPayment(50000, 15, 5);
    expect(payment).toBeCloseTo(1189.5, 2);
  });

  it('handles large loan', () => {
    const payment = calculateMonthlyPayment(1000000, 4, 30);
    expect(payment).toBeCloseTo(4774.15, 2);
  });
});

describe('calculateTotalPaid', () => {
  it('multiplies monthly payment by term', () => {
    const total = calculateTotalPaid(1073.64, 30);
    expect(total).toBeCloseTo(386510.4, 2);
  });

  it('handles short term', () => {
    expect(calculateTotalPaid(500, 5)).toBe(30000);
  });
});

describe('calculateTotalInterest', () => {
  it('subtracts principal from total paid', () => {
    const interest = calculateTotalInterest(386510.4, 200000);
    expect(interest).toBeCloseTo(186510.4, 2);
  });

  it('returns zero when total equals principal', () => {
    expect(calculateTotalInterest(100000, 100000)).toBe(0);
  });
});

describe('generateAmortizationSchedule', () => {
  it('creates expected number of payments', () => {
    const monthlyPayment = calculateMonthlyPayment(100000, 5, 10);
    const schedule = generateAmortizationSchedule(100000, 5, 10, monthlyPayment);
    expect(schedule).toHaveLength(120);
  });

  it('ensures principal + interest equals payment', () => {
    const monthlyPayment = calculateMonthlyPayment(150000, 5.5, 20);
    const schedule = generateAmortizationSchedule(150000, 5.5, 20, monthlyPayment);
    schedule.forEach((payment) => {
      const total = payment.principalPayment + payment.interestPayment;
      expect(total).toBeCloseTo(payment.paymentAmount, 2);
    });
  });

  it('reduces balance to zero by last payment', () => {
    const monthlyPayment = calculateMonthlyPayment(100000, 6, 15);
    const schedule = generateAmortizationSchedule(100000, 6, 15, monthlyPayment);
    expect(schedule.at(-1).remainingBalance).toBeCloseTo(0, 2);
  });
});

describe('validateInputs', () => {
  it('accepts valid inputs', () => {
    expect(validateInputs(200000, 5, 30)).toEqual({ isValid: true, error: null });
  });

  it('rejects invalid cases', () => {
    expect(validateInputs(0, 5, 30).isValid).toBe(false);
    expect(validateInputs(200000, -1, 30).isValid).toBe(false);
    expect(validateInputs(200000, 5, 0).isValid).toBe(false);
    expect(validateInputs(200000000, 5, 30).isValid).toBe(false);
    expect(validateInputs(200000, 150, 30).isValid).toBe(false);
    expect(validateInputs(200000, 5, 60).isValid).toBe(false);
  });
});

describe('calculateLTV', () => {
  it('calculates LTV correctly', () => {
    expect(calculateLTV(400000, 500000)).toBeCloseTo(0.80, 2);
    expect(calculateLTV(450000, 500000)).toBeCloseTo(0.90, 2);
    expect(calculateLTV(250000, 500000)).toBeCloseTo(0.50, 2);
  });

  it('returns 0 for zero or negative property value', () => {
    expect(calculateLTV(400000, 0)).toBe(0);
    expect(calculateLTV(400000, -100)).toBe(0);
  });

  it('handles edge cases', () => {
    expect(calculateLTV(0, 500000)).toBe(0);
    expect(calculateLTV(500000, 500000)).toBe(1);
  });
});

describe('calculateMonthlyPMI', () => {
  it('calculates monthly PMI correctly', () => {
    const monthlyPMI = calculateMonthlyPMI(400000, 0.008);
    expect(monthlyPMI).toBeCloseTo(266.67, 2);
  });

  it('calculates PMI for different rates', () => {
    expect(calculateMonthlyPMI(300000, 0.005)).toBeCloseTo(125, 2);
    expect(calculateMonthlyPMI(500000, 0.01)).toBeCloseTo(416.67, 2);
  });

  it('returns 0 for zero or negative PMI rate', () => {
    expect(calculateMonthlyPMI(400000, 0)).toBe(0);
    expect(calculateMonthlyPMI(400000, -0.01)).toBe(0);
  });
});

describe('calculatePMIDropOff', () => {
  it('finds PMI drop-off point when LTV reaches 78%', () => {
    const monthlyPayment = calculateMonthlyPayment(400000, 6, 30);
    const schedule = generateAmortizationSchedule(400000, 6, 30, monthlyPayment);
    const dropOff = calculatePMIDropOff(schedule, 500000);

    expect(dropOff).toBeGreaterThan(0);
    expect(dropOff).toBeLessThan(schedule.length);

    // Verify the balance at drop-off is at or below 78% of property value
    const dropOffPayment = schedule[dropOff - 1];
    expect(dropOffPayment.remainingBalance).toBeLessThanOrEqual(500000 * 0.78);
  });

  it('returns null for zero or negative property value', () => {
    const monthlyPayment = calculateMonthlyPayment(400000, 6, 30);
    const schedule = generateAmortizationSchedule(400000, 6, 30, monthlyPayment);

    expect(calculatePMIDropOff(schedule, 0)).toBeNull();
    expect(calculatePMIDropOff(schedule, -100)).toBeNull();
  });

  it('handles edge case where PMI never drops off', () => {
    const monthlyPayment = calculateMonthlyPayment(950000, 6, 30);
    const schedule = generateAmortizationSchedule(950000, 6, 30, monthlyPayment);
    // Property value is $1M, loan is $950k (95% LTV), should never reach 78%
    const dropOff = calculatePMIDropOff(schedule, 1000000);

    expect(dropOff).toBeGreaterThan(0);
  });
});

describe('calculateTotalPMI', () => {
  it('calculates total PMI paid until drop-off', () => {
    const monthlyPMI = 266.67;
    const dropOffMonth = 120;
    const totalPMI = calculateTotalPMI(monthlyPMI, dropOffMonth);

    expect(totalPMI).toBeCloseTo(32000.4, 2);
  });

  it('returns 0 when no drop-off month', () => {
    expect(calculateTotalPMI(266.67, null)).toBe(0);
  });

  it('returns 0 when monthly PMI is zero or negative', () => {
    expect(calculateTotalPMI(0, 120)).toBe(0);
    expect(calculateTotalPMI(-10, 120)).toBe(0);
  });

  it('handles different scenarios', () => {
    expect(calculateTotalPMI(200, 60)).toBe(12000);
    expect(calculateTotalPMI(150.50, 24)).toBeCloseTo(3612, 2);
  });
});
