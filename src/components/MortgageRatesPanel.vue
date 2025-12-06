<template>
  <section class="rates-panel">
    <!-- Animated border gradient overlay -->
    <div class="border-gradient"></div>

    <div class="panel-header">
      <div>
        <p class="eyebrow">Market snapshot</p>
        <h3>Live mortgage rates</h3>
      </div>

      <div class="header-actions">
        <!-- Rate Alert Bell -->
        <button
          class="alert-btn"
          type="button"
          :class="{ 'has-alert': hasActiveAlert }"
          @click="showAlertModal = true"
          title="Set rate alert"
          aria-label="Set rate alert"
        >
          <svg class="bell-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          <span v-if="hasActiveAlert" class="alert-badge"></span>
        </button>

        <!-- Refresh Button with Auto-refresh Progress -->
        <button
          class="refresh-btn"
          type="button"
          :disabled="loading"
          @click="handleRefresh"
          title="Refresh rates"
          aria-label="Refresh rates"
        >
          <svg
            class="refresh-icon"
            :class="{ 'spinning': loading }"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            aria-hidden="true"
          >
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
          </svg>
          <svg class="progress-ring" viewBox="0 0 36 36">
            <circle
              class="progress-ring-circle"
              :style="{ strokeDashoffset: progressOffset }"
              cx="18"
              cy="18"
              r="16"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Auto-refresh countdown -->
    <div v-if="!loading && !error && autoRefreshEnabled" class="refresh-countdown">
      <span class="countdown-text">Next update in {{ Math.ceil(timeUntilRefresh / 1000) }}s</span>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading" class="skeleton-container">
      <div
        v-for="i in 3"
        :key="i"
        class="skeleton-item"
        :style="{ animationDelay: `${i * 0.1}s` }"
      >
        <div class="skeleton-meta">
          <div class="skeleton-line skeleton-term"></div>
          <div class="skeleton-line skeleton-timestamp"></div>
        </div>
        <div class="skeleton-line skeleton-rate"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="panel-state error">
      {{ error }}
    </div>

    <!-- Rate List -->
    <ul v-else class="rate-list">
      <li
        v-for="(rate, index) in displayRates"
        :key="rate.term"
        class="rate-item"
        :class="{
          'selected': selectedRate === rate.term,
          'rate-up': getRateChange(rate) > 0,
          'rate-down': getRateChange(rate) < 0
        }"
        @click="applyRate(rate)"
        :style="{ animationDelay: `${index * 0.1}s` }"
      >
        <div class="rate-meta">
          <div class="term-row">
            <p class="term">{{ rate.term }}</p>

            <!-- Rate Change Indicator -->
            <span v-if="getRateChange(rate) !== 0" class="rate-change">
              <svg v-if="getRateChange(rate) > 0" class="trend-arrow" viewBox="0 0 12 12">
                <path d="M6 2 L6 10 M6 2 L2 6 M6 2 L10 6" stroke="currentColor" fill="none" stroke-width="2"/>
              </svg>
              <svg v-else class="trend-arrow" viewBox="0 0 12 12">
                <path d="M6 10 L6 2 M6 10 L2 6 M6 10 L10 6" stroke="currentColor" fill="none" stroke-width="2"/>
              </svg>
              <span class="change-value">{{ Math.abs(getRateChange(rate)).toFixed(2) }}%</span>
            </span>
          </div>

          <p class="timestamp" v-if="rate.asOf && rate.asOf !== 'Sample data'">
            Updated {{ formatDate(rate.asOf) }}
          </p>

          <!-- Rate Comparison Badge -->
          <div class="comparison-badge" :class="getComparisonClass(rate)">
            <span class="badge-text">{{ getComparisonText(rate) }}</span>
          </div>
        </div>

        <div class="rate-right">
          <!-- Mini Sparkline Chart -->
          <svg class="sparkline" viewBox="0 0 60 24" preserveAspectRatio="none">
            <defs>
              <linearGradient :id="`gradient-${index}`" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" :style="{ stopColor: getSparklineColor(rate), stopOpacity: 0.3 }"/>
                <stop offset="100%" :style="{ stopColor: getSparklineColor(rate), stopOpacity: 0.05 }"/>
              </linearGradient>
            </defs>
            <path
              class="sparkline-fill"
              :d="generateSparklinePath(rate, true)"
              :fill="`url(#gradient-${index})`"
            />
            <path
              class="sparkline-line"
              :d="generateSparklinePath(rate, false)"
              :stroke="getSparklineColor(rate)"
            />
          </svg>

          <!-- Animated Rate Value -->
          <p class="rate-value">
            <span class="animated-number">{{ animatedRate(rate) }}</span>
            <span class="percent">%</span>
          </p>
        </div>

        <!-- Click hint -->
        <div class="click-hint">Click to apply</div>
      </li>
    </ul>

    <p class="panel-foot">
      Source: {{ (rates[0] && rates[0].source) || 'Sample data' }}
    </p>

    <!-- Toast Notification -->
    <transition name="toast">
      <div v-if="showToast" class="toast-notification" role="alert" aria-live="polite" aria-atomic="true">
        <svg class="toast-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
        </svg>
        <span>Rate applied!</span>
      </div>
    </transition>

    <!-- Alert Modal -->
    <transition name="modal">
      <div v-if="showAlertModal" class="modal-overlay" @click.self="showAlertModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h4>Set Rate Alert</h4>
            <button class="modal-close" @click="showAlertModal = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6L18 18M6 18L18 6"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <p class="modal-description">
              Get notified when rates drop below your threshold. We'll check every hour and alert you.
            </p>

            <div class="form-group">
              <label for="alert-type">Rate Type</label>
              <select id="alert-type" v-model="alertForm.rateType">
                <option value="">Select rate type</option>
                <option v-for="rate in rates" :key="rate.term" :value="rate.term">
                  {{ rate.term }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label for="alert-threshold">Alert when below (%)</label>
              <input
                id="alert-threshold"
                v-model.number="alertForm.threshold"
                type="number"
                step="0.01"
                placeholder="e.g., 6.50"
              />
            </div>

            <div class="form-group">
              <label for="alert-email">Email (optional)</label>
              <input
                id="alert-email"
                v-model="alertForm.email"
                type="email"
                placeholder="your@email.com"
              />
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="showAlertModal = false">Cancel</button>
            <button class="btn-primary" @click="setAlert">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
              Set Alert
            </button>
          </div>
        </div>
      </div>
    </transition>
  </section>
</template>

<script>
export default {
  name: 'MortgageRatesPanel',
  props: {
    rates: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      displayRates: [],
      previousRates: {},
      selectedRate: null,
      showToast: false,
      showAlertModal: false,
      hasActiveAlert: false,
      alertForm: {
        rateType: '',
        threshold: null,
        email: ''
      },
      autoRefreshEnabled: true,
      timeUntilRefresh: 60000, // 60 seconds
      refreshInterval: null,
      countdownInterval: null,
      animationFrames: {},
      animationFrameIds: {},
      toastTimeout: null
    };
  },
  computed: {
    progressOffset() {
      const circumference = 2 * Math.PI * 16;
      const progress = this.timeUntilRefresh / 60000;
      return circumference * (1 - progress);
    }
  },
  watch: {
    rates: {
      handler(newRates) {
        if (newRates && newRates.length > 0) {
          this.updateRates(newRates);
        }
      },
      immediate: true,
      deep: true
    },
    loading(isLoading) {
      if (!isLoading) {
        this.resetAutoRefresh();
      }
    }
  },
  mounted() {
    this.resetAutoRefresh();
  },
  beforeUnmount() {
    this.clearIntervals();
    // Clear toast timeout
    if (this.toastTimeout) {
      clearTimeout(this.toastTimeout);
    }
    // Cancel all animation frames
    Object.values(this.animationFrameIds).forEach(id => {
      if (id) cancelAnimationFrame(id);
    });
  },
  methods: {
    formatRate(value) {
      if (typeof value !== 'number' || Number.isNaN(value)) {
        return '--';
      }
      return value.toFixed(2);
    },

    formatDate(dateString) {
      try {
        const date = new Date(dateString);
        return date.toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
      } catch (error) {
        return dateString;
      }
    },

    updateRates(newRates) {
      // Store previous rates for comparison
      this.displayRates.forEach(rate => {
        this.previousRates[rate.term] = rate.rate;
      });

      // Animate numbers counting up
      newRates.forEach(rate => {
        const oldRate = this.previousRates[rate.term] || rate.rate;
        this.animateNumber(rate.term, oldRate, rate.rate);
      });

      this.displayRates = newRates;
    },

    animateNumber(term, start, end) {
      // Cancel any existing animation for this term
      if (this.animationFrameIds[term]) {
        cancelAnimationFrame(this.animationFrameIds[term]);
      }

      const duration = 1000; // 1 second
      const startTime = Date.now();

      const animate = () => {
        const now = Date.now();
        const progress = Math.min((now - startTime) / duration, 1);
        const easeProgress = this.easeOutCubic(progress);
        const current = start + (end - start) * easeProgress;

        // Vue 3: use direct assignment instead of this.$set
        this.animationFrames[term] = current;

        if (progress < 1) {
          this.animationFrameIds[term] = requestAnimationFrame(animate);
        } else {
          this.animationFrameIds[term] = null;
        }
      };

      this.animationFrameIds[term] = requestAnimationFrame(animate);
    },

    easeOutCubic(t) {
      return 1 - Math.pow(1 - t, 3);
    },

    animatedRate(rate) {
      const animated = this.animationFrames[rate.term];
      if (animated !== undefined) {
        return animated.toFixed(2);
      }
      return this.formatRate(rate.rate);
    },

    getRateChange(rate) {
      const previous = this.previousRates[rate.term];
      if (previous === undefined) return 0;
      return rate.rate - previous;
    },

    getComparisonClass(rate) {
      const avg = this.getAverageRate();
      const diff = rate.rate - avg;

      if (diff < -0.1) return 'excellent';
      if (diff < 0) return 'good';
      if (diff < 0.1) return 'average';
      return 'high';
    },

    getComparisonText(rate) {
      const avg = this.getAverageRate();
      const diff = rate.rate - avg;

      if (diff < -0.1) return 'Excellent rate';
      if (diff < 0) return 'Good rate';
      if (diff < 0.1) return 'Average';
      return 'Above average';
    },

    getAverageRate() {
      if (this.displayRates.length === 0) return 0;
      const sum = this.displayRates.reduce((acc, r) => acc + (r.rate || 0), 0);
      return sum / this.displayRates.length;
    },

    getSparklineColor(rate) {
      const change = this.getRateChange(rate);
      if (change > 0) return '#ef4444'; // red for up
      if (change < 0) return '#10b981'; // green for down
      return '#6366f1'; // indigo for neutral
    },

    generateSparklinePath(rate, filled = false) {
      // Generate realistic 7-day trend data
      const points = this.generateTrendData(rate.rate);
      const width = 60;
      const height = 24;
      const max = Math.max(...points);
      const min = Math.min(...points);
      const range = max - min || 1;

      let path = '';

      points.forEach((value, i) => {
        const x = (i / (points.length - 1)) * width;
        const y = height - ((value - min) / range) * height;

        if (i === 0) {
          path += `M ${x} ${y}`;
        } else {
          path += ` L ${x} ${y}`;
        }
      });

      if (filled) {
        path += ` L ${width} ${height} L 0 ${height} Z`;
      }

      return path;
    },

    generateTrendData(currentRate) {
      // Generate 7 data points with realistic variation
      const points = [];
      let rate = currentRate - 0.1; // Start slightly lower

      for (let i = 0; i < 7; i++) {
        rate += (Math.random() - 0.5) * 0.05; // Random walk
        points.push(Math.max(0, rate));
      }

      // Ensure last point is close to current rate
      points[6] = currentRate;

      return points;
    },

    applyRate(rate) {
      this.selectedRate = rate.term;

      // Emit event to parent to fill the form
      this.$emit('rate-selected', {
        rate: rate.rate,
        term: rate.term
      });

      // Show toast notification
      this.showToast = true;
      if (this.toastTimeout) {
        clearTimeout(this.toastTimeout);
      }
      this.toastTimeout = setTimeout(() => {
        this.showToast = false;
        this.selectedRate = null;
      }, 2000);
    },

    handleRefresh() {
      this.clearIntervals();
      this.$emit('refresh');
    },

    resetAutoRefresh() {
      this.clearIntervals();
      this.timeUntilRefresh = 60000;

      this.countdownInterval = setInterval(() => {
        this.timeUntilRefresh -= 1000;

        if (this.timeUntilRefresh <= 0) {
          if (this.autoRefreshEnabled && !this.loading) {
            this.$emit('refresh');
          }
          this.timeUntilRefresh = 60000;
        }
      }, 1000);
    },

    clearIntervals() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
      }
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
      }
    },

    setAlert() {
      if (!this.alertForm.rateType || !this.alertForm.threshold) {
        return;
      }

      this.hasActiveAlert = true;
      this.showAlertModal = false;

      // In a real app, this would call an API

      // Reset form
      this.alertForm = {
        rateType: '',
        threshold: null,
        email: ''
      };
    }
  }
};
</script>

