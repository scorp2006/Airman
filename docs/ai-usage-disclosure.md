# AI Usage Disclosure

The assessment permits AI tools. This document discloses how AI was used, what I personally designed, and where I am most/least confident.

---

## 1. Did you use AI tools? If yes, where?

**Yes.** I used Claude (Anthropic) as a pair-programming assistant for the majority of the codebase.

AI was used in:
- Backend scaffolding (FastAPI structure, SQLAlchemy models, Pydantic schemas)
- Service-layer business rules (state machine, RBAC dependencies, audit logging helper)
- Pytest test scaffolding for the 10 required scenarios
- Frontend scaffolding (React components, Tailwind styles, React Query hooks)
- README + this disclosure document

AI was **not** used to make the design or product decisions — those came from reading the spec, planning the architecture, and choosing the visual direction. AI implemented the decisions.

---

## 2. What did AI generate?

- Boilerplate file structure across both backend and frontend
- SQLAlchemy model definitions (after I specified the table list and field-by-field requirements from spec §5)
- The `ALLOWED_TRANSITIONS` state machine dictionary in `sortie_service.py`
- Pydantic schemas mirroring the spec's data model
- Tailwind theme config and reusable component classes (`.card`, `.pill-*`, `.chip`)
- React component skeletons for the 7 screens
- The 10 pytest test bodies (after I described each required test scenario)
- API endpoint route handlers
- Seed-data dictionary

---

## 3. What did you manually review or change?

- **Read every file before submitting.** I went through each backend service and frontend component to make sure I understood the logic, not just the output.
- **Re-arranged the directory structure** to match the spec's recommended layout under `app/`.
- **Rewrote import paths and folder names** when AI suggestions drifted from spec wording.
- **Picked the visual design direction myself** — I supplied a reference dashboard I liked (Nixtio-style bento, black + lime + orange) and AI implemented within those constraints.
- **Adjusted RBAC scoping rules** — e.g., the cadet's data-level filtering (only seeing their own sorties) is not just a 403 check, it's a `WHERE cadet_id = current.id` query inside the list endpoint.
- **Wrote my own description of business rules** in the README so the explanation reflects how I think about them, not just paraphrasing.

---

## 4. Which AI-generated suggestion did you reject and why?

A few notable rejections:

1. **JWT authentication.** AI initially suggested a full JWT setup with refresh tokens. I rejected it because the spec explicitly allows mock auth and the live review favors code I can explain over code I can't. Saved ~2 hours.
2. **Per-entity schema files.** AI generated separate Pydantic files under `app/schemas/`. I consolidated them into one `schemas.py` because at this size, jumping across files is friction without benefit.
3. **Optimistic UI with rollback.** AI suggested adding optimistic React Query updates for the sortie state transitions. I rejected it for the live review — if the reviewer asks me to debug the rollback path, I want it to be straightforward.
4. **A `useSorties` custom hook layer**. AI suggested wrapping each React Query call in a custom hook. I rejected adding the abstraction because the components are already small and the indirection just adds files to read.
5. **Initial cockpit/HUD theme.** The first frontend AI built was a cyan-on-navy "military HUD" look. I rejected the direction after seeing it and asked for a redesign matching a cleaner dashboard reference (black + lime + orange with rounded bento cards).

---

## 5. Which part of the project did you personally design?

- **Overall architecture decision**: services layer holds business rules, routes are thin, audit logs are written in the same transaction as the change. AI implemented that pattern after I described it.
- **State-machine approach**: encoding allowed transitions as a Python dictionary instead of nested `if/else` chains. Easy to read, easy to change, easy to explain.
- **RBAC strategy**: two-layer enforcement — `require_roles(...)` for action-level gating + data-level `WHERE` clauses for ownership scoping. I chose this so even a logged-in instructor can't see another instructor's sorties.
- **Visual design system**: pure black background, lime green primary, orange secondary, chunky rounded cards, icon-only sidebar — chosen by me from referencing modern aviation/SaaS dashboards.
- **Test strategy**: in-memory SQLite for tests so they run in <1 second and don't touch real Postgres.
- **Seed-data narrative**: 5 sorties in 5 different statuses so the dashboard shows realistic variety immediately on first load.

---

## 6. Which part are you least confident about?

**The SQLAlchemy relationship configurations** in `app/db/models.py`, specifically the `Sortie` model where one user can be both `cadet_id` and `instructor_id` of different sorties. I configured it with `relationship("User", foreign_keys=[cadet_id])` to disambiguate, but the eager/lazy loading semantics is something I want to read up on more.

The `back_populates` between `User` and `BaseLocation` is straightforward, but I haven't memorized the difference between `back_populates` and `backref` and would need to look that up if asked in the live review.

Secondary concern: **how Pydantic v2's `model_config = ConfigDict(from_attributes=True)`** actually serializes SQLAlchemy ORM objects. It works, but I am repeating a pattern rather than fully understanding the v1 → v2 migration.

---

## 7. Pick one backend function and explain it line by line.

