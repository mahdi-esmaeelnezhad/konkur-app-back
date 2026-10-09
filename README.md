# konkur-back

Backend for Study Tracker / کنکور — Django 6 + DRF + PostgreSQL + JWT.

## Quick start

```bash
cd ~/Desktop/konkur-back
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# ensure PostgreSQL DB `konkur` exists
python manage.py migrate
python manage.py seed_dev
python manage.py runserver
```

- Health: http://127.0.0.1:8000/api/health/
- Swagger: http://127.0.0.1:8000/api/docs/
- OpenAPI: http://127.0.0.1:8000/api/schema/

## Environment

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Django + JWT signing (use ≥32 bytes) |
| `DJANGO_DEBUG` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/konkur` |
| `CORS_ALLOWED_ORIGINS` | Front origins |
| `JWT_ACCESS_MINUTES` | Access token lifetime (default 30) |
| `JWT_REFRESH_DAYS` | Refresh lifetime (default 14) |

Stripe webhook verification is stubbed; set provider secrets when integrating a real PSP.

## Tests

```bash
python manage.py test accounts study social billing common org -v 2
```

## Docs

- [API endpoint inventory](docs/api-endpoint-inventory.md)
- [Database architecture](docs/database-architecture.md)
- [Database audit](docs/database-audit-report.md)

## API modules

| Prefix | Domain |
|--------|--------|
| `/api/v1/auth/` | Register, login, tokens |
| `/api/v1/me/` | Profile, privacy, devices |
| `/api/v1/study/` | Sessions, goals, plans, analytics |
| `/api/v1/education/` | Catalog + education profiles |
| `/api/v1/social/` | Feed, communities, XP |
| `/api/v1/coaching/` | Coach CRM |
| `/api/v1/org/` | Parent / school / org |
| `/api/v1/messaging/` | Chat + notifications |
| `/api/v1/admin/` | Platform admin |
| `/api/v1/billing/` | Plans + webhook stub |
