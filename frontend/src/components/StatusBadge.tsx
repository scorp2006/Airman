// Chunky status pill - lime for "good/active", orange for "in progress/warning",
// white for neutral, red for dangerous, gray for finished.

import type { AircraftStatus, SortieStatus, TrainingStatus, DefectStatus, DefectSeverity } from "../types";
type AnyStatus = SortieStatus | AircraftStatus | TrainingStatus | DefectStatus | DefectSeverity;

const COLOR: Record<string, string> = {
  // Sortie
  SCHEDULED: "bg-bg-chip text-ink-mid border border-bg-line",
  RELEASED: "bg-white text-black",
  AIRBORNE: "bg-lime text-black",
  LANDED: "bg-white text-black",
  TRAINING_SUBMITTED: "bg-tang text-black",
  TRAINING_APPROVED: "bg-lime text-black",
  CLOSED: "bg-bg-chip text-ink-low border border-bg-line",
  CANCELLED: "bg-red-500/15 text-red-300 border border-red-500/30",
  AIRCRAFT_GROUNDED: "bg-red-500/20 text-red-300 border border-red-500/40",
  RECOVERY_REQUIRED: "bg-tang/20 text-tang border border-tang/40",
  // Aircraft
  READY: "bg-lime text-black",
  GROUNDED: "bg-red-500/20 text-red-300 border border-red-500/40",
  MAINTENANCE: "bg-tang text-black",
  // Training
  DRAFT: "bg-bg-chip text-ink-low border border-bg-line",
  SUBMITTED: "bg-tang text-black",
  APPROVED: "bg-lime text-black",
  REJECTED: "bg-red-500/15 text-red-300 border border-red-500/40",
  // Defects
  OPEN: "bg-tang text-black",
  RESOLVED: "bg-lime text-black",
  LOW: "bg-bg-chip text-ink-mid border border-bg-line",
  MEDIUM: "bg-yellow-400/20 text-yellow-300 border border-yellow-400/40",
  HIGH: "bg-tang text-black",
  CRITICAL: "bg-red-500/20 text-red-300 border border-red-500/40",
};

const PULSES = new Set(["AIRBORNE", "GROUNDED", "AIRCRAFT_GROUNDED"]);

export function StatusBadge({ status, size = "sm" }: { status: AnyStatus; size?: "sm" | "md" }) {
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
