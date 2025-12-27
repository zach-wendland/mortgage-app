// Error Tracking Utility
// Captures errors in localStorage and optionally sends to remote endpoint

const ERROR_STORAGE_KEY = 'app_errors';
const MAX_STORED_ERRORS = 50;

/**
 * Log an error to localStorage and optionally to a remote endpoint
 * @param {Error} error - The error object
 * @param {Object} context - Additional context (component name, user action, etc.)
 */
export function logError(error, context = {}) {
  const errorLog = {
    timestamp: new Date().toISOString(),
    message: error?.message || 'Unknown error',
    stack: error?.stack || null,
    context,
    userAgent: navigator.userAgent,
    url: window.location.href,
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight
    }
  };

  // Store in localStorage
  try {
    const errors = JSON.parse(localStorage.getItem(ERROR_STORAGE_KEY) || '[]');
    errors.push(errorLog);

    // Keep only last 50 errors
    const trimmedErrors = errors.slice(-MAX_STORED_ERRORS);
    localStorage.setItem(ERROR_STORAGE_KEY, JSON.stringify(trimmedErrors));
  } catch (storageError) {
    console.warn('[errorTracking] Failed to store error in localStorage:', storageError);
  }

  // Log to console for development
  console.error('[Error Tracked]', errorLog);

  // Optional: Send to remote endpoint (future enhancement)
  const remoteEndpoint = import.meta.env.VITE_ERROR_ENDPOINT;
  if (remoteEndpoint) {
    sendToRemote(remoteEndpoint, errorLog);
  }

  return errorLog;
}

/**
 * Send error to remote logging endpoint
 * @param {string} endpoint - Remote endpoint URL
 * @param {Object} errorLog - Error log object
 */
async function sendToRemote(endpoint, errorLog) {
  try {
    await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(errorLog)
    });
  } catch (err) {
    // Silent fail - don't throw errors from error tracking
    console.warn('[errorTracking] Failed to send error to remote:', err);
  }
}

/**
 * Get all stored errors from localStorage
 * @returns {Array} Array of error logs
 */
export function getStoredErrors() {
  try {
    return JSON.parse(localStorage.getItem(ERROR_STORAGE_KEY) || '[]');
  } catch (err) {
    console.warn('[errorTracking] Failed to retrieve errors:', err);
    return [];
  }
}

/**
 * Clear all stored errors
 */
export function clearStoredErrors() {
  try {
    localStorage.removeItem(ERROR_STORAGE_KEY);
  } catch (err) {
    console.warn('[errorTracking] Failed to clear errors:', err);
  }
}

/**
 * Get errors from a specific time range
 * @param {number} hoursAgo - Number of hours to look back
 * @returns {Array} Filtered error logs
 */
export function getRecentErrors(hoursAgo = 24) {
  const cutoffTime = new Date(Date.now() - hoursAgo * 60 * 60 * 1000).toISOString();
  return getStoredErrors().filter(error => error.timestamp >= cutoffTime);
}

/**
 * Get error statistics
 * @returns {Object} Error statistics
 */
export function getErrorStats() {
  const errors = getStoredErrors();
  const recentErrors = getRecentErrors(24);

  // Group by error message
  const errorGroups = {};
  errors.forEach(error => {
    const key = error.message || 'Unknown';
    errorGroups[key] = (errorGroups[key] || 0) + 1;
  });

  return {
    total: errors.length,
    last24Hours: recentErrors.length,
    mostCommon: Object.entries(errorGroups)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([message, count]) => ({ message, count })),
    oldestError: errors[0]?.timestamp || null,
    newestError: errors[errors.length - 1]?.timestamp || null
  };
}

/**
 * Export errors as downloadable JSON file
 */
export function exportErrors() {
  const errors = getStoredErrors();
  const dataStr = JSON.stringify(errors, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });

  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `error-log-${new Date().toISOString().split('T')[0]}.json`;
  link.click();

  URL.revokeObjectURL(url);
}