<style scoped>
/* Glassmorphism Panel */
.rates-panel {
  position: relative;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 24px;
  border: 1px solid rgba(228, 231, 236, 0.5);
  padding: 28px;
  box-shadow:
    0 20px 60px rgba(15, 23, 42, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset,
    0 8px 16px rgba(99, 102, 241, 0.05);
  min-width: 280px;
  overflow: hidden;
  animation: floatIn 0.6s ease-out;
}

/* Animated border gradient */
.border-gradient {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(
    135deg,
    #6366f1,
    #8b5cf6,
    #ec4899,
    #f59e0b,
    #10b981,
    #06b6d4,
    #6366f1
  );
  background-size: 300% 300%;
  border-radius: 24px;
  z-index: -1;
  opacity: 0.15;
  animation: gradientShift 8s ease infinite;
  filter: blur(8px);
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes floatIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Panel Header */
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.eyebrow {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #475467;
  margin-bottom: 4px;
}

h3 {
  font-size: 1.25rem;
  color: #0f172a;
  margin: 0;
  font-weight: 700;
}

/* Alert Bell Button */
.alert-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border: 1px solid #e4e7ec;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.alert-btn:hover {
  background: #f8fafc;
  border-color: #6366f1;
  transform: scale(1.05);
}

.alert-btn.has-alert {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-color: #6366f1;
}

.bell-icon {
  width: 18px;
  height: 18px;
  color: #475467;
  transition: color 0.3s ease;
}

.alert-btn.has-alert .bell-icon {
  color: white;
  animation: ringBell 0.5s ease;
}

@keyframes ringBell {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-15deg); }
  75% { transform: rotate(15deg); }
}

