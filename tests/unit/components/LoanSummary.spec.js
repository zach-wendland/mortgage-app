import { mount } from '@vue/test-utils';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import { nextTick } from 'vue';
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

  it('renders core loan metrics', async () => {
    const wrapper = mount(LoanSummary, {
      props: {
        loanInfo: baseLoanInfo,
        results: baseResults
      }
    });

    // Wait for component to mount and animations to complete
    await nextTick();
    await wrapper.vm.$nextTick();
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(wrapper.text()).toContain('Monthly Payment');
    expect(wrapper.text()).toContain('$1,073.64');
    expect(wrapper.text()).toContain('Loan Amount');
    expect(wrapper.text()).toContain('$200,000.00');
    expect(wrapper.text()).toContain('Loan Term');
    expect(wrapper.text()).not.toContain('Sales Tax Amount');
  });

  it('displays sales tax in principal when enabled', async () => {
    const wrapper = mount(LoanSummary, {
      props: {
        loanInfo: {
          ...baseLoanInfo,
          principal: 200000, // Original principal
          financedPrincipal: 213000, // Principal with tax included
          includeSalesTax: true,
          stateCode: 'WA',
          taxRate: 0.065,
          taxAmount: 13000
        },
        results: {
          ...baseResults,
          monthlyPayment: 1143.43,
          totalPaid: 411634.82,
          totalInterest: 198634.82
        }
      }
    });

    // Wait for component to mount and animations to complete
    await nextTick();
    await wrapper.vm.$nextTick();
    await new Promise(resolve => setTimeout(resolve, 100));

    const text = wrapper.text();
    // Simplified component shows principal amount (which includes tax)
    expect(text).toContain('Loan Amount');
    expect(text).toContain('$213,000.00');
    expect(text).toContain('Monthly Payment');
    expect(text).toContain('$1,143.43');
  });
});

