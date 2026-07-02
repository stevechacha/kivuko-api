# Kivuko la Muungano Hub — API

Django REST Framework backend for the **Kivuko la Muungano Hub** MVP (“The Union
Bridge”), matching the 5-step golden user flow in the Expo demo app.

> **Why Kivuko?** *Kivuko* means “bridge” in Swahili — the same spirit as the
> original concept, but distinct from Safaricom’s M-Pesa **Daraja** API.

## Stack

- Python 3.12+, Django 5, Django REST Framework
- SQLite (local dev) / PostgreSQL (production on Railway)
- Session-token auth via `X-Session-Token` header

## Quick start (local)

```bash
cd kivuko_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional for local SQLite
python manage.py migrate
python manage.py runserver 8000
```

Health check: `GET http://127.0.0.1:8000/health/`

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/users/register` | — | Register participant |
| POST | `/api/v1/matching/match` | token | Match Mainland ↔ Zanzibar peer |
| GET/POST | `/api/v1/missions/{id}/chat` | token | Mission chat messages |
| GET | `/api/v1/quiz/questions` | — | Union history quiz |
| POST | `/api/v1/missions/{id}/quiz/submit` | token | Submit quiz answers |
| POST | `/api/v1/certificates/generate` | token | Issue QR-verifiable certificate |
| GET | `/api/v1/certificates/verify/{code}` | — | Public certificate verification |
| GET | `/api/v1/map/stats` | — | Live union map stats + connections |
| GET | `/api/v1/audio/archive` | — | Elder oral history archive |

Authenticated requests send header: `X-Session-Token: <token from register>`.

## Deploy to Railway

### Option A — Railway dashboard (recommended)

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
2. Select this repo and set **Root Directory** to `kivuko_api`.
3. Add **PostgreSQL** to the project (Railway sets `DATABASE_URL` automatically).
4. On the **web service**, set these variables:

   | Variable | Value |
   |----------|-------|
   | `DJANGO_SECRET_KEY` | long random string |
   | `DJANGO_DEBUG` | `false` |
   | `CORS_ALLOWED_ORIGINS` | your Expo/web origins (comma-separated) |

5. Generate a **public domain** under Settings → Networking.
6. Copy the URL (e.g. `https://kivuko-api-production.up.railway.app`).

### Option B — Railway CLI

```bash
npm install -g @railway/cli
cd kivuko_api
railway login
railway init
railway add --database postgres
railway variables set DJANGO_SECRET_KEY="$(openssl rand -base64 48)" DJANGO_DEBUG=false
railway up
railway domain
```

### Connect the Expo app

```bash
# kivuko_app/.env
EXPO_PUBLIC_API_URL=https://your-service.up.railway.app
```

Then restart Expo:

```bash
cd kivuko_app
npx expo start
```

Verify production:

```bash
curl https://your-service.up.railway.app/health/
```

## Connect the mobile demo (local)

In `kivuko_app/`:

```bash
cp .env.example .env
npm install
npx expo start
```

## Admin dashboard

```bash
python manage.py createsuperuser
```

On Railway:

```bash
railway run python manage.py createsuperuser
```

Then open `https://your-service.up.railway.app/admin/`.
