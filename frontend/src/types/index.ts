// TypeScript types mirroring the backend Pydantic schemas.
// Keeping them in one file makes it easy to find and update.

export type UserRole =
  | "ADMIN"
  | "DISPATCHER"
  | "INSTRUCTOR"
  | "CFI"
  | "CADET"
  | "MAINTENANCE_OFFICER";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  base_id: number | null;
}

export type AircraftStatus =
  | "READY"
  | "SCHEDULED"
  | "AIRBORNE"
  | "LANDED"
  | "GROUNDED"
  | "MAINTENANCE";

export interface Aircraft {
  id: number;
  registration: string;
  aircraft_type: string;
  base_id: number;
  status: AircraftStatus;
  tbo_remaining_hours: number;
}

export type SortieStatus =
  | "SCHEDULED"
  | "RELEASED"
  | "AIRBORNE"
  | "LANDED"
  | "TRAINING_SUBMITTED"
  | "TRAINING_APPROVED"
  | "CLOSED"
  | "CANCELLED"
  | "AIRCRAFT_GROUNDED"
  | "RECOVERY_REQUIRED";

export interface Sortie {
  id: number;
  sortie_number: string;
  cadet_id: number;
  instructor_id: number;
  aircraft_id: number;
  base_id: number;
  lesson_type: string;
  scheduled_start: string;
  scheduled_end: string;
  actual_start: string | null;
  actual_end: string | null;
  status: SortieStatus;
  delay_minutes: number;
}

export type TrainingStatus = "DRAFT" | "SUBMITTED" | "APPROVED" | "REJECTED";

export interface TrainingProgress {
  id: number;
  sortie_id: number;
  cadet_id: number;
  instructor_id: number;
  lesson_type: string;
  maneuver_score: number | null;
  communication_score: number | null;
  situational_awareness_score: number | null;
  remarks: string | null;
  status: TrainingStatus;
  submitted_at: string | null;
  approved_by: number | null;
  approved_at: string | null;
}

export type DefectSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type DefectStatus = "OPEN" | "RESOLVED";

export interface Defect {
  id: number;
  aircraft_id: number;
  sortie_id: number | null;
  reported_by: number;
  severity: DefectSeverity;
  description: string;
  status: DefectStatus;
  created_at: string;
}

export interface AuditLog {
  id: number;
  actor_id: number;
  action: string;
  entity_type: string;
  entity_id: number;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}
