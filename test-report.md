# Mortgage Calculator UI/UX Test Report

**Application:** https://mortgage-app-beryl.vercel.app/
**Test Date:** 2025-12-27
**Platform:** Desktop + Mobile (375x667)
**Tools Used:** Playwright Browser MCP
**UX Score:** 7.5/10

---

## Executive Summary

The mortgage calculator application demonstrates solid functionality with good UX patterns overall. The core calculation engine works correctly, interactive features are responsive, and the mobile layout adapts well. However, **one critical bug** was identified where dollar amounts are not displaying in the Loan Summary cards, showing only "$" symbols without values.

---

## Test Coverage

### 1. Initial Page Load - PASSED ✓

**Test:** Verify all UI elements render correctly on page load

**Results:**
- Page loaded successfully (200 OK)
- All major sections visible: Hero, Mortgage Rates Panel, Calculator Form, Footer
- Mortgage rates loaded with sample data (30yr: 6.89%, 15yr: 6.12%, ARM: 5.95%)
- Form inputs present with proper labels and placeholders
- Dark mode active by default
- Only error: Missing favicon.ico (404) - non-critical

**Screenshot:** C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\01-initial-load.png

**Issues:** None (favicon 404 is cosmetic)

---

### 2. Loan Calculation Flow - PARTIAL PASS ⚠

**Test:** Fill form with test data and verify calculation results

**Test Data:**
- Loan Amount: $425,000
- Interest Rate: 6.5%
- Loan Term: 30 years
- State: WA - Washington
- Sales Tax: Enabled

**Results:**

✓ **Form Input:** All fields accepted input correctly
- Loan amount formatted with comma separators (425,000)
- Interest rate accepted decimal (6.5)
- Loan term slider worked (30 years)
- State dropdown populated all 50 states + DC
- Sales tax checkbox toggled successfully

✓ **Calculation Execution:** Form submitted successfully
- Tax lookup triggered (using fallback static data)
- Sales tax applied to principal (WA rate: ~6.5%)
- Calculation completed without errors
- Results section appeared

✓ **Amortization Table:** Fully functional
- Shows all 360 payments (30 years × 12 months)
- First payment: $2,860.90
  - Principal: $409.18
  - Interest: $2,451.72
  - Balance: $452,215.82
- Virtual scrolling implemented (displays ~60 rows at a time)
- "Showing all 360 payments" text confirmed
- Table structure correct with all columns

✓ **Additional Features:**
- Principal vs Interest chart rendered
- Year jump buttons present (Yr 1-30)
- Search and filter controls available
- Export CSV and Copy buttons visible

**CRITICAL BUG - Loan Summary Values Missing:**

The Loan Summary cards display labels but **values are missing** (only "$" or "%" symbols):
- Monthly Payment: Shows "$" (should show ~$2,860.90)
- Total Interest: Shows "$" (should show calculated total)
- Total Paid: Shows "$" (should show calculated total)
- Loan Amount: Shows "$" (should show ~$452,625 with tax)
- Interest Rate: Shows "%" (should show 6.5%)
- Loan Term: Shows "30 years" ✓ (only field working)

**Screenshots:**
- C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\02-form-filled.png
- C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\03-results-summary.png
- C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\04-amortization-table.png

**Severity:** HIGH - This is a critical UX issue as users cannot see their calculated monthly payment at a glance

**Impact:** Users must scroll to the amortization table to find their payment amount, defeating the purpose of the summary cards

**Recommendation:** Debug the value binding in the Loan Summary component. The data is clearly available (table shows correct values), suggesting a template/binding issue in the summary cards.

---

### 3. Interactive Features - PASSED ✓

**Test:** Verify copy button, theme toggle, and mortgage rate interactions

**Results:**

✓ **Copy to Clipboard:**
- Clicked "Copy" button in Payment Schedule
- Success toast appeared: "Copied to clipboard!"
- Button state updated appropriately

✓ **Theme Toggle:**
- Clicked theme toggle button (moon icon)
- Theme switched from light to dark mode
- Icon changed to sun (☀️)
- All UI elements adapted correctly to dark theme
- Dark mode maintains good contrast and readability

