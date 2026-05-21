"""
Seed script - populates the database with starter data so the app is usable
out of the box.

Run from the backend/ folder:
    python seed.py

Idempotent: wipes existing rows first, then inserts fresh data. Safe to re-run.
"""

from datetime import datetime, timedelta

from app.db.database import SessionLocal, Base, engine
from app.db.models import (
    User, UserRole, BaseLocation, Aircraft, AircraftStatus,
    Sortie, SortieStatus, TrainingProgress, TrainingStatus,
    Defect, DefectSeverity, DefectStatus, AuditLog,
)


def seed():
    # Ensure tables exist.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ---- Wipe existing rows in dependency-safe order ----
        for model in (AuditLog, Defect, TrainingProgress, Sortie, Aircraft, User, BaseLocation):
            db.query(model).delete()
        db.commit()

        # ---- Bases ----
        base1 = BaseLocation(name="Bangalore Flight Center", code="BLR", location="Bangalore, KA")
        base2 = BaseLocation(name="Hyderabad Aviation Hub", code="HYD", location="Hyderabad, TS")
        db.add_all([base1, base2])
        db.flush()

        # ---- Users (one per role) ----
        admin = User(full_name="Admin User", email="admin@airman.in", role=UserRole.ADMIN, base_id=base1.id)
        dispatcher = User(full_name="Dispatch Officer", email="dispatch@airman.in", role=UserRole.DISPATCHER, base_id=base1.id)
        instructor = User(full_name="Capt. Rao", email="rao@airman.in", role=UserRole.INSTRUCTOR, base_id=base1.id)
        cfi = User(full_name="Chief Flying Instructor", email="cfi@airman.in", role=UserRole.CFI, base_id=base1.id)
        cadet = User(full_name="Arjun Menon", email="arjun@airman.in", role=UserRole.CADET, base_id=base1.id)
        maint = User(full_name="Maintenance Officer", email="maint@airman.in", role=UserRole.MAINTENANCE_OFFICER, base_id=base1.id)
        db.add_all([admin, dispatcher, instructor, cfi, cadet, maint])
        db.flush()

        # ---- Aircraft ----
        a1 = Aircraft(registration="VT-ABC", aircraft_type="Cessna 172", base_id=base1.id,
                      status=AircraftStatus.READY, tbo_remaining_hours=1850)
        a2 = Aircraft(registration="VT-SKY", aircraft_type="Piper PA-28", base_id=base1.id,
                      status=AircraftStatus.GROUNDED, tbo_remaining_hours=900)
        a3 = Aircraft(registration="VT-AIR", aircraft_type="Diamond DA40", base_id=base2.id,
                      status=AircraftStatus.READY, tbo_remaining_hours=1500)
        db.add_all([a1, a2, a3])
        db.flush()

        # ---- Sorties (5 with different statuses) ----
        now = datetime.utcnow()
        sorties = [
            Sortie(sortie_number="SOR-001", cadet_id=cadet.id, instructor_id=instructor.id,
                   aircraft_id=a1.id, base_id=base1.id, lesson_type="Circuits",
                   scheduled_start=now + timedelta(hours=1), scheduled_end=now + timedelta(hours=2),
                   status=SortieStatus.SCHEDULED),
            Sortie(sortie_number="SOR-002", cadet_id=cadet.id, instructor_id=instructor.id,
                   aircraft_id=a3.id, base_id=base2.id, lesson_type="Navigation",
                   scheduled_start=now - timedelta(hours=3), scheduled_end=now - timedelta(hours=2),
                   status=SortieStatus.RELEASED),
            Sortie(sortie_number="SOR-003", cadet_id=cadet.id, instructor_id=instructor.id,
                   aircraft_id=a1.id, base_id=base1.id, lesson_type="Stalls",
                   scheduled_start=now - timedelta(hours=5), scheduled_end=now - timedelta(hours=4),
                   actual_start=now - timedelta(hours=5),
                   status=SortieStatus.AIRBORNE),
            Sortie(sortie_number="SOR-004", cadet_id=cadet.id, instructor_id=instructor.id,
                   aircraft_id=a3.id, base_id=base2.id, lesson_type="Landings",
                   scheduled_start=now - timedelta(hours=8), scheduled_end=now - timedelta(hours=7),
                   actual_start=now - timedelta(hours=8), actual_end=now - timedelta(hours=7),
                   status=SortieStatus.LANDED),
            Sortie(sortie_number="SOR-005", cadet_id=cadet.id, instructor_id=instructor.id,
                   aircraft_id=a1.id, base_id=base1.id, lesson_type="Emergency Procedures",
                   scheduled_start=now - timedelta(days=1), scheduled_end=now - timedelta(days=1, hours=-1),
                   actual_start=now - timedelta(days=1), actual_end=now - timedelta(days=1, hours=-1),
                   status=SortieStatus.CLOSED),
        ]
        db.add_all(sorties)
        db.flush()

        # ---- Training progress (2 records) ----
        # one SUBMITTED awaiting CFI approval, one APPROVED (for closed sortie)
        t1 = TrainingProgress(sortie_id=sorties[3].id, cadet_id=cadet.id, instructor_id=instructor.id,
                              lesson_type=sorties[3].lesson_type,
                              maneuver_score=4, communication_score=3, situational_awareness_score=4,
                              remarks="Good landings, work on radio calls.",
                              status=TrainingStatus.SUBMITTED, submitted_at=now)
        t2 = TrainingProgress(sortie_id=sorties[4].id, cadet_id=cadet.id, instructor_id=instructor.id,
                              lesson_type=sorties[4].lesson_type,
                              maneuver_score=5, communication_score=4, situational_awareness_score=5,
                              remarks="Excellent emergency handling.",
                              status=TrainingStatus.APPROVED, submitted_at=now - timedelta(hours=23),
                              approved_by=cfi.id, approved_at=now - timedelta(hours=22))
        db.add_all([t1, t2])
        db.flush()

        # ---- Defects (2) ----
        d1 = Defect(aircraft_id=a2.id, reported_by=maint.id, severity=DefectSeverity.HIGH,
                    description="Magneto fluctuation observed on right engine.",
                    status=DefectStatus.OPEN)
        d2 = Defect(aircraft_id=a1.id, reported_by=instructor.id, severity=DefectSeverity.LOW,
                    description="Cabin air vent stiff.",
                    status=DefectStatus.RESOLVED)
        db.add_all([d1, d2])
        db.flush()

        # ---- A few audit log entries so the audit screen has something to show ----
        db.add_all([
            AuditLog(actor_id=dispatcher.id, action="SORTIE_CREATED", entity_type="Sortie", entity_id=sorties[0].id,
                     new_value='{"status":"SCHEDULED"}'),
            AuditLog(actor_id=dispatcher.id, action="SORTIE_RELEASED", entity_type="Sortie", entity_id=sorties[1].id,
                     old_value='{"status":"SCHEDULED"}', new_value='{"status":"RELEASED"}'),
            AuditLog(actor_id=maint.id, action="DEFECT_CREATED", entity_type="Defect", entity_id=d1.id,
                     new_value='{"severity":"HIGH"}'),
            AuditLog(actor_id=cfi.id, action="TRAINING_APPROVED", entity_type="TrainingProgress", entity_id=t2.id,
                     new_value='{"status":"APPROVED"}'),
        ])

        db.commit()
        print("Seed complete.")
        print(f"  Bases: 2, Users: 6, Aircraft: 3, Sorties: 5, Training: 2, Defects: 2")
        print("  Login emails:")
        for u in (admin, dispatcher, instructor, cfi, cadet, maint):
            print(f"    {u.role.value:22}  {u.email}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
