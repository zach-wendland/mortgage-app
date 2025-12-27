/**
 * Calculate monthly payment for a loan
 * @param {number} principal - Loan amount
 * @param {number} annualRate - Annual interest rate (as percentage, e.g., 5 for 5%)
 * @param {number} years - Loan term in years
 * @returns {number} Monthly payment amount
 */
export function calculateMonthlyPayment(principal, annualRate, years) {
  const monthlyRate = annualRate / 100 / 12;
  const numberOfPayments = years * 12;

  if (annualRate === 0) {
    return principal / numberOfPayments;
  }

  const monthlyPayment = principal *
    (monthlyRate * Math.pow(1 + monthlyRate, numberOfPayments)) /
    (Math.pow(1 + monthlyRate, numberOfPayments) - 1);

  return monthlyPayment;
}

/**
 * Calculate total amount paid over life of loan
 * @param {number} monthlyPayment - Monthly payment amount
 * @param {number} years - Loan term in years
 * @returns {number} Total amount paid
 */
export function calculateTotalPaid(monthlyPayment, years) {
  return monthlyPayment * years * 12;
}

/**
 * Calculate total interest paid over life of loan
 * @param {number} totalPaid - Total amount paid
 * @param {number} principal - Original loan amount
 * @returns {number} Total interest paid
 */
export function calculateTotalInterest(totalPaid, principal) {
  return totalPaid - principal;
}

/**
 * Generate complete amortization schedule
 * @param {number} principal - Loan amount
 * @param {number} annualRate - Annual interest rate (as percentage)
 * @param {number} years - Loan term in years
 * @param {number} monthlyPayment - Monthly payment amount
 * @returns {Array} Array of payment objects
 */
export function generateAmortizationSchedule(principal, annualRate, years, monthlyPayment) {
  const monthlyRate = annualRate / 100 / 12;
  const numberOfPayments = years * 12;
  let remainingBalance = principal;
  const schedule = [];

  for (let i = 1; i <= numberOfPayments; i++) {
    const interestPayment = remainingBalance * monthlyRate;
    let principalPayment;
    let actualPayment;

    if (i === numberOfPayments) {
      // FINAL PAYMENT ADJUSTMENT
      // Adjust to exactly zero out the balance regardless of accumulated rounding
      principalPayment = remainingBalance;
      actualPayment = principalPayment + interestPayment;
      remainingBalance = 0;

      schedule.push({
        paymentNumber: i,
        paymentAmount: actualPayment,        // May differ slightly from regular payment
        principalPayment: principalPayment,  // Exact remaining balance
        interestPayment: interestPayment,
        remainingBalance: 0
      });
    } else {
      // REGULAR PAYMENT
      principalPayment = monthlyPayment - interestPayment;
      remainingBalance -= principalPayment;

      schedule.push({
        paymentNumber: i,
        paymentAmount: monthlyPayment,
        principalPayment: principalPayment,
        interestPayment: interestPayment,
        remainingBalance: Math.max(0, remainingBalance)  // Prevent negative display
      });
    }
  }

  return schedule;
}

/**
 * Validate loan inputs
 * @param {number} principal - Loan amount
 * @param {number} annualRate - Annual interest rate
 * @param {number} years - Loan term in years
 * @returns {Object} Validation result with isValid flag and error message
 */
export function validateInputs(principal, annualRate, years) {
  if (!principal || principal <= 0) {
    return { isValid: false, error: 'Loan amount must be greater than 0' };
  }

  if (annualRate === null || annualRate === undefined || annualRate < 0) {
    return { isValid: false, error: 'Interest rate must be 0 or greater' };
  }

  if (!years || years <= 0) {
    return { isValid: false, error: 'Loan term must be greater than 0' };
  }

  if (principal > 100000000) {
    return { isValid: false, error: 'Loan amount seems too large' };
  }

  if (annualRate > 100) {
    return { isValid: false, error: 'Interest rate seems too high' };
  }

  if (years > 50) {
    return { isValid: false, error: 'Loan term seems too long' };
  }

  return { isValid: true, error: null };
}

/**
 * Calculate Loan-to-Value ratio
 * @param {number} loanAmount - Loan amount
 * @param {number} propertyValue - Property value
 * @returns {number} LTV as decimal (e.g., 0.85 for 85%)
 */
export function calculateLTV(loanAmount, propertyValue) {
  if (!propertyValue || propertyValue <= 0) return 0;
  return loanAmount / propertyValue;
}

/**
 * Calculate monthly PMI payment
 * @param {number} loanAmount - Original loan amount
 * @param {number} annualPMIRate - Annual PMI rate as decimal (e.g., 0.008 for 0.8%)
 * @returns {number} Monthly PMI payment
 */
export function calculateMonthlyPMI(loanAmount, annualPMIRate) {
  if (!annualPMIRate || annualPMIRate <= 0) return 0;
  return (loanAmount * annualPMIRate) / 12;
}

/**
 * Find payment number where PMI drops off (LTV <= 78%)
 * @param {Array} schedule - Amortization schedule
 * @param {number} propertyValue - Property value
 * @returns {number|null} Payment number when PMI ends, or null if never
 */
export function calculatePMIDropOff(schedule, propertyValue) {
  if (!propertyValue || propertyValue <= 0) return null;

  const targetBalance = propertyValue * 0.78; // 78% LTV threshold

  const dropOffPayment = schedule.find(payment =>
    payment.remainingBalance <= targetBalance
  );

  return dropOffPayment ? dropOffPayment.paymentNumber : null;
}

/**
 * Calculate total PMI paid until drop-off
 * @param {number} monthlyPMI - Monthly PMI amount
 * @param {number} dropOffMonth - Payment number when PMI ends
 * @returns {number} Total PMI paid
 */
export function calculateTotalPMI(monthlyPMI, dropOffMonth) {
  if (!dropOffMonth || monthlyPMI <= 0) return 0;
  return monthlyPMI * dropOffMonth;
}
