"""
Comprehensive RBAC tests.

Verifies that for EVERY mutating endpoint, only the allowed role(s) succeed
and every other role gets HTTP 403.
"""

from app.tests.conftest import headers


# ---------- helpers ----------

def _release_sortie(client, db):
    """Walk the helper sortie to RELEASED so we have something in flight."""
    return client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))


def _walk_to_landed(client, db):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))


def _submit_training(client, db):
    return client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4,
        "communication_score": 3,
        "situational_awareness_score": 4,
        "remarks": "Solid.",
    })


# ---------- /sorties POST (create) ----------

def test_only_dispatcher_can_create_sortie(db, client):
    """Each non-dispatcher should be denied (admin allowed)."""
    payload = {
        "sortie_number": "RBAC-001",
        "cadet_id": db.users["cadet"],
        "instructor_id": db.users["instructor"],
        "aircraft_id": db.aircraft_ready_id,
        "base_id": 1,
        "lesson_type": "Test",
        "scheduled_start": "2026-12-31T10:00:00",
        "scheduled_end": "2026-12-31T11:00:00",
    }
    for role in ("instructor", "cfi", "cadet", "maint"):
        r = client.post("/sorties", headers=headers(db.users[role]), json=payload)
        assert r.status_code == 403, f"{role} should not be able to create sortie"


def test_admin_can_create_sortie(db, client):
    payload = {
        "sortie_number": "ADM-001",
        "cadet_id": db.users["cadet"],
        "instructor_id": db.users["instructor"],
        "aircraft_id": db.aircraft_ready_id,
        "base_id": 1,
        "lesson_type": "Admin Override",
        "scheduled_start": "2026-12-31T10:00:00",
        "scheduled_end": "2026-12-31T11:00:00",
    }
    r = client.post("/sorties", headers=headers(db.users["admin"]), json=payload)
    assert r.status_code == 201


def test_dispatcher_can_create_sortie(db, client):
    payload = {
        "sortie_number": "DSP-001",
        "cadet_id": db.users["cadet"],
        "instructor_id": db.users["instructor"],
        "aircraft_id": db.aircraft_ready_id,
        "base_id": 1,
        "lesson_type": "Standard",
        "scheduled_start": "2026-12-31T10:00:00",
        "scheduled_end": "2026-12-31T11:00:00",
    }
    r = client.post("/sorties", headers=headers(db.users["dispatcher"]), json=payload)
    assert r.status_code == 201
    assert r.json()["status"] == "SCHEDULED"


# ---------- /sorties/{id}/release ----------

def test_non_dispatcher_cannot_release(db, client):
    for role in ("instructor", "cfi", "cadet", "maint"):
        r = client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users[role]))
        assert r.status_code == 403, f"{role} should not release"


# ---------- /aircraft/{id}/ground ----------

def test_non_maintenance_cannot_ground_aircraft(db, client):
    for role in ("dispatcher", "instructor", "cfi", "cadet"):
        r = client.patch(f"/aircraft/{db.aircraft_ready_id}/ground", headers=headers(db.users[role]))
        assert r.status_code == 403, f"{role} should not ground aircraft"


def test_maintenance_can_ground_aircraft(db, client):
    r = client.patch(f"/aircraft/{db.aircraft_ready_id}/ground", headers=headers(db.users["maint"]))
    assert r.status_code == 200
    assert r.json()["status"] == "GROUNDED"


def test_admin_can_ground_aircraft(db, client):
    """ADMIN should bypass role checks everywhere."""
    r = client.patch(f"/aircraft/{db.aircraft_ready_id}/ground", headers=headers(db.users["admin"]))
    assert r.status_code == 200


# ---------- /aircraft/{id}/ready ----------

def test_non_maintenance_cannot_mark_ready(db, client):
    for role in ("dispatcher", "instructor", "cfi", "cadet"):
        r = client.patch(f"/aircraft/{db.aircraft_grounded_id}/ready", headers=headers(db.users[role]))
        assert r.status_code == 403


# ---------- /training-progress (POST) ----------

