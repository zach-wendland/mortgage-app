<template>
  <div class="amortization-table">
    <div class="header-section">
      <h2>Payment Schedule</h2>

      <!-- Export Options -->
      <div class="action-buttons">
        <button @click="exportToCSV" class="action-btn" title="Download CSV">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export CSV
        </button>
        <button @click="copyToClipboard" class="action-btn" title="Copy to Clipboard">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
          Copy
        </button>
      </div>
    </div>

    <!-- Search and Filter Controls -->
    <div class="controls-section">
      <div class="search-box">
        <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.35-4.35"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by payment number..."
          class="search-input"
        />
        <button v-if="searchQuery" @click="searchQuery = ''" class="clear-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <div class="filter-controls">
        <select v-model="selectedYear" class="year-filter">
          <option value="">All Years</option>
          <option v-for="year in availableYears" :key="year" :value="year">
            Year {{ year }}
          </option>
        </select>
        <button @click="toggleGrouping" class="toggle-btn" :class="{ active: groupByYear }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
          Group by Year
        </button>
      </div>
    </div>

    <!-- Amortization Chart -->
    <div class="chart-container" v-if="filteredSchedule.length > 0">
      <h3 class="chart-title">Principal vs Interest Over Time</h3>
      <div class="chart-wrapper">
        <svg class="amortization-chart" viewBox="0 0 1000 300" preserveAspectRatio="xMidYMid meet">
          <!-- Grid lines -->
          <g class="grid-lines">
            <line v-for="i in 5" :key="'h-grid-' + i"
              :x1="50" :y1="30 + (i - 1) * 60"
              :x2="980" :y2="30 + (i - 1) * 60"
              class="grid-line" />
          </g>

          <!-- Interest Area -->
          <path :d="interestAreaPath" class="interest-area" />

          <!-- Principal Area -->
          <path :d="principalAreaPath" class="principal-area" />

          <!-- Balance Line -->
          <polyline :points="balanceLinePoints" class="balance-line" />

          <!-- Y-axis labels -->
          <text v-for="(label, i) in chartYLabels" :key="'y-label-' + i"
            :x="45" :y="270 - i * 60"
            class="axis-label" text-anchor="end">
            {{ label }}
          </text>

          <!-- X-axis labels -->
          <text v-for="(label, i) in chartXLabels" :key="'x-label-' + i"
            :x="50 + (i * (930 / (chartXLabels.length - 1)))"
            y="295"
            class="axis-label" text-anchor="middle">
            {{ label }}
          </text>
        </svg>

        <div class="chart-legend">
          <div class="legend-item">
            <span class="legend-color principal"></span>
            <span>Principal</span>
          </div>
          <div class="legend-item">
            <span class="legend-color interest"></span>
            <span>Interest</span>
          </div>
          <div class="legend-item">
            <span class="legend-color balance"></span>
            <span>Balance</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Progress Indicator & Jump Navigation -->
    <div class="progress-section" v-if="!groupByYear && availableYears.length > 1">
      <div class="progress-bar-container">
        <div class="progress-bar" :style="{ width: scrollProgress + '%' }"></div>
      </div>
      <div class="jump-navigation">
        <span class="jump-label">Jump to:</span>
        <button
          v-for="year in availableYears"
          :key="'jump-' + year"
          @click="jumpToYear(year)"
          class="jump-btn"
        >
          Yr {{ year }}
        </button>
      </div>
    </div>

    <!-- Table Container with Virtual Scrolling -->
    <div class="table-wrapper" ref="tableWrapper" @scroll="handleScroll">
      <!-- Sticky Header -->
      <div class="sticky-header" :class="{ visible: isHeaderSticky }">
        <div class="header-cell">#</div>
        <div class="header-cell">Payment</div>
        <div class="header-cell">Principal</div>
        <div class="header-cell">Interest</div>
        <div class="header-cell">Balance</div>
      </div>

      <div class="glass-table-container">
        <table class="glass-table">
          <thead>
            <tr class="glow-header">
              <th scope="col">#</th>
              <th scope="col">Payment</th>
              <th scope="col">Principal</th>
              <th scope="col">Interest</th>
              <th scope="col">Balance</th>
            </tr>
          </thead>
          <tbody>
            <!-- Grouped by Year -->
            <template v-if="groupByYear">
              <template v-for="(group, yearIndex) in groupedSchedule" :key="'year-' + group.year">
                <!-- Year Header Row -->
                <tr
                  class="year-header-row"
                  @click="toggleYearExpansion(group.year)"
                  @keydown.enter="toggleYearExpansion(group.year)"
                  @keydown.space.prevent="toggleYearExpansion(group.year)"
                  :data-year="group.year"
                  role="button"
                  tabindex="0"
                  :aria-expanded="expandedYears.includes(group.year)"
                >
                  <td colspan="5" class="year-header">
                    <div class="year-header-content">
                      <svg
                        class="expand-icon"
                        :class="{ expanded: expandedYears.includes(group.year) }"
                        width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        aria-hidden="true"
                      >
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                      <span class="year-title">Year {{ group.year }}</span>
                      <span class="year-stats">
                        {{ group.payments.length }} payments
                        <span class="separator">•</span>
                        Principal: ${{ formatCurrency(group.totalPrincipal) }}
                        <span class="separator">•</span>
                        Interest: ${{ formatCurrency(group.totalInterest) }}
                      </span>
                    </div>
                  </td>
                </tr>

                <!-- Year Payment Rows -->
                <template v-if="expandedYears.includes(group.year)">
                  <tr
                    v-for="payment in group.payments"
                    :key="'payment-' + payment.paymentNumber"
                    class="payment-row"
                    :class="{
                      expanded: expandedPayment === payment.paymentNumber,
                      'last-payment': payment.paymentNumber === schedule.length
                    }"
                    @click="togglePaymentExpansion(payment.paymentNumber)"
                  >
                    <td>{{ payment.paymentNumber }}</td>
                    <td>${{ formatCurrency(payment.paymentAmount) }}</td>
                    <td class="principal-cell">${{ formatCurrency(payment.principalPayment) }}</td>
                    <td class="interest-cell">${{ formatCurrency(payment.interestPayment) }}</td>
                    <td>${{ formatCurrency(payment.remainingBalance) }}</td>
                  </tr>

                  <!-- Expanded Payment Details -->
                  <tr
                    v-if="expandedPayment === payment.paymentNumber"
                    class="detail-row"
                  >
                    <td colspan="5">
                      <div class="payment-details">
                        <div class="detail-grid">
                          <div class="detail-item">
                            <span class="detail-label">Payment Date</span>
                            <span class="detail-value">Month {{ ((payment.paymentNumber - 1) % 12) + 1 }}</span>
                          </div>
                          <div class="detail-item">
                            <span class="detail-label">Principal Ratio</span>
                            <span class="detail-value">{{ safePercentage(payment.principalPayment, payment.paymentAmount) }}%</span>
                          </div>
                          <div class="detail-item">
                            <span class="detail-label">Interest Ratio</span>
                            <span class="detail-value">{{ safePercentage(payment.interestPayment, payment.paymentAmount) }}%</span>
                          </div>
                          <div class="detail-item">
                            <span class="detail-label">Principal Paid</span>
                            <span class="detail-value">${{ formatCurrency(calculateTotalPrincipalPaid(payment.paymentNumber)) }}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </template>
            </template>

            <!-- Regular View with Virtual Scrolling -->
            <template v-else>
              <!-- Spacer for virtual scroll offset -->
              <tr v-if="virtualScrollOffset > 0" class="virtual-spacer">
                <td colspan="5" :style="{ height: virtualScrollOffset + 'px' }"></td>
              </tr>

              <!-- Visible Rows -->
              <tr
                v-for="payment in visiblePayments"
                :key="'payment-' + payment.paymentNumber"
                class="payment-row"
                :class="{
                  expanded: expandedPayment === payment.paymentNumber,
                  'last-payment': payment.paymentNumber === schedule.length
                }"
                @click="togglePaymentExpansion(payment.paymentNumber)"
              >
                <td>{{ payment.paymentNumber }}</td>
                <td>${{ formatCurrency(payment.paymentAmount) }}</td>
                <td class="principal-cell">${{ formatCurrency(payment.principalPayment) }}</td>
                <td class="interest-cell">${{ formatCurrency(payment.interestPayment) }}</td>
                <td>${{ formatCurrency(payment.remainingBalance) }}</td>
              </tr>

              <!-- Expanded Payment Details -->
              <template v-for="payment in visiblePayments" :key="'detail-' + payment.paymentNumber">
                <tr
                  v-if="expandedPayment === payment.paymentNumber"
                  class="detail-row"
                >
                  <td colspan="5">
                    <div class="payment-details">
                      <div class="detail-grid">
                        <div class="detail-item">
                          <span class="detail-label">Payment Date</span>
                          <span class="detail-value">Month {{ ((payment.paymentNumber - 1) % 12) + 1 }}</span>
                        </div>
                        <div class="detail-item">
                          <span class="detail-label">Principal Ratio</span>
                          <span class="detail-value">{{ safePercentage(payment.principalPayment, payment.paymentAmount) }}%</span>
                        </div>
                        <div class="detail-item">
                          <span class="detail-label">Interest Ratio</span>
                          <span class="detail-value">{{ safePercentage(payment.interestPayment, payment.paymentAmount) }}%</span>
                        </div>
                        <div class="detail-item">
                          <span class="detail-label">Total Principal Paid</span>
                          <span class="detail-value">${{ formatCurrency(calculateTotalPrincipalPaid(payment.paymentNumber)) }}</span>
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>

              <!-- Bottom spacer for virtual scroll -->
              <tr v-if="virtualScrollBottomSpacer > 0" class="virtual-spacer">
                <td colspan="5" :style="{ height: virtualScrollBottomSpacer + 'px' }"></td>
              </tr>
            </template>
          </tbody>
        </table>

        <!-- Loading Indicator -->
        <div v-if="isScrolling" class="scroll-indicator">
          <div class="scroll-spinner"></div>
        </div>
      </div>
    </div>

    <div class="table-info">
      <span v-if="filteredSchedule.length !== schedule.length">
        Showing {{ filteredSchedule.length }} of {{ schedule.length }} payments
      </span>
      <span v-else>
        Showing all {{ schedule.length }} payments
      </span>
    </div>

    <!-- Toast Notification -->
    <Transition name="toast">
      <div v-if="showToast" class="toast-notification" :class="toastType" role="alert" aria-live="polite" aria-atomic="true">
        <svg v-if="toastType === 'success'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>{{ toastMessage }}</span>
      </div>
    </Transition>
  </div>
