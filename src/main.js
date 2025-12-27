import { createApp } from 'vue'
import App from './App.vue'
import { logError } from './utils/errorTracking.js'

const app = createApp(App)

// ============================================
// GLOBAL ERROR HANDLERS
// ============================================

// Vue error handler - catches errors in components
app.config.errorHandler = (err, instance, info) => {
  logError(err, {
    type: 'vue-error',
    component: instance?.$options?.name || instance?.$options?.__name || 'Unknown Component',
    lifecycle: info,
    props: instance?.$props
  })
}

// Global uncaught errors
window.addEventListener('error', (event) => {
  logError(event.error || new Error(event.message), {
    type: 'uncaught-error',
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno
  })
})

// Unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  const error = event.reason instanceof Error
    ? event.reason
    : new Error(String(event.reason))

  logError(error, {
    type: 'unhandled-promise-rejection',
    promise: event.promise
  })
})

// Optional: Log page visibility changes (helps debug timeout issues)
if (process.env.NODE_ENV === 'development') {
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      console.log('[errorTracking] Page hidden - timers may be throttled')
    } else {
      console.log('[errorTracking] Page visible')
    }
  })
}

app.mount('#app')
