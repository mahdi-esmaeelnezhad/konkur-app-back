# Study Tracker API — Endpoint Inventory

Base URL: `/api/v1`  
Auth: `Authorization: Bearer <access_token>` (JWT)  
Docs: `/api/docs/` (Swagger UI) · Schema: `/api/schema/`  
Health: `/api/health/`

## Auth — `/api/v1/auth/` (mostly public)

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/register/` | Public | Creates user + defaults + student role |
| POST | `/login/` | Public | username or email + password |
| POST | `/logout/` | User | Blacklists refresh token |
| POST | `/token/refresh/` | Public | Rotate refresh |
| POST | `/password/change/` | User | |
| POST | `/password/reset/` | Public | Always 200 (no user leak) |
| POST | `/password/reset/confirm/` | Public | |

## Me — `/api/v1/me/`

| Method | Path | Notes |
|--------|------|-------|
| GET/PATCH | `/` | Current user |
| GET/PATCH | `/profile/`, `/settings/`, `/preferences/`, `/privacy/` | |
| GET | `/roles/` | Multi-role assignments |
| GET/POST | `/devices/` · DELETE `/devices/<uuid>/` | |
| GET/POST | `/blocks/` · DELETE `/blocks/<uuid>/` | |
| POST | `/deletion-request/` | |
| GET/POST | `/consents/` | |

## Study — `/api/v1/study/`

| Method | Path | Notes |
|--------|------|-------|
| GET/POST | `/sessions/` | Manual log on POST |
| POST | `/sessions/start/` | Conflict if live session exists |
| POST | `/sessions/<uuid>/{pause,resume,complete,cancel}/` | Owner only |
| GET | `/sessions/<uuid>/events/` | |
| CRUD | `/goals/` · GET `/goal-types/` | |
| CRUD | `/plans/` · nested `/plans/<uuid>/items/` | |
| GET | `/summaries/daily/`, `/streaks/` | |
| CRUD | `/tests/` · `/tests/<uuid>/attempts/` | |
| GET/PATCH | `/focus-settings/`, `/pomodoro-settings/` | Singleton |

## Education — `/api/v1/education/`

Catalog (read): `/countries/`, `/education-systems/`, `/subjects/`, `/subject-topics/`, `/exams/`, `/exam-types/`  
Me CRUD: `/me/education-profiles/`, `/me/exam-registrations/`

## Social — `/api/v1/social/`

Posts (visibility-filtered), comments, reactions, save, feed, follows, friend-requests, friendships, communities (join/leave), challenges, leaderboard entries, XP, achievements.

## Coaching — `/api/v1/coaching/`

Public coaches, `me/coach-profile/`, students (relationship-scoped), private notes (coach-only), assignments, requests accept/decline, reviews.

## Org — `/api/v1/org/`

Parent children + summaries (relationship-gated), link requests, organizations/members (admin-scoped), schools, teacher classes.

## Messaging — `/api/v1/messaging/`

Conversations, messages (participant-gated), read markers, notifications, preferences.

## Admin — `/api/v1/admin/` (platform admin)

Users search, feature flags, audit logs.

## Billing — `/api/v1/billing/`

Public plans, `me/subscriptions/`, Stripe webhook stub (requires `Stripe-Signature`, stores event only).

## Security notes

- Object ownership enforced via querysets / `common.access` helpers.
- Client cannot set roles, XP, payment status, or session durations as trusted metrics.
- Rate limits: auth `10/min`, burst user `120/min`.
