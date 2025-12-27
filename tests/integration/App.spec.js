import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest';
import App from '../../src/App.vue';

const getStateSalesTaxMock = vi.fn(async () => ({
  rate: 0.065,
  source: 'mock',
  updatedAt: '2025-01-01T00:00:00Z'
}));

vi.mock('../../src/services/taxService', () => ({
  listStates: () => [
    { code: 'WA', name: 'Washington' },
    { code: 'TX', name: 'Texas' }
  ],
  getStateSalesTax: (...args) => getStateSalesTaxMock(...args)
}));

describe('App integration', () => {
  beforeAll(() => {
    if (!window.HTMLElement.prototype.scrollIntoView) {
      window.HTMLElement.prototype.scrollIntoView = vi.fn();
    }

    // Mock IntersectionObserver for LoanSummary component
    global.IntersectionObserver = class IntersectionObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  beforeEach(() => {
    getStateSalesTaxMock.mockClear();
  });

  it('performs end-to-end calculation including sales tax', async () => {
    const wrapper = mount(App);

    await wrapper.find('#principal').setValue('200000');
    await wrapper.find('#rate').setValue('5');
    await wrapper.find('#years').setValue('30');
    await wrapper.find('#state').setValue('WA');
    await wrapper.find('input[type="checkbox"]').setValue(true);

    await wrapper.find('form').trigger('submit.prevent');

    // Wait for 800ms form submission delay + async tax lookup + animations
    await new Promise(resolve => setTimeout(resolve, 850));
    await flushPromises();
    await wrapper.vm.$nextTick();
    await new Promise(resolve => setTimeout(resolve, 150)); // Wait for animations to complete

    expect(getStateSalesTaxMock).toHaveBeenCalledWith('WA');

    const summary = wrapper.find('.loan-summary');
    expect(summary.exists()).toBe(true);
    expect(summary.text()).toContain('$213,000.00'); // financed amount with 6.5% tax
    expect(summary.text()).toContain('$13,000.00'); // tax amount

    // AmortizationTable uses virtual scrolling, so check the component's schedule prop instead of DOM rows
    const tableComponent = wrapper.findComponent({ name: 'AmortizationTable' });
    expect(tableComponent.exists()).toBe(true);
    expect(tableComponent.props('schedule').length).toBe(360); // 30 years * 12 months

    expect(wrapper.find('.results-section').exists()).toBe(true);
  });
});

