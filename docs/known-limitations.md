# Known Limitations

## Authentication
- **Mock auth** via `X-User-Id` header. Spec explicitly allowed this.
- No password, JWT, or session. Anyone with knowledge of a valid user id can act as that user.
- Real production: switch to OAuth2 / JWT with refresh-token rotation.

## Database
- **Schema bootstrap via `Base.metadata.create_all()`** instead of Alembic migrations. Fine for dev / assessment; not safe for production schema evolution.
- **No foreign-key cascade deletes** configured. If you delete a base, related users will still hold the stale `base_id`.

## Testing
- **Tests use in-memory SQLite**, not Postgres. SQLAlchemy abstracts the dialect difference, but a small risk exists that something Postgres-specific (e.g., ENUM behavior) could pass in SQLite and fail in Postgres. Mitigation: end-to-end smoke testing against the real Postgres locally before submission.

## Frontend
- **No pagination.** Audit log is hard-capped at 500 rows server-side. Other lists return everything.
- **No optimistic UI.** Mutations show a small disabled state but the table only updates after the server returns.
- **CORS is wide open** (`allow_origins=["*"]`). Production: restrict to known frontend origins.

## Operational
- **No Docker Compose.** The README's setup steps assume Python, Node, and Postgres are installed on the host.
- **No CI/CD.** No GitHub Actions; tests must be run manually.
- **No structured logging.** Backend uses default uvicorn access logs only.

## Deprecations
- `datetime.utcnow()` is deprecated in Python 3.13. Tests pass but emit warnings. Production fix: switch every call site to `datetime.now(timezone.utc)`.
