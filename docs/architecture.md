# Architecture

## High-level

```
┌──────────────────┐         HTTP / JSON          ┌──────────────────────┐
│  React Frontend  │ ───────────────────────────▶ │   FastAPI Backend    │
│   (Vite, TS)     │ ◀─────────────────────────── │  (Pydantic, SQLAlc.) │
└──────────────────┘                              └──────────┬───────────┘
                                                             │
                                                             ▼
                                                    ┌──────────────────┐
                                                    │   PostgreSQL 17  │
                                                    └──────────────────┘
```

## Backend layers

```
api/routes/  ←  thin HTTP handlers, request validation, role-guarding
services/    ←  business rules, state machine, audit writes (the brain)
db/          ←  SQLAlchemy ORM models + session factory
schemas/     ←  Pydantic models for request/response
core/        ←  config, mock auth, RBAC dependency factory
```

Routes are intentionally thin — they parse input, call a service, return the result. All business logic lives in services so it can be tested in isolation and reasoned about without HTTP context.

## State machine

The sortie state machine is encoded as a single dictionary:

```python
ALLOWED_TRANSITIONS = {
    SortieStatus.SCHEDULED: {SortieStatus.RELEASED, SortieStatus.CANCELLED},
    SortieStatus.RELEASED:  {SortieStatus.AIRBORNE, SortieStatus.CANCELLED},
    SortieStatus.AIRBORNE:  {SortieStatus.LANDED},
    ...
}
```

`_check_transition(current, target)` raises HTTP 400 on any unknown transition. Adding a new state means adding one row.

## RBAC

Two layers:

1. **Action-level** — `require_roles(...)` FastAPI dependency. Returns 403 if the user's role isn't in the allowed set. ADMIN bypasses all checks.
2. **Data-level** — inside list endpoints we filter rows. CADET only sees `cadet_id == self.id`; INSTRUCTOR only sees `instructor_id == self.id`.

This means even within an allowed action, a user can only act on their own data.

## Audit log

Every state-changing service function calls `write_audit(...)` which adds a row to `audit_logs`. The audit insert is part of the same transaction as the change — atomic by construction.

## Frontend layers

```
api/        ←  axios client + endpoint wrappers (one function per endpoint)
context/    ←  AuthContext: who is logged in, login/logout
components/ ←  reusable: StatusBadge, Layout, PageHeader, Toast, Icons
pages/      ←  one component per route (7 screens)
types/      ←  TypeScript interfaces mirroring backend schemas
```

React Query handles all server state (caching, refetching, invalidation). After a mutation, we invalidate the relevant query keys and the UI refreshes automatically.

## Deployment story (not yet implemented)

In production:
- Backend behind a reverse proxy (nginx) with TLS
- Postgres on a managed service (RDS / Supabase)
- Frontend built (`npm run build`) and served as static files
- Secrets via environment variables, never committed
- Real authentication via JWT or session cookies