</template>

<script>
export default {
  name: 'AmortizationTable',
  props: {
    schedule: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      searchQuery: '',
      selectedYear: '',
      groupByYear: false,
      expandedYears: [],
      expandedPayment: null,
      isHeaderSticky: false,
      scrollProgress: 0,

      // Virtual scrolling
      virtualScrollStart: 0,
      virtualScrollEnd: 50,
      rowHeight: 50,
      visibleRowCount: 50,
      isScrolling: false,
      scrollTimeout: null,

      // Toast
      showToast: false,
      toastMessage: '',
      toastType: 'success',
      toastTimeout: null
    };
  },
  computed: {
    availableYears() {
      const years = new Set();
      this.schedule.forEach(payment => {
        const year = Math.ceil(payment.paymentNumber / 12);
        years.add(year);
      });
      return Array.from(years).sort((a, b) => a - b);
    },

    filteredSchedule() {
      let filtered = [...this.schedule];

      // Filter by search query
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase().trim();
        filtered = filtered.filter(payment =>
          payment.paymentNumber.toString().includes(query)
        );
      }

      // Filter by year
      if (this.selectedYear) {
        filtered = filtered.filter(payment => {
          const year = Math.ceil(payment.paymentNumber / 12);
          return year === parseInt(this.selectedYear);
        });
      }

      return filtered;
    },

    groupedSchedule() {
      if (!this.groupByYear) return [];

      const groups = {};
      this.filteredSchedule.forEach(payment => {
        const year = Math.ceil(payment.paymentNumber / 12);
        if (!groups[year]) {
          groups[year] = {
            year,
            payments: [],
            totalPrincipal: 0,
            totalInterest: 0
          };
        }
        groups[year].payments.push(payment);
        groups[year].totalPrincipal += payment.principalPayment;
        groups[year].totalInterest += payment.interestPayment;
      });

      return Object.values(groups).sort((a, b) => a.year - b.year);
    },

    visiblePayments() {
      if (this.groupByYear) return [];
      return this.filteredSchedule.slice(this.virtualScrollStart, this.virtualScrollEnd);
    },

    virtualScrollOffset() {
      return this.virtualScrollStart * this.rowHeight;
    },

    virtualScrollBottomSpacer() {
      const remainingRows = this.filteredSchedule.length - this.virtualScrollEnd;
      return Math.max(0, remainingRows * this.rowHeight);
    },

    // Chart data computations
    chartDataPoints() {
      const points = this.filteredSchedule.length > 100
        ? this.sampleData(this.filteredSchedule, 50)
        : this.filteredSchedule;
      return points;
    },

    maxPayment() {
      if (this.chartDataPoints.length === 0) return 0;
      return Math.max(...this.chartDataPoints.map(p => p.paymentAmount));
    },

    maxBalance() {
      if (this.chartDataPoints.length === 0) return 0;
      return Math.max(...this.chartDataPoints.map(p => p.remainingBalance));
    },

    principalAreaPath() {
      if (this.chartDataPoints.length === 0) return '';
      const divisor = Math.max(1, this.chartDataPoints.length - 1);
      const maxPayment = this.maxPayment || 1;

      const points = this.chartDataPoints.map((p, i) => {
        const x = 50 + (i / divisor) * 930;
        const y = 270 - (p.principalPayment / maxPayment) * 240;
        return `${x},${y}`;
      });

      return `M 50,270 L ${points.join(' L ')} L 980,270 Z`;
    },

    interestAreaPath() {
      if (this.chartDataPoints.length === 0) return '';
      const divisor = Math.max(1, this.chartDataPoints.length - 1);
      const maxPayment = this.maxPayment || 1;

      const points = this.chartDataPoints.map((p, i) => {
        const x = 50 + (i / divisor) * 930;
        const principalY = 270 - (p.principalPayment / maxPayment) * 240;
        const interestY = principalY - (p.interestPayment / maxPayment) * 240;
        return { x, principalY, interestY };
      });

      const topPath = points.map(p => `${p.x},${p.interestY}`).join(' L ');
      const bottomPath = points.map(p => `${p.x},${p.principalY}`).reverse().join(' L ');

      return `M ${points[0].x},${points[0].principalY} L ${topPath} L ${bottomPath} Z`;
    },

    balanceLinePoints() {
      if (this.chartDataPoints.length === 0) return '';
      const divisor = Math.max(1, this.chartDataPoints.length - 1);
      const maxBalance = this.maxBalance || 1;

      return this.chartDataPoints.map((p, i) => {
        const x = 50 + (i / divisor) * 930;
        const y = 270 - (p.remainingBalance / maxBalance) * 240;
        return `${x},${y}`;
      }).join(' ');
    },

    chartYLabels() {
      const max = Math.max(this.maxPayment, this.maxBalance);
      return [0, 1, 2, 3, 4].map(i => {
        const value = (max / 4) * i;
        return this.formatShortCurrency(value);
      });
    },

    chartXLabels() {
      const totalPayments = this.chartDataPoints.length;
      if (totalPayments === 0) return [];

      const labelCount = Math.min(6, Math.ceil(totalPayments / 12));
      if (labelCount <= 1) return [`#1`];

      const divisor = Math.max(1, labelCount - 1);
      return Array.from({ length: labelCount }, (_, i) => {
        const paymentNum = Math.floor((i / divisor) * (totalPayments - 1)) + 1;
        return `#${paymentNum}`;
      });
    }
  },
  watch: {
    filteredSchedule() {
      this.resetVirtualScroll();
    },

    groupByYear(newVal) {
      if (newVal) {
        // Expand first year by default
        if (this.groupedSchedule.length > 0) {
          this.expandedYears = [this.groupedSchedule[0].year];
        }
      }
    }
  },
  mounted() {
    // Initialize expanded years if grouping is on
    if (this.groupByYear && this.groupedSchedule.length > 0) {
      this.expandedYears = [this.groupedSchedule[0].year];
    }
  },
  beforeUnmount() {
    // Clear all timeouts to prevent memory leaks
    if (this.scrollTimeout) {
      clearTimeout(this.scrollTimeout);
    }
    if (this.toastTimeout) {
      clearTimeout(this.toastTimeout);
    }
  },
  methods: {
    formatCurrency(value) {
      return value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    formatShortCurrency(value) {
      if (value >= 1000000) {
        return '$' + (value / 1000000).toFixed(1) + 'M';
      } else if (value >= 1000) {
        return '$' + (value / 1000).toFixed(1) + 'K';
      }
      return '$' + value.toFixed(0);
    },

    // Safe percentage calculation to avoid division by zero
    safePercentage(numerator, denominator) {
      if (!denominator || denominator === 0) return '0.0';
      return ((numerator / denominator) * 100).toFixed(1);
    },

    toggleGrouping() {
      this.groupByYear = !this.groupByYear;
      this.expandedPayment = null;
    },

    toggleYearExpansion(year) {
      const index = this.expandedYears.indexOf(year);
      if (index > -1) {
        this.expandedYears.splice(index, 1);
      } else {
        this.expandedYears.push(year);
      }
    },

    togglePaymentExpansion(paymentNumber) {
      if (this.expandedPayment === paymentNumber) {
        this.expandedPayment = null;
      } else {
        this.expandedPayment = paymentNumber;
      }
    },

    handleScroll(event) {
      const scrollTop = event.target.scrollTop;
      const scrollHeight = event.target.scrollHeight;
      const clientHeight = event.target.clientHeight;

      // Update sticky header
      this.isHeaderSticky = scrollTop > 10;

      // Update scroll progress
      const maxScroll = scrollHeight - clientHeight;
      this.scrollProgress = maxScroll > 0 ? (scrollTop / maxScroll) * 100 : 0;

      // Virtual scrolling
      if (!this.groupByYear) {
        const startIndex = Math.floor(scrollTop / this.rowHeight);
        this.virtualScrollStart = Math.max(0, startIndex - 10);
        this.virtualScrollEnd = Math.min(
          this.filteredSchedule.length,
          startIndex + this.visibleRowCount + 10
        );

        // Show scroll indicator
        this.isScrolling = true;
        clearTimeout(this.scrollTimeout);
        this.scrollTimeout = setTimeout(() => {
          this.isScrolling = false;
        }, 150);
      }
    },

    resetVirtualScroll() {
      this.virtualScrollStart = 0;
      this.virtualScrollEnd = this.visibleRowCount;
      if (this.$refs.tableWrapper) {
        this.$refs.tableWrapper.scrollTop = 0;
      }
    },

    jumpToYear(year) {
      const firstPaymentOfYear = (year - 1) * 12 + 1;
      const payment = this.filteredSchedule.find(p => p.paymentNumber >= firstPaymentOfYear);

      if (payment) {
        const index = this.filteredSchedule.indexOf(payment);
        const scrollTop = index * this.rowHeight;

        if (this.$refs.tableWrapper) {
          this.$refs.tableWrapper.scrollTo({
            top: scrollTop,
            behavior: 'smooth'
          });
        }
      }
    },

    calculateTotalPrincipalPaid(paymentNumber) {
      return this.schedule
        .slice(0, paymentNumber)
        .reduce((sum, p) => sum + p.principalPayment, 0);
    },

    sampleData(data, sampleSize) {
      if (data.length <= sampleSize) return data;

      const step = data.length / sampleSize;
      const sampled = [];
      for (let i = 0; i < sampleSize; i++) {
        const index = Math.floor(i * step);
        sampled.push(data[index]);
      }
      return sampled;
    },

    exportToCSV() {
      const headers = ['Payment #', 'Payment Amount', 'Principal', 'Interest', 'Balance'];
      const rows = this.filteredSchedule.map(p => [
        p.paymentNumber,
        p.paymentAmount.toFixed(2),
        p.principalPayment.toFixed(2),
        p.interestPayment.toFixed(2),
        p.remainingBalance.toFixed(2)
      ]);

      const csv = [
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'amortization-schedule.csv';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      this.showToastMessage('CSV exported successfully!', 'success');
    },

    async copyToClipboard() {
      const headers = ['Payment #', 'Payment Amount', 'Principal', 'Interest', 'Balance'];
      const rows = this.filteredSchedule.map(p => [
        p.paymentNumber,
        '$' + this.formatCurrency(p.paymentAmount),
        '$' + this.formatCurrency(p.principalPayment),
        '$' + this.formatCurrency(p.interestPayment),
        '$' + this.formatCurrency(p.remainingBalance)
      ]);

      const text = [
        headers.join('\t'),
        ...rows.map(row => row.join('\t'))
      ].join('\n');

      try {
        await navigator.clipboard.writeText(text);
        this.showToastMessage('Copied to clipboard!', 'success');
      } catch (err) {
        this.showToastMessage('Failed to copy to clipboard', 'error');
      }
    },

    showToastMessage(message, type = 'success') {
      this.toastMessage = message;
      this.toastType = type;
      this.showToast = true;

      clearTimeout(this.toastTimeout);
      this.toastTimeout = setTimeout(() => {
        this.showToast = false;
      }, 3000);
    }
  }
};
</script>

<style scoped>
.amortization-table {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Header Section */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

h2 {
  font-size: 1.5rem;
  color: #0f172a;
  margin: 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.action-btn:active {
  transform: translateY(0);
}

/* Controls Section */
.controls-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 250px;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 44px;
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: rgba(255, 255, 255, 1);
}

.clear-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: #e2e8f0;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-btn:hover {
  background: #cbd5e1;
}

.filter-controls {
  display: flex;
  gap: 12px;
}

.year-filter {
  padding: 10px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.9rem;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  cursor: pointer;
  transition: all 0.3s ease;
}

.year-filter:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  color: #475467;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.toggle-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* Chart Container */
.chart-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.1);
}

