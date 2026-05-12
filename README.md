# StrideCoach

StrideCoach is a full-stack monorepo starter for a running training tracker and AI-assisted coaching app. This foundation includes a React PWA frontend, FastAPI backend, Supabase-ready auth, imported training plans, Strava OAuth/manual activity matching, and OpenAI-powered workout analysis.

## Stack

- Frontend: React, Vite, TypeScript, TailwindCSS, shadcn/ui-style components, Recharts, vite-plugin-pwa
- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Database: Supabase Postgres
- Auth: Supabase Auth with Google OAuth as the primary provider
- Package manager: pnpm

## Structure

```text
apps/
  web/     React + Vite PWA
  api/     FastAPI service
packages/
  shared-types/  Shared TypeScript domain types
```

## Environment

Create your root env file:

```powershell
Copy-Item .env.example .env
```

Create your backend env file:

```powershell
Copy-Item apps/api/.env.example apps/api/.env
```

Set `DATABASE_URL` to your Supabase Postgres connection string:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_DATABASE_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
```

If your database password contains special characters like `@`, `#`, `%`, `/`, or `:`, URL-encode them.

Set `SUPABASE_URL` so FastAPI can verify logged-in users against Supabase's JWKS endpoint:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
```

New Supabase projects usually use asymmetric JWT signing keys, such as ECC/P-256, so the backend verifies tokens with `https://your-project-ref.supabase.co/auth/v1/.well-known/jwks.json`. `SUPABASE_JWT_SECRET` is optional and only needed if your project still issues legacy HS256 tokens.

## Run The Backend

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Then open:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Run The Frontend

```powershell
corepack enable
corepack pnpm install
corepack pnpm dev:web
```

Then open:

- Web: http://localhost:5173

## Supabase Google OAuth

Create a Supabase project, enable Google as an OAuth provider, then set:

```text
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
SUPABASE_URL=
SUPABASE_JWT_SECRET= # optional legacy HS256 fallback
```

The frontend currently stores Supabase session state and exposes Google login only. Email/password login is intentionally omitted.

The API expects the frontend to send the Supabase access token as a bearer token. On first API access, the backend upserts the authenticated user into the local `users` table.

## Strava OAuth

Create an app at Strava's developer settings, then set:

```env
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
STRAVA_REDIRECT_URI=http://localhost:8000/api/v1/strava/callback
FRONTEND_APP_URL=http://localhost:5173
```

In Strava's app settings, use this callback domain for local development:

```text
localhost
```

The backend stores Strava access and refresh tokens in `strava_connections`. For production, encrypt these tokens before launch. Recent activities can be synced and manually linked to planned workouts.

## Implemented Features

- CSV/XLSX training plan import with optional plan replacement
- Supabase Google login and user-scoped plans/workouts
- Strava OAuth, recent activity sync, and manual workout linking/unlinking
- Manual actual workout entry and notes
- OpenAI workout analysis with persisted results

## Remaining Placeholder

- `apps/api/app/api/routes/webhooks.py`: webhook receiver placeholder

## Useful Commands

```powershell
corepack pnpm lint
corepack pnpm typecheck
corepack pnpm build

cd apps/api
.\.venv\Scripts\ruff check .
```
