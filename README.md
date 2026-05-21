# Skynet — Flight Operations Module

A mini fullstack module for **AIRMAN Aeronautics** that demonstrates a real aviation training workflow: sortie dispatch, training progress, aircraft readiness, role-based access, and audit logging.

Built for the AIRMAN Fullstack Developer Intern Technical Assessment (Advanced).

---

## 1. Project Overview

Skynet is a Flight Training Organisation operations SaaS. This module implements:

- **Sortie lifecycle** with strict state-machine transitions (SCHEDULED → RELEASED → AIRBORNE → LANDED → TRAINING_SUBMITTED → TRAINING_APPROVED → CLOSED)
- **Aircraft readiness** with auto-grounding on defect reports
- **Training progress** workflow (Instructor submits, CFI approves/rejects)
- **Role-based access** for 6 roles (ADMIN, DISPATCHER, INSTRUCTOR, CFI, CADET, MAINTENANCE_OFFICER)
- **Append-only audit logging** of every significant action
- **Operations dashboard** with live fleet status and KPIs

The frontend is a dark, modern, aviation-themed React app inspired by current operations-dashboard design trends.

---

## 2. Tech Stack

**Backend**
- Python 3.13 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · PostgreSQL 17
- Pytest with in-memory SQLite for tests

**Frontend**
- React 19 · TypeScript · Vite · Tailwind CSS · React Query · React Router · Axios

**Tooling**
- Inter, JetBrains Mono, Space Grotesk web fonts
- OpenAPI auto-generated at `/docs`

---

## 3. Setup Instructions

### Prerequisites
- Python 3.11+
- Node 18+
- PostgreSQL 14+ running locally on port 5432
- Git

### Clone

```bash
git clone <repo-url>
cd airman-fullstack-assessment
```

### Create the database

```bash
psql -U postgres -c "CREATE DATABASE skynet;"
```

(Or use pgAdmin — create a database named `skynet`.)

---

## 4. Environment Variables

Backend uses a `.env` file at `backend/.env`. A `backend/.env.example` is provided:

```dotenv
DATABASE_URL=postgresql://postgres:skynet123@localhost:5432/skynet
DEBUG=False
```

Update `DATABASE_URL` to match your local Postgres credentials.

The frontend has no required env vars — by default it talks to `http://127.0.0.1:8000`. To change, create `frontend/.env`:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

---

## 5. How to Run the Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

# Populate database with seed data
python seed.py

