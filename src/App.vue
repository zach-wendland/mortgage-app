<template>
  <div id="app" :class="{ 'dark-theme': isDarkTheme }">
    <!-- Animated Background -->
    <div class="animated-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="app-shell">
      <!-- Theme Toggle Button -->
      <button class="theme-toggle" @click="toggleTheme" aria-label="Toggle theme">
        <span class="theme-icon">{{ isDarkTheme ? '☀️' : '🌙' }}</span>
      </button>

      <header class="hero glass-card">
        <div class="hero-copy">
          <p class="eyebrow">Mortgage planning toolkit</p>
          <h1 class="gradient-text">Numbers-forward amortization modeling</h1>
          <p class="intro">
            Model monthly payments, taxes, and payoff timelines with plain-language outputs.
            We added live market rates so your assumptions stay grounded in reality.
          </p>
          <ul class="hero-list">
            <li>Run what-if scenarios faster than a spreadsheet.</li>
            <li>See total interest, tax adjustments, and principle paydown.</li>
            <li>Share a readable schedule with clients or teammates.</li>
          </ul>
        </div>
        <MortgageRatesPanel
          :rates="mortgageRates"
          :loading="ratesLoading"
          :error="ratesError"
          @refresh="loadMortgageRates"
          @rate-selected="handleRateSelected"
        />
      </header>

      <section class="glass-card form-wrapper">
        <LoanInputForm
          ref="inputForm"
          :show-reset="showResults"
          @calculate="handleCalculate"
          @reset="handleReset"
        />
      </section>

      <section v-if="showResults" class="results-section">
        <div class="glass-card stagger-item" style="--stagger: 0">
          <LoanSummary :loan-info="loanInfo" :results="results" />
        </div>
        <div class="glass-card table-panel stagger-item" style="--stagger: 1">
          <AmortizationTable :schedule="schedule" />
        </div>
      </section>

      <footer v-else class="glass-card empty-state">
        <h3>Need a monthly payment fast?</h3>
        <p>
          Plug in your loan details and we will build the amortization table, blended tax impact,
          and payoff overview in one pass. No purple gradients, just numbers you can trust.
        </p>
      </footer>
    </div>
  </div>
</template>

<script>
import LoanInputForm from './components/LoanInputForm.vue';
import LoanSummary from './components/LoanSummary.vue';
import AmortizationTable from './components/AmortizationTable.vue';
import MortgageRatesPanel from './components/MortgageRatesPanel.vue';
import { computeLoanDetails } from './utils/loanProcessor.js';
import { validateInputs } from './utils/calculator.js';
import { getMortgageRates } from './services/mortgageRateService.js';

export default {
  name: 'App',
  components: {
    LoanInputForm,
    LoanSummary,
    AmortizationTable,
    MortgageRatesPanel
  },
  data() {
    return {
      showResults: false,
      loanInfo: null,
      results: null,
      schedule: [],
      mortgageRates: [],
      ratesLoading: false,
      ratesError: '',
      isDarkTheme: false
    };
  },
  created() {
    this.loadMortgageRates();
    // Load theme preference from localStorage
    const savedTheme = localStorage.getItem('mortgage-app-theme');
    if (savedTheme === 'dark') {
      this.isDarkTheme = true;
    }
  },
  methods: {
    async handleCalculate(loanData) {
      const { principal, annualRate, years } = loanData;

      const validation = validateInputs(principal, annualRate, years);
      if (!validation.isValid) {
        this.$refs.inputForm.setError(validation.error);
        return;
      }

      try {
        const { loanInfo, results, schedule } = await computeLoanDetails(loanData);
        this.loanInfo = loanInfo;
        this.results = results;
        this.schedule = schedule;
        this.showResults = true;

        this.$nextTick(() => {
          const resultsSection = document.querySelector('.results-section');
          if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        });
      } catch (error) {
        this.$refs.inputForm.setError('An error occurred while calculating. Please try again.');
        console.error('Calculation error:', error);
      }
    },
    handleReset() {
      this.showResults = false;
      this.loanInfo = null;
      this.results = null;
      this.schedule = [];
    },
    async loadMortgageRates() {
      this.ratesLoading = true;
      this.ratesError = '';
      try {
        this.mortgageRates = await getMortgageRates();
      } catch (error) {
        this.ratesError = error?.message || 'Unable to load mortgage rates.';
      } finally {
        this.ratesLoading = false;
      }
    },
    toggleTheme() {
      this.isDarkTheme = !this.isDarkTheme;
      localStorage.setItem('mortgage-app-theme', this.isDarkTheme ? 'dark' : 'light');
    },
    handleRateSelected(rateData) {
      // Extract the term years from the rate term (e.g., "30-Year Fixed" -> 30)
      const termMatch = rateData.term.match(/(\d+)-Year/);
      const years = termMatch ? parseInt(termMatch[1]) : null;

      // Apply the selected rate to the form
      if (this.$refs.inputForm) {
        this.$refs.inputForm.applyRate(rateData.rate, years);
      }
    }
  }
};
</script>