I'll explain **`sortie_service.release_sortie`**:

```python
def release_sortie(db: Session, actor: User, sortie_id: int) -> Sortie:
    sortie = _get_sortie(db, sortie_id)
    _check_transition(sortie.status, SortieStatus.RELEASED)

    aircraft = db.query(Aircraft).filter(Aircraft.id == sortie.aircraft_id).first()
    if aircraft.status == AircraftStatus.GROUNDED:
        raise HTTPException(
            status_code=400,
            detail="Cannot release sortie - aircraft is grounded",
        )

    old = {"status": sortie.status.value}
    sortie.status = SortieStatus.RELEASED
    aircraft.status = AircraftStatus.SCHEDULED

    write_audit(db, actor.id, "SORTIE_RELEASED", "Sortie", sortie.id,
                old_value=old, new_value={"status": sortie.status.value})
    db.commit()
    db.refresh(sortie)
    return sortie
```

- **`def release_sortie(db, actor, sortie_id)`** — receives the active DB session, the user performing the action (already validated by the route's `require_roles(DISPATCHER)` dependency), and the ID to act on.
- **`sortie = _get_sortie(db, sortie_id)`** — helper that loads the sortie or raises 404. Centralized so I don't repeat the not-found check in every function.
- **`_check_transition(sortie.status, SortieStatus.RELEASED)`** — uses the `ALLOWED_TRANSITIONS` dict to confirm SCHEDULED → RELEASED is valid. Raises 400 if not. This is the heart of the state machine.
- **Aircraft lookup + grounded check** — the spec rule: grounded aircraft cannot be released. We enforce it here, not on the frontend.
- **`old = {"status": ...}`** — capture the value *before* changing it so the audit log records the diff.
- **Two assignments** mutate the sortie and aircraft in memory. SQLAlchemy tracks the changes but doesn't issue SQL yet.
- **`write_audit(...)`** — helper that adds an AuditLog row to the session. Not yet committed.
- **`db.commit()`** — flushes both the sortie update, the aircraft update, **and** the audit insert as a single transaction. Either all three persist or none do — guaranteed atomicity.
- **`db.refresh(sortie)`** — re-reads the sortie row so the returned object has any DB-side defaults (like `updated_at`).
- **`return sortie`** — FastAPI auto-serializes it through the `SortieRead` Pydantic schema declared on the route.

---

## 8. Pick one frontend component and explain it line by line.

I'll explain **`components/StatusBadge.tsx`**:

```tsx
const COLOR: Record<string, string> = {
  SCHEDULED: "bg-bg-chip text-ink-mid border border-bg-line",
  RELEASED:  "bg-white text-black",
  AIRBORNE:  "bg-lime text-black",
  // …
};

const PULSES = new Set(["AIRBORNE", "GROUNDED", "AIRCRAFT_GROUNDED"]);

export function StatusBadge({ status, size = "sm" }) {
  const cls = COLOR[status] ?? "bg-bg-chip text-ink-mid";
  const pad = size === "md" ? "px-4 py-1.5 text-sm" : "px-3 py-1 text-xs";
  return (
    <span className={`chip ${cls} ${pad}`}>
      {PULSES.has(status) && (
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse-soft" />
      )}
      {status.replace(/_/g, " ")}
    </span>
  );
}
```

- **`COLOR` dictionary** — single source of truth for which Tailwind classes correspond to each status. Adding a new status = adding one key here. Keeps visuals consistent across the whole app.
- **`PULSES` set** — statuses that should feel "live" (airborne, grounded). Using a `Set` because membership lookup is O(1).
- **`function StatusBadge({ status, size = "sm" })`** — React function component. `size` defaults to small so most callers don't have to think about it.
- **`const cls = COLOR[status] ?? "bg-bg-chip text-ink-mid"`** — look up the colors for this status; fall back to a neutral gray if the status is unknown. The `??` operator only falls back on `null`/`undefined`, not on falsy strings.
- **`const pad = size === "md" ? ... : ...`** — branch on size to pick padding/font classes. Two sizes is enough; ternary is readable enough.
- **The JSX** — a `<span>` with classes joined by template literal. The `.chip` class comes from my Tailwind `@layer components` block in `index.css` and provides the base pill shape.
- **`{PULSES.has(status) && (…)}`** — conditional rendering: only render the pulsing dot for "live" statuses. `&&` short-circuits to `false` (which React renders as nothing) for other statuses.
- **`bg-current`** — CSS trick: the dot uses `currentColor`, so it auto-matches the badge's text color without me having to hard-code it.
- **`{status.replace(/_/g, " ")}`** — converts `TRAINING_SUBMITTED` to `TRAINING SUBMITTED` for display, but keeps the type-safe enum value internally.

---

## In summary

AI accelerated implementation, but the architecture choices (state machine in a dict, services-thin-routes pattern, two-layer RBAC, visual direction) were mine. I've read every file and am prepared to explain or modify any part of it without AI in the live review.
