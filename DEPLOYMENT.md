# Deployment Guide - Mortgage Calculator

This guide covers deploying the mortgage calculator with the new backend API proxy security architecture.

## Architecture Overview

The application now uses a **two-tier architecture** for security:
- **Frontend (Vue 3)**: Runs on port 3000, contains NO API keys
- **Backend Proxy (Express)**: Runs on port 3001, securely handles all external API calls

## Prerequisites

- Node.js 16+ installed
- API keys (optional):
  - FRED API key (free from https://fred.stlouisfed.org/docs/api/api_key.html)
  - TaxJar API key (from https://www.taxjar.com/api/)

## Local Development

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Backend Proxy

Create `server/.env` from the example:

```bash
cp server/.env.example server/.env
```

Edit `server/.env` and add your API keys (optional):

```env
PORT=3001
ALLOWED_ORIGIN=http://localhost:3000

# Leave as 'static' to use hardcoded rates (no API key needed)
TAX_API_PROVIDER=static

# Only needed if TAX_API_PROVIDER=taxjar
TAXJAR_API_KEY=

# Only needed for live mortgage rates (falls back to sample data without it)
FRED_API_KEY=
```

### 3. Run Development Environment

**Option A: Run both frontend + backend together (recommended)**
```bash
npm run dev:all
```

**Option B: Run separately**

Terminal 1 (Backend Proxy):
```bash
npm run server
```

Terminal 2 (Frontend):
```bash
npm run dev
```

### 4. Access Application

- Frontend: http://localhost:3000
- Backend Proxy Health Check: http://localhost:3001/health

## Production Deployment

### Deployment Checklist

- [ ] Set `VITE_API_PROXY_URL` to your production backend URL
- [ ] Configure `server/.env` with production API keys
- [ ] Set `ALLOWED_ORIGIN` to your production frontend domain
- [ ] Build frontend: `npm run build`
- [ ] Deploy `dist/` folder to static hosting (Vercel/Netlify/etc.)
- [ ] Deploy `server/` to Node.js hosting (Render/Railway/Fly.io/etc.)
- [ ] Verify no API keys in production bundle: `grep -r "TAXJAR\|FRED_API_KEY" dist/`

### Environment Variables by Tier

**Frontend (.env)**
```env
VITE_API_PROXY_URL=https://your-backend-proxy.com
```

**Backend (server/.env)**
```env
PORT=3001
ALLOWED_ORIGIN=https://your-frontend-domain.com
TAX_API_PROVIDER=static
TAXJAR_API_KEY=your_actual_key_here
FRED_API_KEY=your_actual_key_here
```

### Recommended Hosting Platforms

#### Frontend (Static Hosting)
- **Vercel** (recommended)
  ```bash
  npm run build
  vercel --prod
  ```
  Set environment variable: `VITE_API_PROXY_URL=https://your-backend.onrender.com`

- **Netlify**
  - Build command: `npm run build`
  - Publish directory: `dist`
  - Environment: `VITE_API_PROXY_URL=https://your-backend.onrender.com`

#### Backend Proxy (Node.js Hosting)
- **Render** (recommended - free tier available)
  - Create new Web Service
  - Build command: `npm install`
  - Start command: `npm run server`
  - Add environment variables from `server/.env`

- **Railway**
  - Deploy from GitHub
  - Auto-detects Node.js
  - Add environment variables in dashboard

- **Fly.io**
  ```bash
  flyctl launch
  flyctl secrets set FRED_API_KEY=xxx TAXJAR_API_KEY=xxx
  flyctl deploy
  ```

## Security Verification

After deployment, verify security:

```bash
# Check production bundle for leaked API keys (should return nothing)
curl https://your-frontend.com | grep -i "taxjar\|fred_api_key"

# Test backend proxy health
curl https://your-backend.com/health

# Test tax rate endpoint
curl https://your-backend.com/api/tax-rate/CA

# Test mortgage rates endpoint
curl https://your-backend.com/api/mortgage-rates
```

## Troubleshooting

### Frontend shows "Proxy unavailable" errors
- Check that `VITE_API_PROXY_URL` is set correctly
- Verify backend proxy is running and accessible
- Check CORS settings in `server/api-proxy.js` (ALLOWED_ORIGIN)

### Backend returns 429 (Too Many Requests)
- Rate limit is 10 requests/minute per IP
- Increase limit in `server/api-proxy.js` line 18 if needed

### API keys still showing in production bundle
- Run: `npm run build`
- Check: `grep -r "TAXJAR\|FRED_API_KEY" dist/`
- If found: Ensure you're using `VITE_API_PROXY_URL` not `VITE_TAXJAR_API_KEY`

## Monitoring

The backend proxy logs all requests:
```
[TaxJar] Fetched rate for CA: 0.0725
[FRED] Successfully fetched 3 mortgage rates
[Static] Returning tax rate for WA: 0.065
```

Set up log monitoring on your backend hosting platform to track:
- API errors
- Rate limit hits
- Slow external API responses

## Rollback Plan

If deployment fails:

```bash
# Revert to previous commit
git revert HEAD

# Rebuild
npm run build

# Redeploy
```

## Cost Estimate

**With API Keys:**
- FRED API: Free (5,000 calls/day)
- TaxJar: $99/month (Professional plan)
- Backend Hosting: $0-7/month (Render free tier or Railway Hobby)
- Frontend Hosting: $0/month (Vercel/Netlify free tier)

**Without API Keys (Static Fallbacks):**
- Total: $0/month
- App uses hardcoded tax rates and sample mortgage rates

## Support

For issues with this deployment:
1. Check logs on backend hosting platform
2. Verify environment variables are set correctly
3. Test API proxy endpoints directly with curl
4. Check CORS configuration if frontend can't reach backend
