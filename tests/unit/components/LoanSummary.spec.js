import { mount } from '@vue/test-utils';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import LoanSummary from '../../../src/components/LoanSummary.vue';

const baseLoanInfo = {
  principal: 200000,
  financedPrincipal: 200000,
  annualRate: 5,
  years: 30,
  stateCode: '',
  includeSalesTax: false,
  taxRate: 0,
  taxAmount: 0
};

const baseResults = {
  monthlyPayment: 1073.64,
  totalPaid: 386510.4,
  totalInterest: 186510.4
};

describe('LoanSummary', () => {
  beforeAll(() => {
    // Mock IntersectionObserver for jsdom environment
    global.IntersectionObserver = class IntersectionObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it('renders core loan metrics', () => {
    const wrapper = mount(LoanSummary, {
      props: {
        loanInfo: baseLoanInfo,
        results: baseResults
      }
    });

    expect(wrapper.text()).toContain('Monthly Payment');
    expect(wrapper.text()).toContain('$1,073.64');
    expect(wrapper.text()).toContain('Loan Amount');
    expect(wrapper.text()).toContain('$200,000.00');
    expect(wrapper.text()).toContain('Loan Term');
    expect(wrapper.text()).not.toContain('Sales Tax Amount');
  });

  it('displays sales tax details when enabled', () => {
    const wrapper = mount(LoanSummary, {
      props: {
        loanInfo: {
          ...baseLoanInfo,
          includeSalesTax: true,
          stateCode: 'WA',
          taxRate: 0.065,
          taxAmount: 13000,
          financedPrincipal: 213000
        },
        results: baseResults
      }
    });

    const text = wrapper.text();
    expect(text).toContain('Financed Amount (incl. Sales Tax)');
    expect(text).toContain('$213,000.00');
    expect(text).toContain('Sales Tax Rate (WA)');
    expect(text).toContain('6.50%');
    expect(text).toContain('Sales Tax Amount');
    expect(text).toContain('$13,000.00');
  });
});