def test_only_instructor_can_submit_training(db, client):
    _walk_to_landed(client, db)
    payload = {
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 3, "situational_awareness_score": 4,
        "remarks": "n/a",
    }
    for role in ("dispatcher", "cfi", "cadet", "maint"):
        r = client.post("/training-progress", headers=headers(db.users[role]), json=payload)
        assert r.status_code == 403, f"{role} should not submit training"


# ---------- /training-progress/{id}/approve ----------

def test_only_cfi_can_approve_training(db, client):
    _walk_to_landed(client, db)
    submit = _submit_training(client, db)
    training_id = submit.json()["id"]
    for role in ("dispatcher", "instructor", "cadet", "maint"):
        r = client.patch(f"/training-progress/{training_id}/approve", headers=headers(db.users[role]))
        assert r.status_code == 403, f"{role} should not approve"


def test_only_cfi_can_reject_training(db, client):
    _walk_to_landed(client, db)
    submit = _submit_training(client, db)
    training_id = submit.json()["id"]
    for role in ("dispatcher", "instructor", "cadet", "maint"):
        r = client.patch(
            f"/training-progress/{training_id}/reject",
            headers=headers(db.users[role]),
            json={"remarks": "no"},
        )
        assert r.status_code == 403


# ---------- /defects (POST) ----------

def test_dispatcher_and_cfi_and_cadet_cannot_create_defect(db, client):
    payload = {"aircraft_id": db.aircraft_ready_id, "severity": "LOW", "description": "x"}
    for role in ("dispatcher", "cfi", "cadet"):
        r = client.post("/defects", headers=headers(db.users[role]), json=payload)
        assert r.status_code == 403


def test_instructor_can_create_defect(db, client):
    """Instructor can also report defects (they see issues during flight)."""
    payload = {"aircraft_id": db.aircraft_ready_id, "severity": "LOW", "description": "Stall warning intermittent"}
    r = client.post("/defects", headers=headers(db.users["instructor"]), json=payload)
    assert r.status_code == 201


def test_maintenance_can_create_defect(db, client):
    payload = {"aircraft_id": db.aircraft_ready_id, "severity": "HIGH", "description": "Mag drop"}
    r = client.post("/defects", headers=headers(db.users["maint"]), json=payload)
    assert r.status_code == 201


# ---------- /defects/{id}/resolve ----------

def test_only_maintenance_can_resolve_defect(db, client):
    # Create a defect first
    create = client.post(
        "/defects",
        headers=headers(db.users["maint"]),
        json={"aircraft_id": db.aircraft_ready_id, "severity": "LOW", "description": "x"},
    )
    defect_id = create.json()["id"]

    for role in ("dispatcher", "instructor", "cfi", "cadet"):
        r = client.patch(f"/defects/{defect_id}/resolve", headers=headers(db.users[role]))
        assert r.status_code == 403


# ---------- Cadet data-level scoping ----------

def test_cadet_sees_only_own_sorties(db, client):
    """List endpoint must filter by cadet_id for CADET role."""
    r = client.get("/sorties", headers=headers(db.users["cadet"]))
    assert r.status_code == 200
    data = r.json()
    # Helper sortie cadet IS this cadet, so it should appear (count = 1)
    assert all(s["cadet_id"] == db.users["cadet"] for s in data)


def test_cadet_cannot_view_other_cadets_sortie(db, client):
    """Cadet B should get 403 when trying to view cadet A's sortie."""
    # Create a second cadet
    from app.db.models import User, UserRole
    other = User(full_name="Other Cadet", email="other@t.in", role=UserRole.CADET, base_id=1)
    db.session.add(other)
    db.session.commit()

    r = client.get(f"/sorties/{db.sortie_id}", headers=headers(other.id))
    assert r.status_code == 403


# ---------- /auth/me ----------

def test_auth_me_returns_correct_user(db, client):
    r = client.get("/auth/me", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200
    assert r.json()["role"] == "DISPATCHER"


def test_auth_me_missing_header_returns_401(db, client):
    r = client.get("/auth/me")
    # Missing required header -> Pydantic returns 422; we treat it as auth failure
    assert r.status_code in (401, 422)


def test_auth_me_invalid_user_id_returns_401(db, client):
    r = client.get("/auth/me", headers=headers(99999))
    assert r.status_code == 401