.chart-title {
  font-size: 1.1rem;
  color: #0f172a;
  margin-bottom: 16px;
}

.chart-wrapper {
  position: relative;
}

.amortization-chart {
  width: 100%;
  height: auto;
  overflow: visible;
}

.grid-line {
  stroke: #e2e8f0;
  stroke-width: 1;
  opacity: 0.5;
}

.interest-area {
  fill: url(#interestGradient);
  opacity: 0.7;
}

.principal-area {
  fill: url(#principalGradient);
  opacity: 0.7;
}

/* Inline SVG gradients */
.interest-area {
  fill: rgba(239, 68, 68, 0.3);
}

.principal-area {
  fill: rgba(34, 197, 94, 0.3);
}

.balance-line {
  fill: none;
  stroke: #667eea;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.axis-label {
  font-size: 11px;
  fill: #64748b;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.chart-legend {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin-top: 16px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #475467;
}

.legend-color {
  width: 24px;
  height: 12px;
  border-radius: 4px;
}

.legend-color.principal {
  background: rgba(34, 197, 94, 0.6);
}

.legend-color.interest {
  background: rgba(239, 68, 68, 0.6);
}

.legend-color.balance {
  background: #667eea;
  height: 3px;
}

/* Progress Section */
.progress-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-bar-container {
  height: 4px;
  background: rgba(226, 232, 240, 0.6);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.jump-navigation {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.jump-label {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 500;
}

.jump-btn {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.8rem;
  color: #475467;
  cursor: pointer;
  transition: all 0.2s ease;
}

.jump-btn:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* Table Wrapper */
.table-wrapper {
  position: relative;
  max-height: 600px;
  overflow-y: auto;
  overflow-x: auto;
  border-radius: 20px;
  scroll-behavior: smooth;
}

.table-wrapper::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.table-wrapper::-webkit-scrollbar-track {
  background: rgba(226, 232, 240, 0.3);
  border-radius: 10px;
}

.table-wrapper::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
}

.table-wrapper::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* Sticky Header */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: grid;
  grid-template-columns: 1fr 1.5fr 1.5fr 1.5fr 1.5fr;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
  backdrop-filter: blur(20px);
  padding: 14px 20px;
  border-radius: 16px 16px 0 0;
  opacity: 0;
  transform: translateY(-10px);
  transition: all 0.3s ease;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.sticky-header.visible {
  opacity: 1;
  transform: translateY(0);
  pointer-events: all;
}

.header-cell {
  color: white;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: right;
}

.header-cell:first-child {
  text-align: left;
}

/* Glassmorphism Table */
.glass-table-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.1);
  position: relative;
}

.glass-table {
  width: 100%;
  border-collapse: collapse;
}

.glow-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
}

