<template>
  <div class="input-form">
    <div class="form-header">
      <p class="eyebrow">Loan inputs</p>
      <h1>Amortization calculator</h1>
      <p class="subhead">Ground your payment assumptions with structured inputs and instant feedback.</p>
    </div>

    <form @submit.prevent="handleSubmit" @keydown.enter.prevent="handleSubmit">
      <div class="form-grid">
        <!-- Loan Amount with Currency Formatting -->
        <div class="form-group glassmorphic-input" :class="{ 'input-focused': focusedField === 'principal', 'has-value': loanData.principal, 'slide-in': true }" style="animation-delay: 0s">
          <label for="principal" :class="{ 'label-float': focusedField === 'principal' || loanData.principal }">
            Loan Amount
          </label>
          <div class="input-wrapper">
            <span class="currency-symbol" :class="{ 'symbol-active': focusedField === 'principal' || loanData.principal }">$</span>
            <input
              id="principal"
              v-model="formattedPrincipal"
              type="text"
              placeholder="425,000"
              required
              @focus="handleFocus('principal')"
              @blur="handleBlur('principal')"
              @input="handlePrincipalInput"
            />
            <transition name="checkmark">
              <svg v-if="loanData.principal && loanData.principal > 0" class="success-check" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </transition>
          </div>
        </div>

        <!-- Interest Rate -->
        <div class="form-group glassmorphic-input" :class="{ 'input-focused': focusedField === 'rate', 'has-value': loanData.annualRate, 'slide-in': true }" style="animation-delay: 0.1s">
          <label for="rate" :class="{ 'label-float': focusedField === 'rate' || loanData.annualRate }">
            Interest Rate
          </label>
          <div class="input-wrapper">
            <input
              id="rate"
              v-model.number="loanData.annualRate"
              type="number"
              step="0.01"
              placeholder="6.5"
              required
              @focus="handleFocus('rate')"
              @blur="handleBlur('rate')"
            />
            <span class="percent-symbol" :class="{ 'symbol-active': focusedField === 'rate' || loanData.annualRate }">%</span>
            <transition name="checkmark">
              <svg v-if="loanData.annualRate && loanData.annualRate > 0" class="success-check" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </transition>
          </div>
        </div>

        <!-- Loan Term with Range Slider -->
        <div class="form-group glassmorphic-input slider-group" :class="{ 'input-focused': focusedField === 'years', 'has-value': loanData.years, 'slide-in': true }" style="animation-delay: 0.2s">
          <label for="years" :class="{ 'label-float': true }">
            Loan Term (Years)
          </label>
          <div class="slider-wrapper">
            <input
              id="years"
              v-model.number="loanData.years"
              type="range"
              min="1"
              max="40"
              step="1"
              class="range-slider"
              @focus="handleFocus('years')"
              @blur="handleBlur('years')"
              @input="handleSliderInput"
            />
            <div class="slider-track-fill" :style="{ width: sliderFillWidth }"></div>
            <transition name="tooltip">
              <div v-if="loanData.years" class="slider-tooltip" :style="{ left: sliderTooltipPosition }">
                {{ loanData.years }} years
              </div>
            </transition>
          </div>
          <div class="slider-labels">
            <span>1</span>
            <span>40</span>
          </div>
        </div>

        <!-- State Selector -->
        <div class="form-group glassmorphic-input" :class="{ 'input-focused': focusedField === 'state', 'has-value': loanData.stateCode, 'slide-in': true }" style="animation-delay: 0.3s">
          <label for="state" :class="{ 'label-float': focusedField === 'state' || loanData.stateCode }">
            State
          </label>
          <div class="input-wrapper">
            <select
              id="state"
              v-model="loanData.stateCode"
              @focus="handleFocus('state')"
              @blur="handleBlur('state')"
            >
              <option value="">Select state</option>
              <option v-for="s in states" :key="s.code" :value="s.code">
                {{ s.code }} - {{ s.name }}
              </option>
            </select>
            <transition name="checkmark">
              <svg v-if="loanData.stateCode" class="success-check" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </transition>
          </div>
        </div>
      </div>

      <!-- Checkbox with Glassmorphism -->
      <div class="form-group checkbox-group glassmorphic-checkbox slide-in" style="animation-delay: 0.4s">
        <label class="checkbox-label">
          <div class="custom-checkbox" :class="{ 'checked': loanData.includeSalesTax }" @click="toggleCheckbox">
            <input type="checkbox" v-model="loanData.includeSalesTax" />
            <span class="checkbox-inner">
              <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          </div>
          <span>Include state sales tax in loan</span>
        </label>
        <small class="help-text">If checked, we apply the state average sales tax to your financed amount.</small>
      </div>

      <!-- Error Message with Shake Animation -->
      <transition name="shake">
        <div v-if="errorMessage" class="error-message slide-in" style="animation-delay: 0s">
          <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" stroke-width="2"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01" />
          </svg>
          {{ errorMessage }}
        </div>
      </transition>

      <!-- Action Buttons with Neumorphism -->
      <div class="actions slide-in" style="animation-delay: 0.5s">
        <button
          type="submit"
          class="calculate-btn neumorphic-btn"
          :class="{ 'btn-loading': isCalculating }"
          @click="handleRipple"
          ref="calculateBtn"
        >
          <span class="btn-content">
            <transition name="fade" mode="out-in">
              <span v-if="!isCalculating" key="text">Run amortization</span>
              <span v-else key="loading" class="loading-spinner">
                <svg class="spinner" viewBox="0 0 50 50">
                  <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>
                </svg>
                Calculating...
              </span>
            </transition>
          </span>
          <span class="shimmer"></span>
        </button>

        <transition name="slide-fade">
          <button v-if="showReset" type="button" class="reset-btn neumorphic-btn-secondary" @click="handleReset">
            <svg class="reset-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Reset
          </button>
        </transition>
      </div>

      <!-- Keyboard Shortcut Hint -->
      <transition name="fade">
        <div v-if="showKeyboardHint" class="keyboard-hint">
          <kbd>Enter</kbd>
          <span>to calculate</span>
        </div>
      </transition>
    </form>
  </div>
