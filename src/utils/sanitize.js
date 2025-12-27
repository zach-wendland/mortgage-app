// Input Sanitization Utilities
// Prevents XSS, SQL injection, and other input-based attacks

/**
 * Sanitize numeric input (principal, rate, years)
 * @param {string|number} value - Raw input value
 * @param {Object} options - Validation options
 * @returns {number|null} - Sanitized number or null if invalid
 */
export function sanitizeNumber(value, { min = 0, max = Infinity, allowDecimals = true } = {}) {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  // Convert to string and remove any HTML tags
  const cleaned = String(value).replace(/<[^>]*>/g, '');

  // Remove all non-numeric characters except decimal point and minus sign
  const numericOnly = cleaned.replace(/[^\d.-]/g, '');

  // Parse to float or int
  const parsed = allowDecimals ? parseFloat(numericOnly) : parseInt(numericOnly, 10);

  // Validate
  if (isNaN(parsed) || !isFinite(parsed)) {
    return null;
  }

  // Clamp to range
  return Math.max(min, Math.min(max, parsed));
}

/**
 * Sanitize string input (state codes, user-provided text)
 * @param {string} value - Raw input value
 * @param {Object} options - Validation options
 * @returns {string} - Sanitized string
 */
export function sanitizeString(value, { maxLength = 1000, allowedChars = null } = {}) {
  if (value === null || value === undefined) {
    return '';
  }

  // Convert to string and remove HTML tags
  let cleaned = String(value).replace(/<[^>]*>/g, '');

  // Remove script tags and event handlers (defense in depth)
  cleaned = cleaned
    .replace(/<script[^>]*>.*?<\/script>/gi, '')
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
    .replace(/javascript:/gi, '');

  // Apply allowed characters filter if provided
  if (allowedChars) {
    const regex = new RegExp(`[^${allowedChars}]`, 'g');
    cleaned = cleaned.replace(regex, '');
  }

  // Trim and limit length
  return cleaned.trim().slice(0, maxLength);
}

/**
 * Sanitize state code input (2-letter uppercase)
 * @param {string} value - Raw state code
 * @returns {string} - Sanitized 2-letter uppercase state code
 */
export function sanitizeStateCode(value) {
  const cleaned = sanitizeString(value, {
    maxLength: 2,
    allowedChars: 'A-Za-z'
  });
  return cleaned.toUpperCase();
}

/**
 * Sanitize boolean input (checkbox values)
 * @param {any} value - Raw boolean value
 * @returns {boolean} - Sanitized boolean
 */
export function sanitizeBoolean(value) {
  // Handle various truthy/falsy representations
  if (typeof value === 'boolean') {
    return value;
  }

  const str = String(value).toLowerCase().trim();
  return str === 'true' || str === '1' || str === 'yes' || str === 'on';
}

/**
 * Sanitize loan form data
 * @param {Object} formData - Raw form data
 * @returns {Object} - Sanitized form data
 */
export function sanitizeLoanForm(formData) {
  return {
    principal: sanitizeNumber(formData.principal, {
      min: 0,
      max: 100000000, // $100M max
      allowDecimals: true
    }),
    annualRate: sanitizeNumber(formData.annualRate, {
      min: 0,
      max: 100, // 100% max rate
      allowDecimals: true
    }),
    years: sanitizeNumber(formData.years, {
      min: 1,
      max: 50, // 50 years max
      allowDecimals: false
    }),
    state: formData.state ? sanitizeStateCode(formData.state) : '',
    includeSalesTax: sanitizeBoolean(formData.includeSalesTax)
  };
}

/**
 * Escape HTML entities for safe display
 * @param {string} unsafe - Unsafe string
 * @returns {string} - HTML-escaped string
 */
export function escapeHtml(unsafe) {
  if (typeof unsafe !== 'string') {
    return '';
  }

  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Validate URL to prevent SSRF attacks
 * @param {string} url - URL to validate
 * @param {Array<string>} allowedDomains - Whitelist of allowed domains
 * @returns {boolean} - True if URL is safe
 */
export function isUrlSafe(url, allowedDomains = []) {
  try {
    const parsed = new URL(url);

    // Only allow http and https protocols
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return false;
    }

    // Check against allowed domains if provided
    if (allowedDomains.length > 0) {
      return allowedDomains.some(domain => parsed.hostname.endsWith(domain));
    }

    return true;
  } catch {
    return false;
  }
}
