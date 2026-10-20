# Deploying AgentFlow with HTTPS

This guide puts the frontend on **Vercel** and the API on **Render**, with a hosted Postgres
and Qdrant. Both hosts issue and renew HTTPS certificates automatically, so you never handle
certificates yourself. The same steps work on Railway, Fly.io or Netlify with small changes.

## How it fits together

```
Browser --HTTPS--> Vercel (React app)
                     |  /api/*  is proxied by Vercel to the backend
                     v
                   Render (FastAPI) --> Postgres   (accounts, reports, runs, document list)
                                    --> Qdrant     (document search vectors)
                                    --> user's own LLM / Tavily / PostgreSQL (keys sent per request)
```

The browser only ever talks to **one origin** (your Vercel domain). Vercel forwards `/api/*` to
Render. This matters for login: the session cookie is first-party, so it works in Safari and with
third-party-cookie blocking, and no CORS is needed.

## What protects users

| Protection | Where |
|---|---|
| HTTPS everywhere, HTTP redirected to HTTPS | Vercel and Render (automatic) plus `SecurityMiddleware` |
| HSTS (browsers refuse plain HTTP afterwards) | Vercel `vercel.json` and the API in production |
| Session cookie: `HttpOnly`, `Secure`, `SameSite=Lax`, `__Host-` prefix | `ENVIRONMENT=production` |
| Passwords stored only as salted scrypt hashes | `auth_service.py` |
| Session tokens stored only as SHA-256 hashes; logout revokes instantly | `app_sessions` table |
| CSRF: unsafe requests must come from `ALLOWED_ORIGINS` | `AuthMiddleware` |
| Login throttling: per IP and per account lockout | rate limiter and `routes/auth.py` |
| Each user sees only their own documents, runs, reports | `owner_id` filters on every query |
| Content-Security-Policy, X-Frame-Options, no-store caching | `vercel.json` and the API |
| API docs (`/docs`) hidden | `ENVIRONMENT=production` |
| Server refuses unsafe settings | startup check |

## 1. Create the databases

**Postgres (app data).** Create one on Neon, Supabase or Render. Copy its connection string and
make sure it ends with `?ssl=require` (asyncpg's spelling; Neon's default `sslmode=require` is
not accepted). Then, from `backend/`, apply the migrations:

```bash
DATABASE_URL="postgresql://USER:PASSWORD@HOST/DB?ssl=require" PYTHONPATH=. python migrations/apply.py
```

Migrations are tracked in a `schema_migrations` table: each file runs once, in order, in its own
transaction, under a lock so two deploys can't collide. Run it with `--status` to see what is
pending. `render.yaml` runs it automatically before every deploy (`preDeployCommand`).

**Demo database (optional).** Create a second, empty Postgres database, then:

```bash
DEMO_DATABASE_URL="postgresql://USER:PASSWORD@HOST/DEMO_DB?ssl=require" PYTHONPATH=. python demo/seed_demo_db.py
```

Leave `DEMO_DATABASE_URL` unset to hide the demo option in Settings.

**Qdrant (document search).** Create a free cluster at cloud.qdrant.io. Copy its URL and API key.

## 2. Deploy the API on Render

1. Push the repo to GitHub, then in Render choose **New > Blueprint** and select the repo.
   `render.yaml` defines the service.
2. Fill in the secrets Render asks for:
   - `DATABASE_URL`: the app Postgres string from step 1
   - `QDRANT_URL` and `QDRANT_API_KEY`
   - `DEMO_DATABASE_URL`: optional
   - `ALLOWED_ORIGINS`: your Vercel URL, e.g. `https://agentflow.vercel.app` (you can set this
     after step 3, then redeploy)
3. Deploy. Check `https://YOUR-API.onrender.com/health` returns `{"status":"ok"}`.

The blueprint already sets `ENVIRONMENT=production`, `TRUST_PROXY_HEADERS=true`,
`ALLOW_PRIVATE_HOSTS=false`, `REQUIRE_CUSTOMER_DB=true`, `REQUIRE_USER_LLM_KEY=true` and the mock
toggles to `false`. In production the API **will not start** if `ALLOW_PRIVATE_HOSTS=true`.

Note: with `REQUIRE_USER_LLM_KEY=true` every user must add their own LLM key in Settings before
research works. That is deliberate, so your server never pays for anyone's usage.

## 3. Deploy the frontend on Vercel

1. In `frontend/vercel.json`, replace `REPLACE-WITH-YOUR-BACKEND.onrender.com` with your Render
   hostname.
2. In Vercel choose **Add New > Project**, import the repo, set the **Root Directory** to
   `frontend`, and deploy. Vite settings are detected automatically.
3. Copy the resulting URL into Render's `ALLOWED_ORIGINS`, and redeploy the API.

If you attach a custom domain, add that domain to `ALLOWED_ORIGINS` too (comma-separated).

## 4. Verify it end to end

Open your Vercel URL, then:

- [ ] The padlock shows, and `http://` redirects to `https://`.
- [ ] You can create an account and sign in; refreshing keeps you signed in.
- [ ] Browser DevTools > Application > Cookies shows `__Host-agentflow_session` with **HttpOnly**
      and **Secure** ticked.
- [ ] Signing out, then pressing Back, shows the sign-in page, not your data.
- [ ] A second account sees none of the first account's documents or reports.
- [ ] `https://YOUR-API.onrender.com/docs` returns 404.
- [ ] Response headers on the site include `strict-transport-security` and
      `content-security-policy`.
- [ ] In Settings, add an LLM key and press **Save and test**; then run a research question.

## Operating it

- **Logs** are single-line JSON in production, one line per request with `request_id`, method,
  path, status and duration. Every response carries an `X-Request-ID` header, so when a user
  reports a problem, ask for that ID (or the one in a 500 error body) and search the logs for it.
  Request bodies, headers, cookies and query strings are never logged.
- **Probes:** `GET /health` is liveness (no I/O). `GET /ready` checks Postgres and Qdrant and
  returns 503 when either is down; point a load balancer at it if you want traffic withheld from
  an instance that has lost its database.
- **Errors** return `{"detail": "Internal server error.", "request_id": "..."}`; the stack trace
  stays in the server log. Validation errors never echo what the user submitted.
- **Shutdown** is orderly: in-flight research runs get a few seconds to finish, then are
  cancelled and marked failed; database and Qdrant connections are closed.
- **CI** (`.github/workflows/ci.yml`) lints, runs the tests, builds the frontend, and scans both
  dependency trees for known vulnerabilities on every push and pull request.
- **Dependencies are pinned.** `backend/requirements.txt` is generated from `requirements.in`;
  to upgrade, re-resolve it, run the tests in a clean virtualenv, and commit both files.
- **Docker.** `backend/Dockerfile` builds a non-root image for platforms that run containers
  (Fly, Cloud Run, a VPS). It reads `$PORT`, exposes `/health` as its health check, and is meant to
  sit behind the platform's load balancer. It has not been built in this repo's test runs.

## Things to know

- **Render's free tier sleeps** after inactivity; the first request wakes it (about a minute). The
  paid `starter` plan in `render.yaml` stays awake.
- **Rate limits are per server process.** One instance is fine; with several instances, move the
  limiter to a shared store such as Redis.
- **No password reset or email verification.** A user who forgets their password cannot recover the
  account. Add an email provider before opening it to the public.
- **Running a research job lives in server memory.** If Render restarts the service mid-run, that
  run is marked failed; finished reports are safe in Postgres.
- **Rotate secrets** you used while developing (database passwords, API keys), and never commit `.env`.