.alert-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  background: #ef4444;
  border: 2px solid white;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

/* Refresh Button with Progress Ring */
.refresh-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border: 1px solid #d0d5dd;
  background: rgba(248, 250, 252, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn:not(:disabled):hover {
  background: #0f172a;
  border-color: #0f172a;
  transform: scale(1.05);
}

.refresh-btn:not(:disabled):hover .refresh-icon {
  color: #ffffff;
}

.refresh-icon {
  width: 18px;
  height: 18px;
  color: #475467;
  transition: all 0.3s ease;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-ring {
  position: absolute;
  width: 36px;
  height: 36px;
  transform: rotate(-90deg);
  pointer-events: none;
}

.progress-ring-circle {
  fill: none;
  stroke: #6366f1;
  stroke-width: 2;
  stroke-dasharray: 100.53;
  stroke-dashoffset: 0;
  transition: stroke-dashoffset 1s linear;
  stroke-linecap: round;
}

/* Refresh Countdown */
.refresh-countdown {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.countdown-text {
  font-size: 0.75rem;
  color: #6366f1;
  font-weight: 600;
}

/* Loading Skeleton */
.skeleton-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 12px 0;
}

.skeleton-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: linear-gradient(
    90deg,
    rgba(248, 250, 252, 0.8) 0%,
    rgba(241, 245, 249, 0.8) 50%,
    rgba(248, 250, 252, 0.8) 100%
  );
  background-size: 200% 100%;
  border-radius: 16px;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.skeleton-line {
  background: rgba(203, 213, 225, 0.4);
  border-radius: 8px;
  height: 16px;
}

.skeleton-term {
  width: 80px;
  height: 20px;
}

.skeleton-timestamp {
  width: 120px;
}

.skeleton-rate {
  width: 70px;
  height: 32px;
}

/* Error State */
.panel-state.error {
  color: #b42318;
  background: rgba(254, 243, 242, 0.9);
  border: 1px solid #fecdca;
  border-radius: 14px;
  padding: 16px;
  font-size: 0.9rem;
  margin: 8px 0;
}

/* Rate List */
.rate-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
}

/* Rate Item with Click Effect */
.rate-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.9));
  border: 1px solid rgba(228, 231, 236, 0.6);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: slideIn 0.4s ease-out backwards;
  overflow: hidden;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.rate-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.08));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.rate-item:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow:
    0 12px 24px rgba(15, 23, 42, 0.1),
    0 0 0 1px rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.3);
}