.glow-header th {
  padding: 16px 20px;
  text-align: right;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
  border: none;
}

.glow-header th:first-child {
  text-align: left;
}

/* Year Header Row */
.year-header-row {
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

.year-header-row:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  box-shadow: inset 0 0 20px rgba(102, 126, 234, 0.2);
}

.year-header {
  padding: 0 !important;
}

.year-header-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  font-weight: 600;
}

.expand-icon {
  transition: transform 0.3s ease;
  color: #667eea;
  flex-shrink: 0;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.year-title {
  font-size: 1rem;
  color: #0f172a;
}

.year-stats {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 400;
  margin-left: auto;
}

.separator {
  margin: 0 8px;
  color: #cbd5e1;
}

/* Payment Rows */
.payment-row {
  transition: all 0.3s ease;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.4);
}

.payment-row:nth-child(even) {
  background: rgba(248, 250, 252, 0.6);
}

.payment-row:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  box-shadow: inset 0 0 20px rgba(102, 126, 234, 0.15),
              0 4px 12px rgba(102, 126, 234, 0.1);
  transform: translateX(4px);
}

.payment-row.expanded {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  box-shadow: inset 0 0 20px rgba(102, 126, 234, 0.2);
}

.payment-row.last-payment {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%);
  font-weight: 600;
}

