import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import { nextTick } from 'vue';
import LoanInputForm from '../../../src/components/LoanInputForm.vue';

vi.mock('../../../src/services/taxService', () => ({
  listStates: () => [
    { code: 'WA', name: 'Washington' },
    { code: 'TX', name: 'Texas' }
  ]
}));

describe('LoanInputForm', () => {
  it('emits calculate event with state and tax flag', async () => {
    const wrapper = mount(LoanInputForm);

    await wrapper.find('#principal').setValue('200000');
    await wrapper.find('#propertyValue').setValue('250000');
    await wrapper.find('#rate').setValue('5');
    await wrapper.find('#years').setValue('30');
    await wrapper.find('#state').setValue('WA');
    await wrapper.find('input[type="checkbox"]').setValue(true);

    await wrapper.find('form').trigger('submit.prevent');

    // Wait for the 800ms timeout before checking the emitted event
    await new Promise(resolve => setTimeout(resolve, 850));

    const payload = wrapper.emitted('calculate')?.[0]?.[0];
    expect(payload).toMatchObject({
      principal: 200000,
      propertyValue: 250000,
      annualRate: 5,
      years: 30,
      stateCode: 'WA',
      includeSalesTax: true,
      pmiRate: 0.8,
      monthlyInsurance: 0
    });
  });

  it('emits reset event and clears inputs', async () => {
    const wrapper = mount(LoanInputForm, {
      props: { showReset: true }
    });

    await wrapper.find('#principal').setValue('150000');
    await wrapper.find('#rate').setValue('4');
    await wrapper.find('#years').setValue('20');
    await wrapper.find('#state').setValue('TX');
    await wrapper.find('input[type="checkbox"]').setValue(true);

    await wrapper.find('.reset-btn').trigger('click');

    expect(wrapper.emitted('reset')).toBeTruthy();
    expect(wrapper.find('#principal').element.value).toBe('');
    expect(wrapper.find('#state').element.value).toBe('');
    expect(wrapper.find('input[type="checkbox"]').element.checked).toBe(false);
  });

  it('displays error message via setError', async () => {
    const wrapper = mount(LoanInputForm);
    wrapper.vm.setError('Invalid input');
    await nextTick();

    expect(wrapper.find('.error-message').text()).toContain('Invalid input');
  });
});