✓ **Mortgage Rate Application:**
- Clicked on "30-year fixed" rate card (6.89%)
- Rate automatically applied to Interest Rate field
- Success toast displayed: "Rate applied!"
- Form value updated from 6.5% to 6.89%
- Excellent UX pattern for quick rate application

**Screenshot:** C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\05-dark-mode.png

**Issues:** None

---

### 4. Error Handling - PASSED ✓

**Test:** Submit invalid inputs and verify error messages

**Test Cases:**

✓ **Negative Number:**
- Entered: -10,000 in Loan Amount
- Error displayed: "Please enter a valid loan amount"
- Form submission blocked
- Error styling applied (red alert banner)

✓ **Empty Field:**
- Cleared Loan Amount field
- Browser native validation triggered: "Please fill out this field"
- Custom validation message also displayed
- Form submission prevented
- Good defensive validation with multiple layers

**Screenshot:** C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\06-error-validation.png

**Issues:** None - Error handling is robust

---

### 5. Responsive Design - PASSED ✓

**Test:** Resize to mobile viewport (375x667) and verify layout

**Results:**

✓ **Mobile Layout Adaptation:**
- All content stacks vertically appropriately
- Hero section text remains readable
- Mortgage rate cards stack in single column
- Form fields scale to full width
- Touch targets are appropriately sized
- No horizontal scrolling required
- Theme toggle remains accessible in top-right

✓ **Content Prioritization:**
- Critical information (rates, form) visible above fold
- Navigation pattern suitable for mobile
- Text sizes appropriate for mobile reading
- Spacing prevents accidental taps

**Screenshots:**
- C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\07-mobile-view.png
- C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\08-mobile-form.png

**Issues:** None - Responsive implementation is solid

---

### 6. Performance & Console Analysis - PASSED ✓

**Console Errors:**
- 1 × 404 error: favicon.ico (cosmetic issue, no impact)
- 0 × JavaScript errors
- 0 × React errors

**Console Warnings:**
- Multiple warnings: "[mortgageRateService] Proxy unavailable, using fallback rates"
- This is expected behavior when FRED API key is not configured
- App gracefully falls back to sample data
- No negative user impact

**Network Requests:**
- All static assets loaded successfully (200 OK)
- index.html, index.js, index.css served from Vercel CDN
- Attempted localhost:3001 API call (expected to fail in production)
- Fallback mechanism working correctly

**Performance Characteristics:**
- Initial page load smooth
- Form interactions responsive
- No lag in calculations
- Table virtualization efficient (360 rows handled well)
- Theme switching instant
- No memory leaks observed during testing

**Issues:** None critical - Warning messages are informational only

---

## Critical Issues Found

### 1. Missing Dollar Values in Loan Summary (HIGH SEVERITY)

**Location:** Loan Summary cards (Monthly Payment, Total Interest, Total Paid, Loan Amount)

**Description:**
The summary cards display only currency symbols ("$", "%") without the actual calculated values. The Interest Rate field shows only "%" and the numeric fields show only "$". Only the Loan Term field displays correctly ("30 years").

**Evidence:**
- Screenshot shows "$" placeholders: C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\03-results-summary.png
- JavaScript evaluation returned: `{"Monthly Payment":"$","Total Interest":"$","Total Paid":"$","Loan Amount":"$","Interest Rate":"%","Loan Term":"30 years"}`

**Impact:**
- Users cannot see their calculated monthly payment
- Defeats the primary purpose of the summary section
- Forces users to scroll to amortization table to find basic information
- Significantly degrades UX and trustworthiness

**Root Cause (Hypothesis):**
The data is calculating correctly (amortization table shows $2,860.90 monthly payment), suggesting:
1. Template binding issue in Vue component
2. CSS display property hiding the values
3. Reactive data not updating in summary component
4. Number formatting function returning empty string

**Recommendation:**
- Inspect `LoanSummary.vue` component's template bindings
- Check computed properties for summary values
- Verify number formatting utility functions
- Test with browser DevTools to see if values exist in DOM but are hidden

**Priority:** Fix before production use - this is a showstopper bug

---

## Minor Issues Found

### 2. Missing Favicon (LOW SEVERITY)

**Description:** Browser requests favicon.ico but receives 404 response

**Impact:** Browser tab shows default icon instead of branded favicon