<style>
/* ===========================
   CSS CUSTOM PROPERTIES
   =========================== */
:root {
  /* Glassmorphism Design System */
  --glass-bg: rgba(255, 255, 255, 0.25);
  --glass-border: rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
  --blur-strength: 16px;

  /* Gradient Colors */
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-accent: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --gradient-mesh-1: #667eea;
  --gradient-mesh-2: #764ba2;
  --gradient-mesh-3: #f093fb;
  --gradient-mesh-4: #4facfe;

  /* Light Theme Colors */
  --bg-primary: #e8f4f8;
  --bg-gradient-1: #667eea;
  --bg-gradient-2: #4facfe;
  --bg-gradient-3: #43e97b;
  --text-primary: #0f172a;
  --text-secondary: #475467;
  --text-tertiary: #1d2939;
  --card-hover-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.25);
}

.dark-theme {
  /* Dark Theme Glassmorphism */
  --glass-bg: rgba(17, 25, 40, 0.35);
  --glass-border: rgba(255, 255, 255, 0.125);
  --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);

  /* Dark Theme Colors */
  --bg-primary: #0f172a;
  --bg-gradient-1: #4c1d95;
  --bg-gradient-2: #1e3a8a;
  --bg-gradient-3: #064e3b;
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-tertiary: #e2e8f0;
  --card-hover-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
}

/* ===========================
   GLOBAL RESETS
   =========================== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  padding: 32px 20px 60px;
  transition: background 0.4s ease, color 0.4s ease;
  overflow-x: hidden;
}

#app {
  width: 100%;
  position: relative;
}

/* ===========================
   ANIMATED GRADIENT BACKGROUND
   =========================== */
.animated-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
  background: linear-gradient(
    135deg,
    var(--bg-gradient-1),
    var(--bg-gradient-2),
    var(--bg-gradient-3)
  );
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

/* Floating Gradient Orbs */
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.8), transparent);
  top: -250px;
  left: -250px;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(79, 172, 254, 0.6), transparent);
  bottom: -200px;
  right: -200px;
  animation-delay: 5s;
  animation-duration: 25s;
}

.orb-3 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(118, 75, 162, 0.7), transparent);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 10s;
  animation-duration: 30s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(50px, -50px) scale(1.1);
  }
  66% {
    transform: translate(-50px, 50px) scale(0.9);
  }
}

/* ===========================
   THEME TOGGLE BUTTON
   =========================== */
.theme-toggle {
  position: fixed;
  top: 32px;
  right: 32px;
  z-index: 1000;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--blur-strength));
  -webkit-backdrop-filter: blur(var(--blur-strength));
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: var(--card-hover-shadow);
}

.theme-toggle:active {
  transform: translateY(0) scale(0.98);
}

