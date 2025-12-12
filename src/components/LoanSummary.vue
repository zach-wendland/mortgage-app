<template>
  <div class="loan-summary">
    <div class="header-row">
      <h2>Loan Summary</h2>
      <div class="action-buttons">
        <button @click="compareScenarios" class="btn-compare" title="Compare scenarios">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 11l3 3L22 4"></path>
            <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"></path>
          </svg>
          Compare
        </button>
        <button @click="copyToClipboard" class="btn-share" title="Copy to clipboard">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
          </svg>
          Share
        </button>
        <button @click="printSummary" class="btn-print" title="Print summary">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
          </svg>
          Print
        </button>
      </div>
    </div>

    <div class="summary-grid">
      <div
        ref="cards"
        v-for="(card, index) in summaryCards"
        :key="index"
        :class="['summary-card', card.highlight ? 'highlight' : '', card.glass ? 'glass' : '']"
        :style="{ animationDelay: `${index * 100}ms` }"
        @mouseenter="card.highlight && (hoveredCard = index)"
        @mouseleave="hoveredCard = null"
      >
        <div class="card-content">
          <div class="label">{{ card.label }}</div>
          <div class="value">
            <span v-if="card.prefix">{{ card.prefix }}</span>
            <animated-number
              v-if="card.isNumber"
              :value="card.rawValue"
              :decimals="card.decimals || 2"
              :duration="card.duration || 2000"
            />
            <span v-else>{{ card.displayValue }}</span>
            <span v-if="card.suffix">{{ card.suffix }}</span>
          </div>

          <!-- Progress ring for principal vs interest breakdown -->
          <div v-if="card.showChart" class="chart-container">
            <svg class="donut-chart" viewBox="0 0 100 100">
              <circle
                class="donut-ring"
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
                stroke="rgba(255,255,255,0.1)"
                stroke-width="12"
              />
              <circle
                class="donut-segment"
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
                :stroke="card.chartColor || '#10b981'"
                stroke-width="12"
                :stroke-dasharray="getCircleDashArray(card.percentage)"
                :stroke-dashoffset="25"
                stroke-linecap="round"
                :style="{ animation: 'fillChart 2s ease-out forwards' }"
              />
              <text x="50" y="50" text-anchor="middle" dy="7" class="chart-text">
                {{ card.percentage }}%
              </text>
            </svg>
            <div class="chart-labels">
              <div class="chart-label">
                <span class="chart-dot" :style="{ background: card.chartColor || '#10b981' }"></span>
                {{ card.chartLabel }}
              </div>
            </div>
          </div>
        </div>

        <!-- Animated gradient overlay for highlight card -->
        <div v-if="card.highlight" class="gradient-overlay"></div>
        <div v-if="card.highlight" class="glow-effect" :class="{ pulsing: hoveredCard === index }"></div>
      </div>
    </div>

    <!-- Comparison Modal -->
    <transition name="modal">
      <div v-if="showComparisonModal" class="modal-overlay" @click="closeModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Compare Scenarios</h3>
            <button @click="closeModal" class="close-btn">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="comparison-grid">
              <div class="scenario-column">
                <h4>Current Scenario</h4>
                <div class="scenario-item" v-for="item in comparisonItems" :key="item.label">
                  <span class="item-label">{{ item.label }}</span>
                  <span class="item-value">{{ item.current }}</span>
                </div>
              </div>
              <div class="scenario-column">
                <h4>Saved Scenario</h4>
                <div class="scenario-item" v-for="item in comparisonItems" :key="item.label">
                  <span class="item-label">{{ item.label }}</span>
                  <span class="item-value">{{ item.saved || 'N/A' }}</span>
                  <span
                    v-if="item.saved && item.difference"
                    :class="['difference', item.differenceClass]"
                  >
                    {{ item.difference }}
                  </span>
                </div>
              </div>
            </div>
            <div class="modal-actions">
              <button @click="saveCurrentScenario" class="btn-primary">Save Current</button>
              <button @click="clearSavedScenario" class="btn-secondary">Clear Saved</button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Toast Notification -->
    <transition name="toast">
      <div v-if="showToast" class="toast-notification" role="alert" aria-live="polite" aria-atomic="true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'LoanSummary',
  props: {
    loanInfo: {
      type: Object,
      required: true
    },
    results: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      hoveredCard: null,
      showComparisonModal: false,
      savedScenario: null,
      showToast: false,
      toastMessage: '',
      observer: null,
      toastTimeout: null
    };
  },
  computed: {
    summaryCards() {
      const cards = [];

      // Monthly Payment - Highlight card with chart
      const interestPercentage = this.results.totalPaid > 0
        ? ((this.results.totalInterest / this.results.totalPaid) * 100).toFixed(1)
        : '0';
      cards.push({
        label: 'Monthly Payment',
        prefix: '$',
        rawValue: this.results.monthlyPayment,
        isNumber: true,
        decimals: 2,
        highlight: true,
        showChart: true,
        percentage: parseFloat(interestPercentage),
        chartColor: '#f59e0b',
        chartLabel: 'Interest Portion',
        duration: 2500
      });

      // Loan Amount
      cards.push({
        label: 'Loan Amount',
        prefix: '$',
        rawValue: this.loanInfo.principal,
        isNumber: true,
        decimals: 2,
        glass: true
      });

      // Financed Amount (if sales tax included)
      if (this.loanInfo.includeSalesTax) {
        cards.push({
          label: 'Financed Amount (incl. Sales Tax)',
          prefix: '$',
          rawValue: this.loanInfo.financedPrincipal,
          isNumber: true,
          decimals: 2,
          glass: true
        });
      }

      // Interest Rate
      cards.push({
        label: 'Interest Rate',
        rawValue: this.loanInfo.annualRate,
        suffix: '%',
        isNumber: true,
        decimals: 2,
        glass: true,
        duration: 1500
      });

      // Loan Term
      cards.push({
        label: 'Loan Term',
        rawValue: this.loanInfo.years,
        suffix: ' years',
        isNumber: true,
        decimals: 0,
        glass: true,
        duration: 1000
      });

      // Sales Tax Rate
      if (this.loanInfo.includeSalesTax && this.loanInfo.stateCode) {
        cards.push({
          label: `Sales Tax Rate (${this.loanInfo.stateCode})`,
          rawValue: this.loanInfo.taxRate * 100,
          suffix: '%',
          isNumber: true,
          decimals: 2,
          glass: true,
          duration: 1500
        });
      }

      // Sales Tax Amount
      if (this.loanInfo.includeSalesTax) {
        cards.push({
          label: 'Sales Tax Amount',
          prefix: '$',
          rawValue: this.loanInfo.taxAmount,
          isNumber: true,
          decimals: 2,
          glass: true
        });
      }

      // Total Paid
      cards.push({
        label: 'Total Paid',
        prefix: '$',
        rawValue: this.results.totalPaid,
        isNumber: true,
        decimals: 2,
        glass: true,
        duration: 2500
      });

      // Total Interest
      const principalPercentage = this.results.totalPaid > 0
        ? ((this.loanInfo.principal / this.results.totalPaid) * 100).toFixed(1)
        : '0';
      cards.push({
        label: 'Total Interest',
        prefix: '$',
        rawValue: this.results.totalInterest,
        isNumber: true,
        decimals: 2,
        glass: true,
        showChart: true,
        percentage: 100 - parseFloat(principalPercentage),
        chartColor: '#ef4444',
        chartLabel: 'Interest vs Total',
        duration: 2500
      });

      return cards;
    },
    comparisonItems() {
      if (!this.savedScenario) {
        return [
          { label: 'Monthly Payment', current: `$${this.formatCurrency(this.results.monthlyPayment)}` },
          { label: 'Total Paid', current: `$${this.formatCurrency(this.results.totalPaid)}` },
          { label: 'Total Interest', current: `$${this.formatCurrency(this.results.totalInterest)}` },
          { label: 'Interest Rate', current: `${this.loanInfo.annualRate}%` },
          { label: 'Loan Term', current: `${this.loanInfo.years} years` }
        ];
      }

      return [
        {
          label: 'Monthly Payment',
          current: `$${this.formatCurrency(this.results.monthlyPayment)}`,
          saved: `$${this.formatCurrency(this.savedScenario.monthlyPayment)}`,
          difference: this.formatDifference(this.results.monthlyPayment - this.savedScenario.monthlyPayment, true),
          differenceClass: this.results.monthlyPayment > this.savedScenario.monthlyPayment ? 'negative' : 'positive'
        },
        {
          label: 'Total Paid',
          current: `$${this.formatCurrency(this.results.totalPaid)}`,
          saved: `$${this.formatCurrency(this.savedScenario.totalPaid)}`,
          difference: this.formatDifference(this.results.totalPaid - this.savedScenario.totalPaid, true),
          differenceClass: this.results.totalPaid > this.savedScenario.totalPaid ? 'negative' : 'positive'
        },
        {
          label: 'Total Interest',
          current: `$${this.formatCurrency(this.results.totalInterest)}`,
          saved: `$${this.formatCurrency(this.savedScenario.totalInterest)}`,
          difference: this.formatDifference(this.results.totalInterest - this.savedScenario.totalInterest, true),
          differenceClass: this.results.totalInterest > this.savedScenario.totalInterest ? 'negative' : 'positive'
        },
        {
          label: 'Interest Rate',
          current: `${this.loanInfo.annualRate}%`,
          saved: `${this.savedScenario.annualRate}%`,
          difference: this.formatDifference(this.loanInfo.annualRate - this.savedScenario.annualRate, false),
          differenceClass: this.loanInfo.annualRate > this.savedScenario.annualRate ? 'negative' : 'positive'
        },
        {
          label: 'Loan Term',
          current: `${this.loanInfo.years} years`,
          saved: `${this.savedScenario.years} years`,
          difference: this.loanInfo.years !== this.savedScenario.years ? `${this.loanInfo.years > this.savedScenario.years ? '+' : ''}${this.loanInfo.years - this.savedScenario.years} years` : null
        }
      ];
    }
  },
  mounted() {
    this.setupIntersectionObserver();
  },
  beforeUnmount() {
    if (this.observer) {
      this.observer.disconnect();
    }
    if (this.toastTimeout) {
      clearTimeout(this.toastTimeout);
    }
  },
  methods: {
    formatCurrency(value) {
      return value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    formatDifference(value, isCurrency) {
      const sign = value > 0 ? '+' : '';
      const formatted = isCurrency ? `$${Math.abs(value).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}` : Math.abs(value).toFixed(2);
      return `${sign}${value < 0 ? '-' : ''}${formatted}`;
    },
    getCircleDashArray(percentage) {
      const circumference = 2 * Math.PI * 40;
      const filled = (percentage / 100) * circumference;
      return `${filled} ${circumference}`;
    },
    compareScenarios() {
      this.showComparisonModal = true;
    },
    closeModal() {
      this.showComparisonModal = false;
    },
    saveCurrentScenario() {
      this.savedScenario = {
        monthlyPayment: this.results.monthlyPayment,
        totalPaid: this.results.totalPaid,
        totalInterest: this.results.totalInterest,
        annualRate: this.loanInfo.annualRate,
        years: this.loanInfo.years,
        principal: this.loanInfo.principal
      };
      this.showToastNotification('Scenario saved successfully!');
    },
    clearSavedScenario() {
      this.savedScenario = null;
      this.showToastNotification('Saved scenario cleared');
    },
    async copyToClipboard() {
      const summary = `
Loan Summary
${'-'.repeat(50)}
Monthly Payment: $${this.formatCurrency(this.results.monthlyPayment)}
Loan Amount: $${this.formatCurrency(this.loanInfo.principal)}
Interest Rate: ${this.loanInfo.annualRate}%
Loan Term: ${this.loanInfo.years} years
Total Paid: $${this.formatCurrency(this.results.totalPaid)}
Total Interest: $${this.formatCurrency(this.results.totalInterest)}
${'-'.repeat(50)}
Generated by Mortgage Calculator
      `.trim();

      try {
        await navigator.clipboard.writeText(summary);
        this.showToastNotification('Copied to clipboard!');
      } catch (err) {
        this.showToastNotification('Failed to copy');
      }
    },
    printSummary() {
      window.print();
    },
    showToastNotification(message) {
      this.toastMessage = message;
      this.showToast = true;
      if (this.toastTimeout) {
        clearTimeout(this.toastTimeout);
      }
      this.toastTimeout = setTimeout(() => {
        this.showToast = false;
      }, 3000);
    },
    setupIntersectionObserver() {
      const options = {
        threshold: 0.1,
        rootMargin: '0px'
      };

      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      }, options);

      this.$nextTick(() => {
        if (this.$refs.cards) {
          const cards = Array.isArray(this.$refs.cards) ? this.$refs.cards : [this.$refs.cards];
          cards.forEach(card => {
            if (card) {
              this.observer.observe(card);
            }
          });
        }
      });
    }
  },
  components: {
    AnimatedNumber: {
      props: {
        value: {
          type: Number,
          required: true
        },
        decimals: {
          type: Number,
          default: 2
        },
        duration: {
          type: Number,
          default: 2000
        }
      },
      data() {
        return {
          displayValue: 0,
          animationFrameId: null
        };
      },
      computed: {
        formattedValue() {
          return this.displayValue.toFixed(this.decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        }
      },
      watch: {
        value: {
          handler(newValue) {
            this.animateValue(newValue);
          },
          immediate: true
        }
      },
      beforeUnmount() {
        if (this.animationFrameId) {
          cancelAnimationFrame(this.animationFrameId);
        }
      },
      methods: {
        animateValue(endValue) {
          // Cancel any existing animation
          if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
          }

          const startValue = 0;
          const startTime = performance.now();

          const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / this.duration, 1);

            // Ease-out-expo easing function
            const easeOutExpo = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);

            this.displayValue = startValue + (endValue - startValue) * easeOutExpo;

            if (progress < 1) {
              this.animationFrameId = requestAnimationFrame(animate);
            } else {
              this.displayValue = endValue;
              this.animationFrameId = null;
            }
          };

          this.animationFrameId = requestAnimationFrame(animate);
        }
      },
      template: '<span>{{ formattedValue }}</span>'
    }
  }
};
</script>

