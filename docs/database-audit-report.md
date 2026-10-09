# Study Tracker — Database Architecture, ERD & Security Audit

**Date:** 2026-10-09  
**Scope:** `~/Desktop/konkur-back` (Django 6.1 + PostgreSQL `konkur`)  
**Environment:** Local development DB (greenfield). No production reset performed.

## Stack confirmed

| Layer | Implementation |
|-------|----------------|
| Engine | PostgreSQL |
| ORM | Django ORM |
| Migrations | Django migrations (`0001_initial` + corrective `0002_*`) |
| Auth user | `accounts.User` (UUID) |
| Access helpers | `common/access.py` |

## Severity summary (pre-fix)

| Severity | Count (confirmed) | Theme |
|----------|-------------------|--------|
| Critical | 4 | Authz helpers unused/incomplete; coach note reverse leak; wallet ledger non-idempotent; dual block tables; multi-active sessions |
| High | 10+ | Tenant FK mismatches; review without relationship; XP key scope; post community visibility; soft-delete manager missing |
| Medium | 15+ | Lifecycle CHECKs, feed audience, org membership lifecycle |
| Low | 8+ | Enum string drift, denormalized counters |

## Critical findings

| ID | Issue | Models / files | Root cause | Fix status |
|----|-------|----------------|------------|------------|
| C1 | Authorization incomplete | `common/access.py` | Only 3 helpers; unused by APIs | **Fixed:** expanded helpers + regression tests |
| C2 | Coach notes reverse ORM leak | `CoachNote.student` `related_name` | Student could traverse `coach_notes_about` | **Fixed:** `related_name="+"` + soft-delete filter in helper |
| C3 | Wallet ledger not idempotent | `WalletTransaction` | No unique on reference | **Fixed:** partial unique `(wallet, kind, reference_type, reference_id)` + `idempotency_key` |
| C4 | Duplicate block tables | `accounts.UserBlock` vs `safety.BlockedUser` | Divergent privacy enforcement | **Fixed:** removed `BlockedUser`; SoT = `accounts.UserBlock` |
| C5 | Multiple concurrent live sessions | `StudySession` | No partial unique on active/paused | **Fixed:** partial unique per user when live + not deleted |

## High findings

| ID | Issue | Fix status |
|----|-------|------------|
| H1 | Soft-delete without default manager | **Fixed:** `SoftDeleteQuerySet` / `objects` / `all_objects` |
| H2 | XP idempotency key global not per-user | **Fixed:** unique `(user, idempotency_key)` |
| H3 | Community posts without community FK | **Fixed:** CHECK constraint |
| H4 | Posts default PUBLIC | **Fixed:** default `followers` |
| H5 | Feed items lack visibility snapshot | **Fixed:** `visibility_snapshot` + `dedupe_key` unique |
| H6 | `payment_transaction_id` bare UUID | **Fixed:** FK to `PaymentTransaction` |
| H7 | `study_session_id` bare UUID on integrity flags | **Fixed:** FK to `StudySession` |
| H8 | External payment ID not unique when set | **Fixed:** partial unique |
| H9 | Coach capacity unconstrained | **Fixed:** CHECK `active_student_count <= student_capacity` |
| H10 | CoachReview optional relationship | **Fixed:** relationship required |
| H11 | Org membership no active lifecycle | **Fixed:** `status` + partial unique active |
| H12 | School slug unique broken when org NULL | **Fixed:** require `organization` |
| H13 | UserRole primary without active status | **Fixed:** CHECK `is_primary` ⇒ `status=active` |
| H14 | CoachWallet CASCADE on user delete | **Fixed:** `PROTECT` |

## Tenant isolation strategy

**Chosen approach:** application-layer authorization via `common/access.py` (membership + role + relationship status filters).  
**RLS:** not enabled. Reasons: Django connection pooling / role switching, background jobs, and admin tooling need explicit `set_config` discipline; premature RLS risks silent empty results or privilege bypass via table owners.

**Limitations:** every new queryset must call helpers; ORM reverse relations can still leak if misused — mitigated for coach notes via `related_name="+"`. Cross-table school↔org consistency still relies on service validation for some assignment paths (follow-up).

## Privacy rules (enforced / documented)

1. Parent access requires **active** `ParentChildRelationship` (+ optional `ParentPermission`).
2. Revoked/pending relationships deny access immediately.
3. Coach private notes: only owning coach profile; never students/parents.
4. Coach student data: only via **active** (or explicitly paused) relationship.
5. Org admin: only membership **active** in that organization.
6. Teacher class access: `TeacherClassAssignment` ownership under teacher's school.
7. Messages: conversation participants with `left_at IS NULL`.
8. Blocks: `accounts.UserBlock` only.
9. Private posts: feed/query helpers must filter by visibility + ownership (API layer follow-up).

## Migration safety

- Corrective migrations are additive constraints/FKs on a clean local DB with seed data only.
- Before applying to a populated environment: dedupe live sessions, backfill wallet references, assign schools to organizations, attach coach reviews to relationships.
- Rollback: dropping constraints is safe; restoring `BlockedUser` would require a reverse data migration.

## Test results (executed)

```text
python manage.py test accounts study social billing common -v 2
Ran 27 tests in 11.403s
OK
```

Covered: multi-role, parent allow/deny/revoke, multi-coach, coach IDOR deny, coach note privacy, org tenant deny, teacher class deny, private feed filtering, live session uniqueness, wallet/payment/webhook/XP idempotency.

## Unresolved / follow-up

- API endpoints not yet built — IDOR still a risk until views use helpers.
- Cross-table CHECKs for teacher.school_id vs assignment.school_id (needs triggers or denormalized composite keys).
- Direct conversation pair uniqueness.
- Sender∈participants DB trigger for messages.
- Wallet balance vs ledger trigger reconciliation job.
- Partitioning of `study_sessions` / `messages` deferred until volume justifies it.
- School.organization still nullable for legacy rows; unscoped slug uniqueness added.
- CoachReview.relationship still nullable at column level but CHECK requires non-null.