.rate-item:hover::before {
  opacity: 1;
}

.rate-item:active {
  transform: translateY(0) scale(0.98);
}

.rate-item.selected {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
  border-color: #6366f1;
  box-shadow:
    0 8px 16px rgba(99, 102, 241, 0.2),
    0 0 0 2px rgba(99, 102, 241, 0.3);
}

/* Rate Up/Down Animations */
.rate-item.rate-up .rate-value {
  color: #ef4444;
  animation: rateUp 0.6s ease;
}

.rate-item.rate-down .rate-value {
  color: #10b981;
  animation: rateDown 0.6s ease;
}

@keyframes rateUp {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

@keyframes rateDown {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(4px); }
}

/* Rate Meta */
.rate-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  z-index: 1;
}

.term-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.term {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

/* Rate Change Indicator */
.rate-change {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
}

.rate-item.rate-up .rate-change {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.rate-item.rate-down .rate-change {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.trend-arrow {
  width: 10px;
  height: 10px;
}

.change-value {
  font-size: 0.7rem;
}

.timestamp {
  font-size: 0.75rem;
  color: #667085;
  margin: 0;
}

/* Comparison Badge */
.comparison-badge {
  display: inline-flex;
  padding: 3px 8px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 700;
  width: fit-content;
}

.comparison-badge.excellent {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}

.comparison-badge.good {
  background: rgba(34, 197, 94, 0.15);
  color: #16a34a;
}

.comparison-badge.average {
  background: rgba(99, 102, 241, 0.15);
  color: #6366f1;
}

.comparison-badge.high {
  background: rgba(239, 68, 68, 0.15);
  color: #dc2626;
}

/* Rate Right Section */
.rate-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  z-index: 1;
}

/* Sparkline */
.sparkline {
  width: 60px;
  height: 24px;
  opacity: 0.7;
  transition: opacity 0.3s ease;
}

.rate-item:hover .sparkline {
  opacity: 1;
}

.sparkline-line {
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sparkline-fill {
  opacity: 0.6;
}

/* Animated Rate Value */
.rate-value {
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0;
  color: #0f172a;
  transition: color 0.3s ease;
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.animated-number {
  font-variant-numeric: tabular-nums;
}

.percent {
  font-size: 1.2rem;
  font-weight: 700;
  opacity: 0.7;
}

/* Click Hint */
.click-hint {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 0.65rem;
  color: #6366f1;
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.3s ease;
  font-weight: 600;
  pointer-events: none;
}

.rate-item:hover .click-hint {
  opacity: 1;
  transform: translateY(0);
}

/* Panel Footer */
.panel-foot {
  font-size: 0.75rem;
  color: #98a2b3;
  margin-top: 16px;
  text-align: center;
}

/* Toast Notification */
.toast-notification {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border-radius: 16px;
  box-shadow:
    0 12px 28px rgba(16, 185, 129, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  font-weight: 600;
  font-size: 0.95rem;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.toast-icon {
  width: 22px;
  height: 22px;
}

.toast-enter-active, .toast-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px) scale(0.9);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 24px;
  max-width: 480px;
  width: 100%;
  box-shadow:
    0 24px 48px rgba(15, 23, 42, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px;
  border-bottom: 1px solid #e4e7ec;
}

.modal-header h4 {
  font-size: 1.35rem;
  color: #0f172a;
  margin: 0;
  font-weight: 700;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(248, 250, 252, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: #f1f5f9;
  transform: rotate(90deg);
}

.modal-close svg {
  width: 18px;
  height: 18px;
  color: #475467;
}

.modal-body {
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-description {
  color: #475467;
  line-height: 1.6;
  margin: 0;
  font-size: 0.95rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #0f172a;
  font-weight: 600;
  font-size: 0.9rem;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px 16px;
  font-size: 1rem;
  border: 1px solid #d0d5dd;
  border-radius: 12px;
  transition: all 0.3s ease;
  background: #fcfdff;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 20px 28px;
  background: #f8fafc;
  border-top: 1px solid #e4e7ec;
}

.btn-secondary,
.btn-primary {
  flex: 1;
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-secondary {
  background: white;
  color: #475467;
  border: 1px solid #d0d5dd;
}

.btn-secondary:hover {
  background: #f8fafc;
  border-color: #94a3b8;
}

.btn-primary {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}

.btn-icon {
  width: 18px;
  height: 18px;
}

.modal-enter-active, .modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9) translateY(20px);
}

/* Responsive */
@media (max-width: 640px) {
  .rates-panel {
    padding: 20px;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .rate-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .rate-right {
    width: 100%;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .sparkline {
    order: 1;
  }

  .rate-value {
    font-size: 1.5rem;
  }

  .modal-content {
    margin: 20px;
  }

  h3 {
    font-size: 1.1rem;
  }
}
</style>
