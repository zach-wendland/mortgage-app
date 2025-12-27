<template>
  <div
    :class="['summary-card', highlight ? 'highlight' : '', glass ? 'glass' : '']"
    :style="{ animationDelay: `${animationDelay}ms` }"
    @mouseenter="$emit('hover', true)"
    @mouseleave="$emit('hover', false)"
  >
    <div class="card-content">
      <div class="label">{{ label }}</div>
      <div class="value">
        <span v-if="prefix">{{ prefix }}</span>
        <animated-number
          v-if="isNumber"
          :value="rawValue"
          :decimals="decimals || 2"
          :duration="duration || 2000"
        />
        <span v-else>{{ displayValue }}</span>
        <span v-if="suffix">{{ suffix }}</span>
      </div>

      <div v-if="showChart" class="chart-container">
        <svg class="donut-chart" viewBox="0 0 100 100">
          <circle class="donut-ring" cx="50" cy="50" r="40" fill="transparent" stroke="rgba(255,255,255,0.1)" stroke-width="12" />
          <circle
            class="donut-segment"
            cx="50" cy="50" r="40"
            fill="transparent"
            :stroke="chartColor || '#10b981'"
            stroke-width="12"
            :stroke-dasharray="circleDashArray"
            :stroke-dashoffset="25"
            stroke-linecap="round"
            :style="{ animation: 'fillChart 2s ease-out forwards' }"
          />
          <text x="50" y="50" text-anchor="middle" dy="7" class="chart-text">{{ percentage }}%</text>
        </svg>
        <div class="chart-labels">
          <div class="chart-label">
            <span class="chart-dot" :style="{ background: chartColor || '#10b981' }"></span>
            {{ chartLabel }}
          </div>
        </div>
      </div>
    </div>

    <div v-if="highlight" class="gradient-overlay"></div>
    <div v-if="highlight" class="glow-effect" :class="{ pulsing: isHovered }"></div>
  </div>
</template>

<script>
import { h } from 'vue';

export default {
  name: 'LoanSummaryCard',
  components: {
    AnimatedNumber: {
      props: {
        value: { type: Number, required: true },
        decimals: { type: Number, default: 2 },
        duration: { type: Number, default: 2000 }
      },
      data() {
        return { displayValue: 0, animationFrameId: null };
      },
      computed: {
        formattedValue() {
          return this.displayValue.toFixed(this.decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        }
      },
      watch: {
        value: {
          handler(newValue) { this.animateValue(newValue); },
          immediate: true
        }
      },
      beforeUnmount() {
        if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
      },
      methods: {
        animateValue(endValue) {
          if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
          const startValue = this.displayValue || 0;
          const startTime = performance.now();
          const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / this.duration, 1);
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
      render() {
        return h('span', this.formattedValue);
      }
    }
  },
  props: {
    label: String,
    prefix: String,
    suffix: String,
    displayValue: [String, Number],
    rawValue: Number,
    isNumber: Boolean,
    decimals: Number,
    duration: Number,
    highlight: Boolean,
    glass: Boolean,
    showChart: Boolean,
    chartColor: String,
    chartLabel: String,
    percentage: Number,
    animationDelay: Number
  },
  data() {
    return {
      isHovered: false
    };
  },
  computed: {
    circleDashArray() {
      if (!this.percentage) return '0 251.2';
      const circumference = 2 * Math.PI * 40;
      const dashLength = (this.percentage / 100) * circumference;
      return `${dashLength} ${circumference}`;
    }
  }
};
</script>

<style scoped>
.summary-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  animation: slideUp 0.6s ease forwards;
  opacity: 0;
}

.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
}

.summary-card.highlight {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
  border-color: rgba(16, 185, 129, 0.3);
}

.card-content {
  position: relative;
  z-index: 1;
}

.label {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.value {
  font-size: 2rem;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.chart-container {
  margin-top: 16px;
}

.donut-chart {
  width: 100px;
  height: 100px;
  transform: rotate(-90deg);
}

.chart-text {
  font-size: 18px;
  font-weight: 700;
  fill: #fff;
  transform: rotate(90deg);
  transform-origin: center;
}

.chart-labels {
  margin-top: 8px;
  font-size: 0.875rem;
}

.chart-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.8);
}

.chart-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05), transparent);
  pointer-events: none;
}

.glow-effect {
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.4), rgba(5, 150, 105, 0.2));
  filter: blur(20px);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.glow-effect.pulsing {
  opacity: 0.6;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fillChart {
  from {
    stroke-dashoffset: 251.2;
  }
  to {
    stroke-dashoffset: 25;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.8;
  }
}
</style>
