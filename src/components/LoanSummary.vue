<template>
  <div class="loan-summary">
    <div class="header-row">
      <h2>Loan Summary</h2>
      <div class="action-buttons">
        <button @click="copyToClipboard" class="btn-share" title="Copy to clipboard">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
          </svg>
          Share
        </button>
      </div>
    </div>

    <div class="summary-grid">
      <loan-summary-card
        v-for="(card, index) in summaryCards"
        :key="index"
        v-bind="card"
        :animation-delay="index * 100"
        @hover="card.highlight && (hoveredCard = $event ? index : null)"
      />
    </div>

    <transition name="toast">
      <div v-if="showToast" class="toast-notification" role="alert">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        <span>{{ toastMessage }}</span>
      </div>
    </transition>
  </div>
</template>

<script>
import LoanSummaryCard from './LoanSummaryCard.vue';

export default {
  name: 'LoanSummary',
  components: { LoanSummaryCard },
  props: {
    loanInfo: { type: Object, required: true },
    results: { type: Object, required: true }
  },
  data() {
    return {
      hoveredCard: null,
      showToast: false,
      toastMessage: ''
    };
  },
  computed: {
    summaryCards() {
      const interestPercentage = this.results?.totalPaid > 0 && this.results?.totalInterest
        ? ((this.results.totalInterest / this.results.totalPaid) * 100).toFixed(1)
        : '0';

      const principalPercentage = this.results?.totalPaid > 0 && this.loanInfo?.principal
        ? ((this.loanInfo.principal / this.results.totalPaid) * 100).toFixed(1)
        : '0';

      const cards = [];

      // Total Monthly Payment (P&I + PMI + Insurance) - ALWAYS show first
      const hasPMIorInsurance = (this.results?.monthlyPMI ?? 0) > 0 || (this.results?.monthlyInsurance ?? 0) > 0;
      cards.push({
        label: hasPMIorInsurance ? 'Total Monthly Payment' : 'Monthly Payment',
        prefix: '$',
        rawValue: this.results?.totalMonthlyPayment ?? this.results?.monthlyPayment ?? 0,
        isNumber: true,
        decimals: 2,
        highlight: true,
        glass: true
      });

      // P&I Breakdown (if PMI or insurance exists)
      if (hasPMIorInsurance) {
        cards.push({
          label: 'Principal & Interest',
          prefix: '$',
          rawValue: this.results?.monthlyPayment ?? 0,
          isNumber: true,
          decimals: 2
        });
      }

      // Monthly PMI (if applicable)
      if ((this.results?.monthlyPMI ?? 0) > 0) {
        const pmiDropOff = this.results?.pmiDropOffMonth;
        cards.push({
          label: 'Monthly PMI',
          prefix: '$',
          rawValue: this.results.monthlyPMI,
          isNumber: true,
          decimals: 2,
          displayValue: pmiDropOff
            ? `$${this.results.monthlyPMI.toFixed(2)} (ends payment #${pmiDropOff})`
            : undefined
        });
      }

      // Homeowner's Insurance (if applicable)
      if ((this.results?.monthlyInsurance ?? 0) > 0) {
        cards.push({
          label: "Homeowner's Insurance",
          prefix: '$',
          rawValue: this.results.monthlyInsurance,
          isNumber: true,
          decimals: 2
        });
      }

      // Loan-to-Value (if available)
      if (this.loanInfo?.ltv != null) {
        cards.push({
          label: 'Loan-to-Value (LTV)',
          rawValue: this.loanInfo.ltv * 100,
          suffix: '%',
          isNumber: true,
          decimals: 1,
          showChart: true,
          chartColor: this.loanInfo.ltv > 0.80 ? '#f59e0b' : '#10b981',
          chartLabel: 'LTV',
          percentage: this.loanInfo.ltv * 100
        });
      }

      // Down Payment (if available)
      if (this.loanInfo?.downPayment != null && this.loanInfo.downPayment > 0) {
        cards.push({
          label: 'Down Payment',
          prefix: '$',
          rawValue: this.loanInfo.downPayment,
          isNumber: true,
          decimals: 2
        });
      }

      // Total Interest
      cards.push({
        label: 'Total Interest',
        prefix: '$',
        rawValue: this.results?.totalInterest ?? 0,
        isNumber: true,
        decimals: 2,
        showChart: true,
        chartColor: '#f59e0b',
        chartLabel: 'Interest',
        percentage: parseFloat(interestPercentage)
      });

      // Total PMI Paid (if applicable)
      if ((this.results?.totalPMIPaid ?? 0) > 0) {
        cards.push({
          label: 'Total PMI Paid',
          prefix: '$',
          rawValue: this.results.totalPMIPaid,
          isNumber: true,
          decimals: 2
        });
      }

      // Total Paid
      cards.push({
        label: 'Total Paid',
        prefix: '$',
        rawValue: this.results?.totalPaid ?? 0,
        isNumber: true,
        decimals: 2
      });

      // Loan Amount
      cards.push({
        label: 'Loan Amount',
        prefix: '$',
        rawValue: this.loanInfo?.financedPrincipal ?? this.loanInfo?.principal ?? 0,
        isNumber: true,
        decimals: 2,
        showChart: this.loanInfo?.taxAmount > 0,
        chartColor: '#10b981',
        chartLabel: 'Principal',
        percentage: parseFloat(principalPercentage)
      });

      // Interest Rate
      cards.push({
        label: 'Interest Rate',
        rawValue: this.loanInfo?.annualRate ?? 0,
        suffix: '%',
        isNumber: true,
        decimals: 3
      });

      // Loan Term
      cards.push({
        label: 'Loan Term',
        displayValue: `${this.loanInfo?.years ?? 0} years`,
        isNumber: false
      });

      return cards;
    }
  },
  methods: {
    copyToClipboard() {
      const summary = `
Loan Summary:
Monthly Payment: $${this.results?.monthlyPayment?.toFixed(2) ?? '0.00'}
Total Interest: $${this.results?.totalInterest?.toFixed(2) ?? '0.00'}
Total Paid: $${this.results?.totalPaid?.toFixed(2) ?? '0.00'}
Loan Amount: $${this.loanInfo?.principal?.toFixed(2) ?? '0.00'}
Interest Rate: ${this.loanInfo?.annualRate?.toFixed(3) ?? '0.000'}%
Loan Term: ${this.loanInfo?.years ?? 0} years
      `.trim();

      navigator.clipboard.writeText(summary)
        .then(() => this.showToastNotification('Copied to clipboard!'))
        .catch(() => this.showToastNotification('Failed to copy'));
    },
    showToastNotification(message) {
      this.toastMessage = message;
      this.showToast = true;
      setTimeout(() => {
        this.showToast = false;
      }, 3000);
    }
  }
};
</script>

<style scoped>
.loan-summary {
  padding: 0;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-share {
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.btn-share:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.toast-notification {
  position: fixed;
  bottom: 32px;
  right: 32px;
  background: rgba(16, 185, 129, 0.95);
  color: #fff;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.toast-enter-active, .toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  transform: translateY(100px);
  opacity: 0;
}

.toast-leave-to {
  transform: translateY(100px);
  opacity: 0;
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .toast-notification {
    bottom: 16px;
    right: 16px;
    left: 16px;
  }
}
</style>