.theme-icon {
  animation: iconPop 0.3s ease;
}

@keyframes iconPop {
  0% {
    transform: scale(0.8) rotate(-10deg);
    opacity: 0;
  }
  50% {
    transform: scale(1.1) rotate(5deg);
  }
  100% {
    transform: scale(1) rotate(0);
    opacity: 1;
  }
}

/* ===========================
   APP SHELL
   =========================== */
.app-shell {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
  position: relative;
  z-index: 1;
}

/* ===========================
   GLASSMORPHISM CARDS
   =========================== */
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--blur-strength));
  -webkit-backdrop-filter: blur(var(--blur-strength));
  border-radius: 32px;
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  padding: 32px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

/* Subtle glass shine effect */
.glass-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  transition: left 0.5s ease;
}

.glass-card:hover::before {
  left: 100%;
}

.glass-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--card-hover-shadow);
  border-color: rgba(255, 255, 255, 0.3);
}

/* ===========================
   HERO SECTION
   =========================== */
.hero {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  align-items: center;
  position: relative;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.eyebrow {
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-secondary);
  font-weight: 600;
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
  animation-delay: 0.2s;
}

/* Gradient Text Effect */
.gradient-text {
  font-size: 2.5rem;
  line-height: 1.2;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientTextShift 8s ease infinite, fadeInUp 0.6s ease forwards;
  animation-delay: 0s, 0.3s;
  opacity: 0;
  filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.3));
}

@keyframes gradientTextShift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.intro {
  color: var(--text-secondary);
  max-width: 520px;
  line-height: 1.6;
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
  animation-delay: 0.4s;
}

.hero-list {
  margin-left: 18px;
  color: var(--text-tertiary);
  display: flex;
  flex-direction: column;
  gap: 8px;
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
  animation-delay: 0.5s;
}

.hero-list li {
  line-height: 1.6;
  transition: transform 0.3s ease, color 0.3s ease;
}

.hero-list li:hover {
  transform: translateX(4px);
  color: #667eea;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===========================
   FORM WRAPPER
   =========================== */
.form-wrapper {
  padding: 0;
}

/* ===========================
   RESULTS SECTION WITH STAGGER
   =========================== */
.results-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stagger-item {
  opacity: 0;
  animation: staggerFadeIn 0.6s ease forwards;
  animation-delay: calc(var(--stagger) * 0.15s);
}

@keyframes staggerFadeIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.table-panel {
  padding: 24px;
}

/* ===========================
   EMPTY STATE
   =========================== */
.empty-state {
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: fadeInUp 0.6s ease forwards;
}

.empty-state h3 {
  font-size: 1.5rem;
  color: var(--text-primary);
}

.empty-state p {
  color: var(--text-secondary);
  line-height: 1.6;
}

/* ===========================
   RESPONSIVE DESIGN
   =========================== */
@media (max-width: 768px) {
  body {
    padding: 20px 12px 40px;
  }

  .theme-toggle {
    top: 20px;
    right: 20px;
    width: 48px;
    height: 48px;
    font-size: 1.25rem;
  }

  .hero {
    padding: 24px;
  }

  .glass-card {
    padding: 24px;
  }

  .gradient-text {
    font-size: 2rem;
  }

  .gradient-orb {
    filter: blur(60px);
  }

  .orb-1 {
    width: 300px;
    height: 300px;
  }

  .orb-2 {
    width: 250px;
    height: 250px;
  }

  .orb-3 {
    width: 200px;
    height: 200px;
  }
}

/* ===========================
   ACCESSIBILITY
   =========================== */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  .gradient-orb {
    animation: none;
  }

  .animated-background {
    animation: none;
  }
}

/* ===========================
   SCROLLBAR STYLING
   =========================== */
::-webkit-scrollbar {
  width: 10px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--glass-bg);
  border-radius: 10px;
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.4);
}
</style>
