import { mount } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import AmortizationTable from '../../../src/components/AmortizationTable.vue';

const sampleSchedule = [
  {
    paymentNumber: 1,
    paymentAmount: 1000,
    principalPayment: 300,
    interestPayment: 700,
    remainingBalance: 99900
  },
  {
    paymentNumber: 2,
    paymentAmount: 1000,
    principalPayment: 302,
    interestPayment: 698,
    remainingBalance: 99598
  }
];

const sampleLoanInfo = {
  principal: 100000,
  propertyValue: 125000,
  downPayment: 25000,
  ltv: 0.80,
  pmiRequired: false,
  annualRate: 5,
  years: 10
};

const sampleResults = {
  monthlyPayment: 1000,
  monthlyPMI: 0,
  monthlyInsurance: 0,
  totalMonthlyPayment: 1000,
  pmiDropOffMonth: null,
  totalPMIPaid: 0,
  totalPaid: 12000,
  totalInterest: 2000
};

describe('AmortizationTable', () => {
  it('renders rows for each payment in the schedule', () => {
    const wrapper = mount(AmortizationTable, {
      props: {
        schedule: sampleSchedule,
        loanInfo: sampleLoanInfo,
        results: sampleResults
      }
    });

    const rows = wrapper.findAll('tbody tr');
    expect(rows).toHaveLength(sampleSchedule.length);
    expect(rows[0].text()).toContain('$1,000.00');
    expect(rows[0].text()).toContain('$300.00');
    expect(rows[0].text()).toContain('$700.00');
  });

  it('displays summary info with payment count', () => {
    const wrapper = mount(AmortizationTable, {
      props: {
        schedule: sampleSchedule,
        loanInfo: sampleLoanInfo,
        results: sampleResults
      }
    });

    expect(wrapper.find('.table-info').text()).toContain('Showing all 2 payments');
  });
});