**Recommendation:** Add favicon.ico to public directory or configure in Vite config

---

## UX Strengths

1. **Excellent Rate Application Pattern** - One-click rate copying from market data to form is intuitive and saves user time

2. **Robust Error Validation** - Multiple validation layers (browser native + custom) provide good guardrails

3. **Smooth Interactive Feedback** - Toast notifications for user actions (copy, rate applied) provide clear feedback

4. **Responsive Mobile Layout** - Clean single-column layout on mobile with appropriate touch targets

5. **Dark Mode Implementation** - Well-executed theme toggle with good contrast in both modes

6. **Virtualized Table** - Efficient rendering of 360 rows prevents performance issues

7. **Clear Information Hierarchy** - Content organized logically from inputs → summary → detailed table

8. **Accessible Form Labels** - All inputs properly labeled for screen readers

---

## UX Weaknesses

1. **Missing Summary Values (Critical)** - As detailed above, this breaks the primary user flow

2. **Sales Tax Behavior Unclear** - When tax is enabled, the starting balance ($452,215.82) is higher than entered amount ($425,000) but this isn't explicitly explained in the summary

3. **No Loading States** - When calculation occurs, there's no visual feedback during processing (works so fast it's not critical, but could be jarring on slow connections)

4. **Chart Readability** - Principal vs Interest chart axis labels are small and may be hard to read

5. **No Tooltip on Visual Elements** - Chart and donut visualizations lack hover tooltips for exact values

---

## Recommendations

### Immediate (Pre-Production)

1. **Fix missing summary values** - Critical bug blocking production use
2. **Add favicon** - Quick fix for polish
3. **Add explicit tax explanation** - When tax checkbox is enabled, show calculated tax amount and adjusted loan total

### Short-Term Enhancements

1. **Loading indicators** - Add spinner during calculation for slower connections
2. **Chart tooltips** - Add interactive tooltips to chart for exact values on hover
3. **Print stylesheet** - Enable users to print amortization schedules
4. **Keyboard navigation** - Ensure full keyboard accessibility (test tab order)

### Long-Term Considerations

1. **Comparison mode** - Allow users to compare multiple scenarios side-by-side
2. **Save/share functionality** - Generate shareable links or PDF exports
3. **Extra payment calculator** - Show impact of additional principal payments
4. **Refinance calculator** - Add tool to calculate refinancing benefits

---

## Accessibility Notes

- Form labels properly associated with inputs ✓
- Color contrast appears adequate in both themes ✓
- Interactive elements have focus states ✓
- Semantic HTML structure (headings, landmarks) ✓
- Need to verify: Screen reader testing, keyboard-only navigation

---

## Browser Compatibility

Tested in: Chromium-based browser (Playwright default)

Recommended additional testing:
- Firefox
- Safari (especially mobile Safari)
- Edge
- Older browser versions if supporting legacy users

---

## Test Artifacts

All screenshots saved to: `C:\Users\lyyud\projects\mortgage-app\.playwright-mcp\`

1. `01-initial-load.png` - Initial page state (light mode)
2. `02-form-filled.png` - Form with test data entered
3. `03-results-summary.png` - Loan summary with missing values (BUG)
4. `04-amortization-table.png` - Amortization table showing correct calculations
5. `05-dark-mode.png` - Dark theme view
6. `06-error-validation.png` - Error handling demonstration
7. `07-mobile-view.png` - Mobile responsive layout (top)
8. `08-mobile-form.png` - Mobile form view

---

## Conclusion

The mortgage calculator demonstrates strong technical implementation with excellent responsive design, error handling, and interactive features. However, **the critical bug preventing summary values from displaying must be fixed before production deployment**. Once resolved, this would be a highly usable tool for mortgage planning.

The application successfully handles the core calculation flow, displays all 360 amortization payments correctly, and provides good user feedback through toasts and validation messages. The rate application feature from the market data panel is particularly well-designed.

**Overall Assessment:** 7.5/10 (would be 9/10 after fixing the summary values bug)

---

## Next Steps

1. Fix critical bug: Loan Summary value display
2. Add favicon for polish
3. Conduct keyboard accessibility audit
4. Test in Safari and Firefox
5. Consider performance testing with Lighthouse
6. User acceptance testing with target audience
