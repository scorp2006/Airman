"""
Defect / aircraft-readiness lifecycle tests.
"""

from app.tests.conftest import headers
from app.db.models import Aircraft, AircraftStatus, DefectStatus, Defect


def test_defect_creation_grounds_aircraft(db, client):
    r = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "HIGH",
        "description": "Brake binding.",
    })
    assert r.status_code == 201

    a = db.session.query(Aircraft).filter(Aircraft.id == db.aircraft_ready_id).first()
    db.session.refresh(a)
    assert a.status == AircraftStatus.GROUNDED


def test_resolving_defect_does_not_auto_ready_aircraft(db, client):
    """Spec rule: aircraft READY requires explicit mark_ready by Maintenance."""
    create = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "LOW",
        "description": "Light bulb",
    })
    did = create.json()["id"]
    client.patch(f"/defects/{did}/resolve", headers=headers(db.users["maint"]))

    a = db.session.query(Aircraft).filter(Aircraft.id == db.aircraft_ready_id).first()
    db.session.refresh(a)
    # Aircraft should STILL be grounded - mechanic must explicitly mark it ready
    assert a.status == AircraftStatus.GROUNDED


def test_mark_ready_blocked_when_open_defects_remain(db, client):
    """Cannot mark aircraft READY if any OPEN defect exists."""
    client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "MEDIUM",
        "description": "Engine cowling loose",
    })
    r = client.patch(f"/aircraft/{db.aircraft_ready_id}/ready", headers=headers(db.users["maint"]))
    assert r.status_code == 400
    assert "open defect" in r.json()["detail"].lower()


def test_mark_ready_succeeds_after_all_defects_resolved(db, client):
    create = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "LOW",
        "description": "Tail light",
    })
    did = create.json()["id"]
    client.patch(f"/defects/{did}/resolve", headers=headers(db.users["maint"]))

    r = client.patch(f"/aircraft/{db.aircraft_ready_id}/ready", headers=headers(db.users["maint"]))
    assert r.status_code == 200
    assert r.json()["status"] == "READY"


def test_multiple_defects_all_must_resolve(db, client):
    """Two defects open - resolving one isn't enough."""
    d1 = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "LOW",
        "description": "First defect",
    }).json()
    client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "HIGH",
        "description": "Second defect",
    })
    # Resolve only the first
    client.patch(f"/defects/{d1['id']}/resolve", headers=headers(db.users["maint"]))
    # Mark-ready should still fail
    r = client.patch(f"/aircraft/{db.aircraft_ready_id}/ready", headers=headers(db.users["maint"]))
    assert r.status_code == 400


def test_resolved_defect_cannot_be_resolved_again(db, client):
    create = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "LOW",
        "description": "x",
    })
    did = create.json()["id"]
    client.patch(f"/defects/{did}/resolve", headers=headers(db.users["maint"]))
    r = client.patch(f"/defects/{did}/resolve", headers=headers(db.users["maint"]))
    assert r.status_code == 400


def test_defect_tied_to_landed_sortie_marks_sortie_aircraft_grounded(db, client):
    """When defect is filed against a sortie in LANDED status, sortie becomes AIRCRAFT_GROUNDED."""
    # Walk sortie to LANDED
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))

    client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "sortie_id": db.sortie_id,
        "severity": "CRITICAL",
        "description": "Hard landing damage suspected",
    })

    s = client.get(f"/sorties/{db.sortie_id}", headers=headers(db.users["admin"]))
    assert s.json()["status"] == "AIRCRAFT_GROUNDED"


def test_listing_defects_returns_all(db, client):
    client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "LOW",
        "description": "Test defect A",
    })
    client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "severity": "HIGH",
        "description": "Test defect B",
    })
    r = client.get("/defects", headers=headers(db.users["admin"]))
    assert r.status_code == 200
    assert len(r.json()) >= 2