# Start the API
uvicorn app.main:app --reload --port 8000
```

API will be live at:
- API root: **http://127.0.0.1:8000/**
- Interactive docs: **http://127.0.0.1:8000/docs**

---

## 6. How to Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be live at **http://127.0.0.1:5173/** (or 5174 if 5173 is in use).

---

## 7. How to Run Migrations / Seed Data

This project uses SQLAlchemy's `Base.metadata.create_all()` to bootstrap the schema on first startup. Alembic was not added (see Known Limitations).

To **(re)seed** the database with starter data:

```bash
cd backend
python seed.py
```

The seed script is **idempotent** — it wipes existing rows in dependency-safe order and re-inserts a clean baseline. Output lists all login emails.

---

## 8. How to Run Tests

```bash
cd backend
venv\Scripts\python.exe -m pytest app/tests/ -v
```

10 backend tests covering all required scenarios from spec §11 should pass.

Tests use an **in-memory SQLite database** (no Postgres needed) — fast and isolated.

---

## 9. API Summary

| Method  | Endpoint                                       | Purpose                          |
| ------- | ---------------------------------------------- | -------------------------------- |
| POST    | `/auth/login`                                  | Mock login by email              |
| GET     | `/auth/me`                                     | Current user                     |
| GET     | `/users`                                       | List all users                   |
| GET     | `/users/{id}`                                  | One user                         |
| GET     | `/aircraft`                                    | List fleet                       |
| GET     | `/aircraft/{id}`                               | One aircraft                     |
| PATCH   | `/aircraft/{id}/ground`                        | Ground (MAINT)                   |
| PATCH   | `/aircraft/{id}/ready`                         | Mark ready (MAINT, no defects)   |
| POST    | `/sorties`                                     | Create sortie (DISPATCHER)       |
| GET     | `/sorties`                                     | List (role-filtered)             |
| GET     | `/sorties/{id}`                                | One sortie                       |
| PATCH   | `/sorties/{id}/release`                        | Release (DISPATCHER)             |
| PATCH   | `/sorties/{id}/airborne`                       | Mark airborne (DISPATCHER)       |
| PATCH   | `/sorties/{id}/landed`                         | Mark landed (DISPATCHER)         |
| PATCH   | `/sorties/{id}/cancel`                         | Cancel (DISPATCHER)              |
| PATCH   | `/sorties/{id}/close`                          | Close — requires CFI approval    |
| POST    | `/training-progress`                           | Submit (INSTRUCTOR)              |
| GET     | `/training-progress/{sortie_id}`               | Get for a sortie                 |
| PATCH   | `/training-progress/{id}/approve`              | Approve (CFI)                    |
| PATCH   | `/training-progress/{id}/reject`               | Reject (CFI) with remarks        |
| POST    | `/defects`                                     | File defect (MAINT/INSTRUCTOR)   |
| GET     | `/defects`                                     | List                             |
| GET     | `/defects/{id}`                                | One                              |
| PATCH   | `/defects/{id}/resolve`                        | Resolve (MAINT)                  |
| GET     | `/audit-logs`                                  | List with filters                |

Full schema with examples available at **http://127.0.0.1:8000/docs** (auto-generated OpenAPI).

---

## 10. User Roles and Permissions

| Role                  | Can do                                                                        |
| --------------------- | ----------------------------------------------------------------------------- |
| `ADMIN`               | Everything                                                                    |
| `DISPATCHER`          | Create, release, mark airborne, mark landed, cancel sorties                   |
| `INSTRUCTOR`          | Submit training progress (only for sorties they're assigned to)               |
| `CFI`                 | Approve or reject training progress; close sortie                             |
| `CADET`               | View **only their own** sorties + progress (no actions)                       |
| `MAINTENANCE_OFFICER` | Ground / mark-ready aircraft; file & resolve defects                          |

RBAC is enforced **on the backend** via `require_roles(...)` FastAPI dependencies (see `app/core/security.py`). Frontend role-gating is a UX layer only — every API still returns 403 if the wrong role hits it.

---

## 11. Business Rules Implemented

### Sortie state transitions (enforced backend-side)

```
SCHEDULED          → RELEASED, CANCELLED
RELEASED           → AIRBORNE, CANCELLED
AIRBORNE           → LANDED
LANDED             → TRAINING_SUBMITTED, AIRCRAFT_GROUNDED
TRAINING_SUBMITTED → TRAINING_APPROVED, LANDED  (rejection goes back)
TRAINING_APPROVED  → CLOSED
```

Any invalid transition raises HTTP 400 (see `sortie_service._check_transition`).

### Aircraft rules
- Grounded aircraft cannot be assigned to new sorties
- Grounded aircraft cannot be released
- Aircraft auto-becomes AIRBORNE / LANDED tracking the sortie
- Filing a defect auto-grounds the aircraft
- An aircraft can only be marked READY when it has zero OPEN defects

### Training-progress rules
- Only the **assigned instructor** of a sortie can submit progress
- Sortie must be in LANDED state at submission time
- All three scores constrained to **1-5** (validated by Pydantic `Field(ge=1, le=5)`)
- Remarks must be non-empty (Pydantic `Field(min_length=1)`)
- Only **CFI** (or ADMIN) can approve / reject
- Rejection requires a non-empty `remarks` reason; sortie moves back to LANDED for resubmission
- A sortie cannot CLOSE until training is APPROVED

### Audit rules
Every state-changing action (sortie release/airborne/landed/cancel/close, training submit/approve/reject, defect create/resolve, aircraft ground/ready) writes an `AuditLog` row in the **same DB transaction** as the change. Audit table is append-only.

---

## 12. Known Limitations

1. **No Alembic migrations.** Schema is bootstrapped via `Base.metadata.create_all()` on app start. Sufficient for assessment; in production we would use Alembic for versioned migrations and rollbacks.
2. **Mock authentication.** The spec explicitly allows this. The frontend sends `X-User-Id: <id>` on every request and the backend looks up the user. No password, no JWT, no session.
3. **No pagination.** List endpoints return up to 500 audit logs and full lists for everything else. Fine at this data size; would need pagination at scale.
4. **No Docker Compose.** Skipped to save setup time within the 24-hour window. The stack is local-first (Python venv + npm + Postgres).
5. **CORS is wide open** (`allow_origins=["*"]`). In production we'd restrict to the frontend domain.
6. **Schemas live in one file** (`app/schemas/schemas.py`) instead of per-entity files. Logically equivalent but flatter than the spec's suggested structure.
7. **No WebSocket / live updates.** React Query refetches after mutations — sufficient for the demo. Real-time would use WebSockets or Server-Sent Events.
8. **`datetime.utcnow()` deprecation warnings** in Python 3.13. Tests pass; production fix is to switch to `datetime.now(timezone.utc)`.

---

## 13. What I Would Improve With More Time

- **Alembic migrations** so schema changes are tracked in version control
- **Real JWT authentication** with refresh tokens and an HTTPS-only cookie
- **Per-route audit decorator** so writing audit becomes declarative (`@audit("SORTIE_RELEASED")`) instead of inline in each service method
- **Playwright E2E** covering the full happy path: dispatcher releases → airborne → landed → instructor submits → CFI approves → close
- **WebSocket-based live sortie board** so multiple operators see status changes without refresh
- **Pagination + server-side filtering** on the sortie board and audit log
- **Docker Compose** with three services (postgres, backend, frontend) for one-command setup
- **GitHub Actions CI** running pytest + ESLint + a build check on every push
- **Per-role onboarding tooltips** the first time a user logs in, showing what they can and can't do
- **Notification badges** in the topbar wired to recent audit events

---

## 14. AI Usage Disclosure

See [`docs/ai-usage-disclosure.md`](docs/ai-usage-disclosure.md) for full disclosure.

---

## Folder Structure

```
airman-fullstack-assessment/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entry point
│   │   ├── core/                  # config + security (mock auth + RBAC)
│   │   ├── db/                    # database setup + SQLAlchemy models
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── api/routes/            # one router per entity
│   │   ├── services/              # business rules + state machines
│   │   └── tests/                 # 10 required pytest tests
│   ├── seed.py                    # idempotent seed script
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                   # axios client + endpoint wrappers
│   │   ├── components/            # Layout, StatusBadge, Brand, Toast, …
│   │   ├── pages/                 # 7 screens
│   │   ├── context/               # AuthContext
│   │   ├── types/                 # TS interfaces mirroring backend schemas
│   │   └── App.tsx                # router + providers
│   ├── tailwind.config.js         # custom Skynet theme tokens
│   └── package.json
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   ├── ai-usage-disclosure.md
│   └── known-limitations.md
└── README.md
```

---

## Quick Demo Credentials (Seed Data)

| Role                 | Email                  |
| -------------------- | ---------------------- |
| ADMIN                | `admin@airman.in`      |
| DISPATCHER           | `dispatch@airman.in`   |
| INSTRUCTOR           | `rao@airman.in`        |
| CFI                  | `cfi@airman.in`        |
| CADET                | `arjun@airman.in`      |
| MAINTENANCE_OFFICER  | `maint@airman.in`      |

Pick any of these on the login screen to enter the console.