<style scoped>
.loan-summary {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

h2 {
  text-align: left;
  color: #0f172a;
  font-size: 1.8rem;
  margin: 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-buttons button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 12px;
  border: none;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  color: #475467;
  border: 1px solid #e4e7ec;
}

.action-buttons button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.btn-compare {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  border-color: transparent !important;
}

.btn-share {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white !important;
  border-color: transparent !important;
}

.btn-print:hover {
  background: #f9fafb;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
}

.summary-card {
  position: relative;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 160px;
  opacity: 0;
  transform: translateY(20px);
  animation: slideInUp 0.6s ease-out forwards;
  overflow: hidden;
}

@keyframes slideInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.summary-card.visible {
  animation: bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
}

@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.3) translateY(30px);
  }
  50% {
    transform: scale(1.05) translateY(-5px);
  }
  70% {
    transform: scale(0.95);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.summary-card.glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.summary-card.glass:hover {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid transparent;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
  border-image: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) 1;
}

.summary-card.glass::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 20px;
  padding: 1px;
  background: linear-gradient(135deg, transparent, transparent);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.4s ease;
}

.summary-card.glass:hover::before {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  opacity: 1;
}

.summary-card.highlight {
  grid-column: span 2;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: white;
  border: none;
  position: relative;
  overflow: hidden;
  transition: all 0.4s ease;
}