.payment-row.last-payment:hover {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.25) 0%, rgba(16, 185, 129, 0.25) 100%);
}

.payment-row td {
  padding: 14px 20px;
  text-align: right;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  font-variant-numeric: tabular-nums;
  transition: all 0.3s ease;
}

.payment-row td:first-child {
  text-align: left;
  font-weight: 600;
  color: #475467;
}

.principal-cell {
  color: #059669;
  font-weight: 500;
}

.interest-cell {
  color: #dc2626;
  font-weight: 500;
}

/* Detail Row */
.detail-row {
  animation: expandDetail 0.3s ease;
}

@keyframes expandDetail {
  from {
    opacity: 0;
    transform: scaleY(0);
  }
  to {
    opacity: 1;
    transform: scaleY(1);
  }
}

.detail-row td {
  padding: 0 !important;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
}

.payment-details {
  padding: 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.detail-value {
  font-size: 1rem;
  color: #0f172a;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* Virtual Scroll Spacer */
.virtual-spacer td {
  padding: 0 !important;
  border: none !important;
}

/* Scroll Indicator */
.scroll-indicator {
  position: absolute;
  top: 50%;
  right: 30px;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 50%;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2);
}

.scroll-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Table Info */
.table-info {
  font-size: 0.85rem;
  color: #667085;
  padding: 0 4px;
}

/* Toast Notification */
.toast-notification {
  position: fixed;
  bottom: 30px;
  right: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: white;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.2);
  z-index: 1000;
  font-size: 0.95rem;
  font-weight: 500;
  backdrop-filter: blur(10px);
}