</template>

<script>
import { listStates } from '../services/taxService';
export default {
  name: 'LoanInputForm',
  props: {
    showReset: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      loanData: {
        principal: null,
        annualRate: null,
        years: 30,
        stateCode: '',
        includeSalesTax: false
      },
      errorMessage: '',
      focusedField: null,
      formattedPrincipal: '',
      isCalculating: false,
      showKeyboardHint: true,
      // Timeout IDs for cleanup
      keyboardHintTimeout: null,
      calculateTimeout: null
    };
  },
  computed: {
    states() {
      return listStates();
    },
    sliderFillWidth() {
      if (!this.loanData.years) return '0%';
      const percentage = ((this.loanData.years - 1) / (40 - 1)) * 100;
      return `${percentage}%`;
    },
    sliderTooltipPosition() {
      if (!this.loanData.years) return '0%';
      const percentage = ((this.loanData.years - 1) / (40 - 1)) * 100;
      return `${percentage}%`;
    }
  },
  mounted() {
    this.keyboardHintTimeout = setTimeout(() => {
      this.showKeyboardHint = false;
    }, 5000);
  },
  beforeUnmount() {
    // Clear all timeouts to prevent memory leaks
    if (this.keyboardHintTimeout) {
      clearTimeout(this.keyboardHintTimeout);
    }
    if (this.calculateTimeout) {
      clearTimeout(this.calculateTimeout);
    }
  },
  methods: {
    handleFocus(field) {
      this.focusedField = field;
    },
    handleBlur(field) {
      if (this.focusedField === field) {
        this.focusedField = null;
      }
    },
    handlePrincipalInput(event) {
      const value = event.target.value.replace(/,/g, '');
      const numValue = parseFloat(value);

      if (!isNaN(numValue)) {
        this.loanData.principal = numValue;
        this.formattedPrincipal = this.formatCurrency(numValue);
      } else if (value === '') {
        this.loanData.principal = null;
        this.formattedPrincipal = '';
      }
    },
    formatCurrency(value) {
      if (!value && value !== 0) return '';
      return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    handleSliderInput() {
      this.showKeyboardHint = false;
    },
    toggleCheckbox() {
      this.loanData.includeSalesTax = !this.loanData.includeSalesTax;
    },
    handleRipple(event) {
      const button = event.currentTarget;
      const ripple = document.createElement('span');
      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = event.clientX - rect.left - size / 2;
      const y = event.clientY - rect.top - size / 2;

      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.classList.add('ripple');

      button.appendChild(ripple);

      setTimeout(() => {
        ripple.remove();
      }, 600);
    },
    async handleSubmit() {
      this.errorMessage = '';
      this.isCalculating = true;
      this.showKeyboardHint = false;

      // Capture snapshot of loan data at submit time
      // This creates a new object with the current values
      const loanDataSnapshot = {
        principal: this.loanData.principal,
        annualRate: this.loanData.annualRate,
        years: this.loanData.years,
        stateCode: this.loanData.stateCode,
        includeSalesTax: this.loanData.includeSalesTax
      };

      this.calculateTimeout = setTimeout(() => {
        this.isCalculating = false;
        this.$emit('calculate', loanDataSnapshot);
      }, 800);
    },
    handleReset() {
      this.loanData = {
        principal: null,
        annualRate: null,
        years: 30,
        stateCode: '',
        includeSalesTax: false
      };
      this.formattedPrincipal = '';
      this.errorMessage = '';
      this.$emit('reset');
    },
    setError(message) {
      this.errorMessage = message;
    },
    applyRate(rate, years) {
      // Apply the selected rate from the MortgageRatesPanel
      this.loanData.annualRate = rate;

      // Apply the term years if provided
      if (years) {
        this.loanData.years = years;
      }

      // Scroll to the form smoothly
      this.$nextTick(() => {
        const formElement = this.$el.querySelector('#rate');
        if (formElement) {
          formElement.focus();
          formElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    }
  }
};
</script>

<style scoped>
.input-form {
  width: 100%;
  padding: 32px;
}

.form-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 24px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  color: #667085;
}

h1 {
  font-size: 2rem;
  color: #0f172a;
}

.subhead {
  color: #475467;
  max-width: 420px;
  font-size: 0.95rem;
}

form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

/* ===== SLIDE-IN ANIMATION ===== */
.slide-in {
  animation: slideIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  opacity: 0;
  transform: translateY(20px);
}

@keyframes slideIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== GLASSMORPHISM INPUT FIELDS ===== */
.glassmorphic-input {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.glassmorphic-input .input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.glassmorphic-input input,
.glassmorphic-input select {
  width: 100%;
  padding: 14px 16px;
  font-size: 1rem;
  border: 2px solid rgba(209, 213, 219, 0.3);
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05),
              inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.glassmorphic-input.input-focused input,
.glassmorphic-input.input-focused select {
  border-color: #6366f1;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1),
              0 8px 16px rgba(99, 102, 241, 0.15),
              inset 0 1px 0 rgba(255, 255, 255, 1);
  transform: translateY(-2px);
}

.glassmorphic-input input:focus,
.glassmorphic-input select:focus {
  outline: none;
}

/* ===== FLOATING LABELS ===== */
.glassmorphic-input label {
  color: #6b7280;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  transform-origin: left;
}

.glassmorphic-input label.label-float {
  color: #6366f1;
  font-size: 0.75rem;
  transform: translateY(-2px);
}

/* ===== CURRENCY & PERCENT SYMBOLS ===== */
.currency-symbol,
.percent-symbol {
  position: absolute;
  font-weight: 700;
  color: #9ca3af;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.currency-symbol {
  left: 16px;
  font-size: 1.1rem;
}

.percent-symbol {
  right: 16px;
  font-size: 1rem;
}

.currency-symbol.symbol-active,
.percent-symbol.symbol-active {
  color: #6366f1;
  transform: scale(1.1);
}

.glassmorphic-input input[type="text"] {
  padding-left: 36px;
}

.glassmorphic-input input[type="number"] {
  padding-right: 36px;
}

/* ===== SUCCESS CHECKMARKS ===== */
.success-check {
  position: absolute;
  right: 16px;
  width: 20px;
  height: 20px;
  color: #10b981;
  stroke-width: 3;
}

/* Checkmark transition */
.checkmark-enter-active {
  animation: checkmarkPop 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.checkmark-leave-active {
  animation: checkmarkPop 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55) reverse;
}

@keyframes checkmarkPop {
  0% {
    opacity: 0;
    transform: scale(0) rotate(-180deg);
  }
  50% {
    transform: scale(1.2) rotate(10deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

/* ===== RANGE SLIDER ===== */
.slider-group {
  padding-top: 8px;
}

.slider-wrapper {
  position: relative;
  padding: 20px 0;
  margin-top: 8px;
}

.range-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 8px;
  border-radius: 8px;
  background: rgba(209, 213, 219, 0.3);
  outline: none;
  position: relative;
  z-index: 2;
  cursor: pointer;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4),
              0 0 0 4px rgba(255, 255, 255, 1),
              0 0 0 6px rgba(99, 102, 241, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.range-slider::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  cursor: pointer;
  border: none;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4),
              0 0 0 4px rgba(255, 255, 255, 1),
              0 0 0 6px rgba(99, 102, 241, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5),
              0 0 0 4px rgba(255, 255, 255, 1),
              0 0 0 8px rgba(99, 102, 241, 0.3);
}

.range-slider::-moz-range-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5),
              0 0 0 4px rgba(255, 255, 255, 1),
              0 0 0 8px rgba(99, 102, 241, 0.3);
}

.slider-track-fill {
  position: absolute;
  top: 20px;
  left: 0;
  height: 8px;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 8px;
  pointer-events: none;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.slider-tooltip {
  position: absolute;
  top: -35px;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 700;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  pointer-events: none;
}

.slider-tooltip::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 8px;
  height: 8px;
  background: #8b5cf6;
}

.tooltip-enter-active,
.tooltip-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(5px);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 600;
}

/* ===== CHECKBOX GLASSMORPHISM ===== */
.glassmorphic-checkbox {
  padding: 18px;
  border: 2px solid rgba(209, 213, 219, 0.3);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  gap: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05),
              inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glassmorphic-checkbox:hover {
  border-color: rgba(99, 102, 241, 0.3);
  background: rgba(255, 255, 255, 0.85);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: #0f172a;
  cursor: pointer;
}

.custom-checkbox {
  position: relative;
  cursor: pointer;
}

.custom-checkbox input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  border: 2px solid #d1d5db;
  background: rgba(255, 255, 255, 0.9);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.custom-checkbox.checked .checkbox-inner {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.check-icon {
  width: 16px;
  height: 16px;
  color: white;
  opacity: 0;
  transform: scale(0) rotate(-180deg);
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.custom-checkbox.checked .check-icon {
  opacity: 1;
  transform: scale(1) rotate(0deg);
}

.help-text {
  color: #475467;
  font-size: 0.85rem;
  margin-left: 36px;
}

/* ===== ERROR MESSAGE WITH SHAKE ===== */
.error-message {
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 16px;
  padding: 14px 18px;
  background: rgba(254, 243, 242, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: #b42318;
  border: 2px solid #fecdca;
  box-shadow: 0 4px 12px rgba(180, 35, 24, 0.15);
}

.error-icon {
  width: 24px;
  height: 24px;
  color: #b42318;
  flex-shrink: 0;
}

.shake-enter-active {
  animation: shake 0.6s cubic-bezier(0.36, 0.07, 0.19, 0.97);
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  10%, 30%, 50%, 70%, 90% {
    transform: translateX(-8px);
  }
  20%, 40%, 60%, 80% {
    transform: translateX(8px);
  }
}

/* ===== NEUMORPHISM BUTTONS ===== */
.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.neumorphic-btn,
.neumorphic-btn-secondary {
  position: relative;
  width: 100%;
  padding: 16px;
  font-size: 1rem;
  font-weight: 700;
  border-radius: 16px;
  border: none;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.neumorphic-btn {
  background: linear-gradient(145deg, #1f2937, #111827);
  color: #ffffff;
  box-shadow: 8px 8px 16px rgba(0, 0, 0, 0.25),
              -8px -8px 16px rgba(55, 65, 81, 0.1),
              inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.neumorphic-btn:hover {
  transform: translateY(-2px);
  box-shadow: 12px 12px 24px rgba(0, 0, 0, 0.3),
              -8px -8px 16px rgba(55, 65, 81, 0.15),
              inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.neumorphic-btn:active {
  transform: translateY(0px);
  box-shadow: inset 4px 4px 8px rgba(0, 0, 0, 0.3),
              inset -4px -4px 8px rgba(55, 65, 81, 0.1);
}

/* Shimmer effect */
.shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.6s;
}

.neumorphic-btn:hover .shimmer {
  left: 100%;
}

/* Ripple effect */
.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0);
  animation: ripple-animation 0.6s ease-out;
  pointer-events: none;
}

@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}

/* Loading state */
.btn-loading {
  pointer-events: none;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.loading-spinner {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spinner {
  width: 20px;
  height: 20px;
  animation: rotate 1.5s linear infinite;
}

.spinner .path {
  stroke: #ffffff;
  stroke-linecap: round;
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

/* Reset button */
.neumorphic-btn-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(145deg, #f9fafb, #f3f4f6);
  color: #0f172a;
  box-shadow: 8px 8px 16px rgba(0, 0, 0, 0.08),
              -8px -8px 16px rgba(255, 255, 255, 0.9),
              inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.neumorphic-btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 12px 12px 24px rgba(0, 0, 0, 0.1),
              -8px -8px 16px rgba(255, 255, 255, 1);
}

.neumorphic-btn-secondary:active {
  transform: translateY(0px);
  box-shadow: inset 4px 4px 8px rgba(0, 0, 0, 0.1),
              inset -4px -4px 8px rgba(255, 255, 255, 0.5);
}

.reset-icon {
  width: 20px;
  height: 20px;
  stroke-width: 2;
}

/* ===== KEYBOARD HINT ===== */
.keyboard-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.keyboard-hint kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  background: linear-gradient(145deg, #f9fafb, #f3f4f6);
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.875rem;
  font-weight: 700;
  color: #374151;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05),
              inset 0 -2px 0 rgba(0, 0, 0, 0.1);
}

/* ===== TRANSITIONS ===== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* ===== RESPONSIVE ===== */
@media (max-width: 640px) {
  .input-form {
    padding: 24px;
  }

  h1 {
    font-size: 1.6rem;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .help-text {
    margin-left: 0;
  }
}
</style>