.summary-card.highlight:hover {
  transform: translateY(-6px) rotateX(5deg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.gradient-overlay {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent 30%,
    rgba(255, 255, 255, 0.1) 50%,
    transparent 70%
  );
  animation: shimmer 3s infinite;
  pointer-events: none;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%) translateY(-100%) rotate(45deg);
  }
  100% {
    transform: translateX(100%) translateY(100%) rotate(45deg);
  }
}

.glow-effect {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.4) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;
}

.glow-effect.pulsing {
  animation: pulse 2s ease-in-out infinite;
  opacity: 1;
}

@keyframes pulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.6;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.8;
  }
}

.card-content {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.label {
  font-size: 0.85rem;
  letter-spacing: 0.01em;
  text-transform: uppercase;
  color: #475467;
  font-weight: 600;
}

.summary-card.highlight .label {
  color: rgba(255, 255, 255, 0.7);
}

.value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.summary-card.highlight .value {
  color: white;
  font-size: 2.5rem;
}

.chart-container {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 16px;
}

.donut-chart {
  width: 80px;
  height: 80px;
  transform: rotate(-90deg);
}

.donut-ring {
  transition: all 0.3s ease;
}

.donut-segment {
  transition: all 0.3s ease;
}

@keyframes fillChart {
  from {
    stroke-dashoffset: 251.2;
  }
  to {
    stroke-dashoffset: 25;
  }
}

.chart-text {
  font-size: 16px;
  font-weight: 700;
  fill: white;
  transform: rotate(90deg);
  transform-origin: center;
}

.chart-labels {
  flex: 1;
}

.chart-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.9);
}

