# Nexus Hestia × Cosmic Buildings
# Backend Deploy Instructions
# api.nexushestia.com — FastAPI + Supabase + Railway
# =====================================================

## OVERVIEW

  Frontend:  cosmicbuildings.nexushestia.com  (your HTML file, static host)
  Backend:   api.nexushestia.com              (FastAPI on Railway)
  Database:  Supabase Postgres               (supabase.com)

---

## STEP 1 — SUPABASE SETUP (10 min)

1. Go to https://supabase.com → Sign in → New Project
   - Name: nexushestia-cosmic
   - Region: US West (closest to LA)
   - Password: generate a strong one, save it

2. Wait ~2 min for project to spin up

3. Go to: SQL Editor → New Query
   - Paste the entire contents of schema.sql
   - Click "Run"
   - You should see: "Success. No rows returned"

4. Get your credentials:
   - Settings → API
   - Copy "Project URL"        → this is SUPABASE_URL
   - Copy "service_role" key   → this is SUPABASE_KEY
     (NOT the anon key — use service_role for the backend)

5. Direct database access:
   - Settings → Database → Connection string
   - Copy the URI — paste into DBeaver, TablePlus, or any Postgres client
   - You can view/edit all tables directly there
   - Or use Supabase Table Editor (supabase.com dashboard) for a spreadsheet-like UI

---

## STEP 2 — GITHUB REPO (5 min)

1. Create new repo at github.com
   - Name: nexushestia-cosmic-api
   - Private: YES
   - Don't initialize with README

2. In terminal, from the nexus-api/ folder:
   git init
   git add .
   git commit -m "initial: cosmic buildings fastapi backend"
   git remote add origin https://github.com/nbajc/nexushestia-cosmic-api.git
   git push -u origin main

---

## STEP 3 — RAILWAY DEPLOY (10 min)

1. Go to https://railway.app → Sign in with GitHub

2. New Project → Deploy from GitHub repo
   - Select: nexushestia-cosmic-api
   - Railway auto-detects Python + Procfile

3. Add environment variables:
   - Go to your service → Variables tab
   - Add:
     SUPABASE_URL   = https://YOUR_PROJECT_ID.supabase.co
     SUPABASE_KEY   = your_service_role_key
     ENVIRONMENT    = production

4. Deploy triggers automatically. Watch logs for:
   "Uvicorn running on http://0.0.0.0:PORT"

5. Test it:
   - Click the generated Railway URL
   - Append /health → should return {"status":"ok"}
   - Append /docs   → FastAPI auto-generated docs (Swagger UI)

---

## STEP 4 — CUSTOM DOMAIN api.nexushestia.com (5 min)

1. In Railway: Settings → Domains → Custom Domain
   - Enter: api.nexushestia.com
   - Railway gives you a CNAME target (looks like xxx.railway.app)

2. In your DNS provider (wherever nexushestia.com DNS lives):
   - Add CNAME record:
     Name:   api
     Value:  xxx.railway.app  (from Railway)
     TTL:    300

3. Railway auto-provisions SSL certificate (~5 min propagation)

4. Verify: https://api.nexushestia.com/health

---

## STEP 5 — CONNECT FRONTEND

In cosmic-buildings-data-audit.html, update this line:
  const API_BASE = 'https://api.nexushestia.com';

That's it. All checkbox events, audit log entries, and user management
now persist to Supabase through the Railway API.

---

## API REFERENCE (quick)

  GET  /health                          → liveness check
  POST /access/check    {email}         → returns {granted, role}
  GET  /streams                         → all checked streams
  POST /streams/check   {stream_id...}  → check/update a stream
  DEL  /streams/{id}    ?email&name     → uncheck a stream
  GET  /audit           ?limit=100      → audit log
  DEL  /audit           ?admin_email    → clear log (admin only)
  GET  /users           ?admin_email    → user list (admin only)
  POST /users/invite    {email,...}     → invite new user
  POST /users/approve   {email,action} → approve/deny (admin only)

Full interactive docs: https://api.nexushestia.com/docs

---

## COSTS

  Railway:  ~$5/mo (Hobby plan, more than enough)
  Supabase: Free tier (500MB DB, 2GB bandwidth — plenty for this)
  Total:    ~$5/mo

---

## NEXT: GOOGLE OAUTH

When ready to add Google OAuth (auto-login from Chrome):
  1. Google Cloud Console → OAuth 2.0 Client ID
  2. Add to FastAPI: pip install python-jose google-auth
  3. Frontend: Google Identity Services JS SDK
  4. Replace email gate with one-click Google sign-in
  Estimated: 2 hours to implement

---
Nexus Hestia Technologies — natasha.bajc@nexushestia.com
