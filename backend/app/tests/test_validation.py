"""
Validation tests - Pydantic schemas and business validation rules.
"""

from app.tests.conftest import headers
from app.db.models import SortieStatus


def _walk_to_landed(client, db):
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))


# ---------- training score range ----------

def test_score_below_1_rejected(db, client):
    _walk_to_landed(client, db)
    r = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 0,           # invalid
        "communication_score": 3,
        "situational_awareness_score": 4,
        "remarks": "x",
    })
    assert r.status_code == 422  # Pydantic validation


def test_score_above_5_rejected(db, client):
    _walk_to_landed(client, db)
    r = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4,
        "communication_score": 6,      # invalid
        "situational_awareness_score": 4,
        "remarks": "x",
    })
    assert r.status_code == 422


def test_score_negative_rejected(db, client):
    _walk_to_landed(client, db)
    r = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": -2,
        "communication_score": 3,
        "situational_awareness_score": 4,
        "remarks": "x",
    })
    assert r.status_code == 422


def test_empty_remarks_rejected(db, client):
    _walk_to_landed(client, db)
    r = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4,
        "communication_score": 3,
        "situational_awareness_score": 4,
        "remarks": "",                 # invalid - min_length=1
    })
    assert r.status_code == 422


def test_score_1_to_5_all_valid(db, client):
    _walk_to_landed(client, db)
    # 1, 2, 3, 4, 5 should all be accepted - we just check the boundary
    r = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 1,           # boundary
        "communication_score": 5,      # boundary
        "situational_awareness_score": 3,
        "remarks": "Test remarks.",
    })
    assert r.status_code == 201


# ---------- defect description ----------

def test_empty_defect_description_rejected(db, client):
    r = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "LOW",
        "description": "",
    })
    assert r.status_code == 422


def test_invalid_defect_severity_rejected(db, client):
    r = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "EXTREME",         # not a valid enum value
        "description": "Something broke",
    })
    assert r.status_code == 422


# ---------- create sortie validation ----------

def test_create_sortie_missing_field(db, client):
    payload = {
        # sortie_number missing
        "cadet_id": db.users["cadet"],
        "instructor_id": db.users["instructor"],
        "aircraft_id": db.aircraft_ready_id,
        "base_id": 1,
        "lesson_type": "Test",
        "scheduled_start": "2026-12-31T10:00:00",
        "scheduled_end": "2026-12-31T11:00:00",
    }
    r = client.post("/sorties", headers=headers(db.users["dispatcher"]), json=payload)
    assert r.status_code == 422


def test_create_sortie_on_nonexistent_aircraft(db, client):
    payload = {
        "sortie_number": "NX-001",
        "cadet_id": db.users["cadet"],
        "instructor_id": db.users["instructor"],
        "aircraft_id": 99999,          # doesn't exist
        "base_id": 1,
        "lesson_type": "Test",
        "scheduled_start": "2026-12-31T10:00:00",
        "scheduled_end": "2026-12-31T11:00:00",
    }
    r = client.post("/sorties", headers=headers(db.users["dispatcher"]), json=payload)
    assert r.status_code == 404


def test_create_sortie_on_grounded_aircraft_rejected(db, client):
    payload = {
        "sortie_number": "GR-001",
        "cadet_id": db.users["cadet"],
        "instructor_id": db.users["instructor"],
        "aircraft_id": db.aircraft_grounded_id,
        "base_id": 1,
        "lesson_type": "Test",
        "scheduled_start": "2026-12-31T10:00:00",
        "scheduled_end": "2026-12-31T11:00:00",
    }
    r = client.post("/sorties", headers=headers(db.users["dispatcher"]), json=payload)
    assert r.status_code == 400
    assert "grounded" in r.json()["detail"].lower()


# ---------- non-existent entity ----------

def test_release_nonexistent_sortie_returns_404(db, client):
    r = client.patch("/sorties/99999/release", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 404


def test_get_nonexistent_aircraft_returns_404(db, client):
    r = client.get("/aircraft/99999", headers=headers(db.users["admin"]))
    assert r.status_code == 404


def test_resolve_nonexistent_defect_returns_404(db, client):
    r = client.patch("/defects/99999/resolve", headers=headers(db.users["maint"]))
    assert r.status_code == 404
