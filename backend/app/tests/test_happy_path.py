"""
End-to-end happy path: full sortie lifecycle from creation to closure.
"""

from app.tests.conftest import headers


def test_full_sortie_lifecycle(db, client):
    """
    The complete happy path:
      Create -> Release -> Airborne -> Landed -> Submit -> Approve -> Close
    Every step is a different role doing exactly what they're allowed to do.
    """
    # 1. Dispatcher creates a fresh sortie
    create = client.post("/sorties", headers=headers(db.users["dispatcher"]), json={
        "sortie_number": "E2E-001",
        "cadet_id": db.users["cadet"],
        "instructor_id": db.users["instructor"],
        "aircraft_id": db.aircraft_ready_id,
        "base_id": 1,
        "lesson_type": "Full E2E",
        "scheduled_start": "2026-12-31T10:00:00",
        "scheduled_end": "2026-12-31T11:00:00",
    })
    assert create.status_code == 201
    sortie_id = create.json()["id"]
    assert create.json()["status"] == "SCHEDULED"

    # 2. Dispatcher releases
    r = client.patch(f"/sorties/{sortie_id}/release", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200 and r.json()["status"] == "RELEASED"

    # 3. Dispatcher marks airborne
    r = client.patch(f"/sorties/{sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200 and r.json()["status"] == "AIRBORNE"

    # 4. Dispatcher marks landed
    r = client.patch(f"/sorties/{sortie_id}/landed", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200 and r.json()["status"] == "LANDED"

    # 5. Instructor submits training
    submit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": sortie_id,
        "maneuver_score": 5,
        "communication_score": 4,
        "situational_awareness_score": 5,
        "remarks": "Excellent performance.",
    })
    assert submit.status_code == 201
    training_id = submit.json()["id"]

    # Sortie now in TRAINING_SUBMITTED
    s = client.get(f"/sorties/{sortie_id}", headers=headers(db.users["admin"]))
    assert s.json()["status"] == "TRAINING_SUBMITTED"

    # 6. CFI approves
    r = client.patch(f"/training-progress/{training_id}/approve", headers=headers(db.users["cfi"]))
    assert r.status_code == 200 and r.json()["status"] == "APPROVED"

    # 7. Dispatcher closes
    r = client.patch(f"/sorties/{sortie_id}/close", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 200 and r.json()["status"] == "CLOSED"

    # 8. Verify audit log has all 7 actions
    audit = client.get(
        "/audit-logs", headers=headers(db.users["admin"]),
        params={"entity_type": "Sortie", "entity_id": sortie_id},
    ).json()
    actions = {log["action"] for log in audit}
    assert "SORTIE_CREATED" in actions
    assert "SORTIE_RELEASED" in actions
    assert "SORTIE_AIRBORNE" in actions
    assert "SORTIE_LANDED" in actions
    assert "SORTIE_CLOSED" in actions


def test_rejection_loop_recovery(db, client):
    """
    Reject path: instructor submits, CFI rejects, instructor resubmits, CFI approves.
    """
    # Get to LANDED
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))

    # First submission
    submit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 2, "communication_score": 2, "situational_awareness_score": 2,
        "remarks": "First attempt.",
    })
    tid = submit.json()["id"]

    # CFI rejects
    client.patch(
        f"/training-progress/{tid}/reject",
        headers=headers(db.users["cfi"]),
        json={"remarks": "Scores too low; reconsider"},
    )

    # Sortie back to LANDED
    s = client.get(f"/sorties/{db.sortie_id}", headers=headers(db.users["admin"]))
    assert s.json()["status"] == "LANDED"

    # Resubmit (this uses the POST path; the service overwrites the existing row)
    resubmit = client.post("/training-progress", headers=headers(db.users["instructor"]), json={
        "sortie_id": db.sortie_id,
        "maneuver_score": 4, "communication_score": 4, "situational_awareness_score": 4,
        "remarks": "Resubmitted with adjusted scores.",
    })
    assert resubmit.status_code == 201

    # CFI now approves
    r = client.patch(f"/training-progress/{tid}/approve", headers=headers(db.users["cfi"]))
    assert r.status_code == 200


def test_defect_exception_path(db, client):
    """
    Sortie lands -> defect reported -> aircraft grounded -> sortie cannot close.
    """
    client.patch(f"/sorties/{db.sortie_id}/release", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/airborne", headers=headers(db.users["dispatcher"]))
    client.patch(f"/sorties/{db.sortie_id}/landed", headers=headers(db.users["dispatcher"]))

    # Defect reported with sortie_id - should cascade
    r = client.post("/defects", headers=headers(db.users["maint"]), json={
        "aircraft_id": db.aircraft_ready_id,
        "sortie_id": db.sortie_id,
        "severity": "CRITICAL",
        "description": "Engine fire warning during taxi after landing",
    })
    assert r.status_code == 201

    # Aircraft should be grounded; sortie should be AIRCRAFT_GROUNDED
    s = client.get(f"/sorties/{db.sortie_id}", headers=headers(db.users["admin"]))
    assert s.json()["status"] == "AIRCRAFT_GROUNDED"

    # Cannot close the sortie (no training approved, and we're in AIRCRAFT_GROUNDED)
    r = client.patch(f"/sorties/{db.sortie_id}/close", headers=headers(db.users["dispatcher"]))
    assert r.status_code == 400