.chart-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 24px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e4e7ec;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #0f172a;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  color: #475467;
}

.close-btn:hover {
  background: #f9fafb;
  color: #0f172a;
}

.modal-body {
  padding: 24px;
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.scenario-column {
  background: #f9fafb;
  border-radius: 16px;
  padding: 20px;
}

.scenario-column h4 {
  margin: 0 0 16px 0;
  color: #0f172a;
  font-size: 1.1rem;
}

.scenario-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 0;
  border-bottom: 1px solid #e4e7ec;
  position: relative;
}

.scenario-item:last-child {
  border-bottom: none;
}

.item-label {
  font-size: 0.8rem;
  color: #475467;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.01em;
}

.item-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: #0f172a;
}

.difference {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.difference.positive {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.difference.negative {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-primary, .btn-secondary {
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  font-size: 0.95rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
  background: white;
  color: #475467;
  border: 1px solid #e4e7ec;
}

.btn-secondary:hover {
  background: #f9fafb;
}

/* Toast Notification */
.toast-notification {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  z-index: 2000;
  animation: toastSlideIn 0.3s ease-out;
}

@keyframes toastSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Transitions */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9) translateY(20px);
}

.toast-enter-active, .toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* Print Styles */
@media print {
  .action-buttons,
  .gradient-overlay,
  .glow-effect,
  .chart-container {
    display: none !important;
  }

  .summary-card {
    page-break-inside: avoid;
    box-shadow: none !important;
    border: 1px solid #e4e7ec !important;
  }

  .summary-card.highlight {
    background: #f9fafb !important;
    color: #0f172a !important;
  }

  .summary-card.highlight .label,
  .summary-card.highlight .value {
    color: #0f172a !important;
  }
}

/* Responsive */
@media (max-width: 768px) {
  h2 {
    font-size: 1.5rem;
  }

  .summary-card.highlight {
    grid-column: span 1;
  }

  .value {
    font-size: 1.5rem;
  }

  .summary-card.highlight .value {
    font-size: 2rem;
  }

  .comparison-grid {
    grid-template-columns: 1fr;
  }

  .chart-container {
    justify-content: center;
  }

  .action-buttons {
    width: 100%;
    justify-content: stretch;
  }

  .action-buttons button {
    flex: 1;
  }

  .toast-notification {
    left: 24px;
    right: 24px;
  }
}

@media (max-width: 480px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons button {
    width: 100%;
  }
}
</style>