.toast-notification.success {
  color: #059669;
  border-left: 4px solid #059669;
}

.toast-notification.error {
  color: #dc2626;
  border-left: 4px solid #dc2626;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    align-items: stretch;
  }

  .action-buttons {
    width: 100%;
  }

  .action-btn {
    flex: 1;
    justify-content: center;
  }

  .controls-section {
    flex-direction: column;
  }

  .search-box {
    max-width: 100%;
  }

  .filter-controls {
    width: 100%;
    flex-direction: column;
  }

  .year-filter,
  .toggle-btn {
    width: 100%;
    justify-content: center;
  }

  .chart-container {
    padding: 16px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .year-stats {
    display: none;
  }

  .jump-navigation {
    justify-content: center;
  }

  .toast-notification {
    bottom: 20px;
    right: 20px;
    left: 20px;
  }

  .sticky-header {
    grid-template-columns: 0.8fr 1.2fr 1.2fr 1.2fr 1.2fr;
    font-size: 0.75rem;
    padding: 10px;
  }

  .header-cell {
    font-size: 0.7rem;
  }

  .payment-row td,
  .glow-header th {
    padding: 10px 12px;
    font-size: 0.85rem;
  }
}

@media (max-width: 480px) {
  .payment-row td,
  .glow-header th {
    padding: 8px 8px;
    font-size: 0.8rem;
  }

  h2 {
    font-size: 1.25rem;
  }

  .action-btn {
    font-size: 0.85rem;
    padding: 8px 12px;
  }
}
</style>
