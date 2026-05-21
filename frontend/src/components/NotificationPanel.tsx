// Notification panel - dropdown that opens from the bell icon.
//
// Pulls recent audit log entries and shows them as notifications,
// filtered to what's relevant for the current role.

import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { listAuditLogs, listUsers } from "../api/endpoints";
import { useAuth } from "../context/AuthContext";
import type { UserRole } from "../types";

// What kinds of events each role cares about.
const ROLE_FILTERS: Record<UserRole, string[]> = {
  ADMIN: [],  // sees all
  DISPATCHER: [
    "SORTIE_CREATED", "SORTIE_RELEASED", "SORTIE_AIRBORNE", "SORTIE_LANDED",
    "AIRCRAFT_GROUNDED", "DEFECT_CREATED",
  ],
  INSTRUCTOR: ["SORTIE_LANDED", "TRAINING_REJECTED"],
  CFI: ["TRAINING_SUBMITTED"],
  CADET: ["TRAINING_APPROVED", "SORTIE_CLOSED"],
  MAINTENANCE_OFFICER: ["DEFECT_CREATED", "AIRCRAFT_GROUNDED", "SORTIE_LANDED"],
};

// Friendly action labels.
const ACTION_LABEL: Record<string, string> = {
  SORTIE_CREATED: "New sortie scheduled",
  SORTIE_RELEASED: "Sortie released",
  SORTIE_AIRBORNE: "Sortie airborne",
  SORTIE_LANDED: "Sortie landed",
  SORTIE_CANCELLED: "Sortie cancelled",
  SORTIE_CLOSED: "Sortie closed",
  AIRCRAFT_GROUNDED: "Aircraft grounded",
  AIRCRAFT_READY: "Aircraft marked ready",
  TRAINING_SUBMITTED: "Training submitted",
  TRAINING_APPROVED: "Training approved",
  TRAINING_REJECTED: "Training rejected",
  DEFECT_CREATED: "New defect reported",
  DEFECT_RESOLVED: "Defect resolved",
};

const ACTION_COLOR: Record<string, string> = {
  SORTIE_CREATED: "bg-lime/15 text-lime",
  SORTIE_RELEASED: "bg-lime/15 text-lime",
  SORTIE_AIRBORNE: "bg-lime/15 text-lime",
  SORTIE_LANDED: "bg-white/10 text-ink-high",
  SORTIE_CLOSED: "bg-bg-chip text-ink-low",
  SORTIE_CANCELLED: "bg-red-500/15 text-red-400",
  AIRCRAFT_GROUNDED: "bg-red-500/15 text-red-400",
  AIRCRAFT_READY: "bg-lime/15 text-lime",
  TRAINING_SUBMITTED: "bg-tang/15 text-tang",
  TRAINING_APPROVED: "bg-lime/15 text-lime",
  TRAINING_REJECTED: "bg-red-500/15 text-red-400",
  DEFECT_CREATED: "bg-tang/15 text-tang",
  DEFECT_RESOLVED: "bg-lime/15 text-lime",
};

// Format a timestamp as "5 minutes ago" / "2 hours ago" / "3 days ago"
function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-IN");
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function NotificationPanel({ open, onClose }: Props) {
  const { user } = useAuth();
  const ref = useRef<HTMLDivElement>(null);

  const auditQ = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => listAuditLogs({}),
    enabled: open,
  });
  const usersQ = useQuery({ queryKey: ["users"], queryFn: listUsers, enabled: open });

  // Close panel when clicking outside.
  useEffect(() => {
    if (!open) return;
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    // Slight delay so the click that opened the panel doesn't immediately close it.
    const t = setTimeout(() => document.addEventListener("mousedown", onClick), 50);
    return () => {
      clearTimeout(t);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open, onClose]);

  if (!open) return null;

  const userById = Object.fromEntries((usersQ.data ?? []).map((u) => [u.id, u]));
  const filterList = user ? ROLE_FILTERS[user.role] : [];
  const filtered = (auditQ.data ?? []).filter((log) =>
    filterList.length === 0 ? true : filterList.includes(log.action),
  );
  const top = filtered.slice(0, 10);

  return (
    <div
      ref={ref}
      className="absolute right-0 top-12 w-96 card p-0 z-50 max-h-[480px] flex flex-col overflow-hidden shadow-2xl"
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-bg-line/60 flex items-center justify-between">
        <div>
          <div className="font-display font-semibold text-ink-high">Notifications</div>
          <div className="text-[11px] text-ink-low">Scoped to your role · last 10 events</div>
        </div>
        <span className="chip bg-lime text-black">{top.length}</span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-auto">
        {auditQ.isLoading && (
          <div className="p-5 text-ink-low text-sm">Loading…</div>
        )}
        {top.length === 0 && !auditQ.isLoading && (
          <div className="p-8 text-center text-ink-low text-sm">
            No new notifications for you right now.
          </div>
        )}
        {top.map((log) => {
          const actor = userById[log.actor_id];
          const color = ACTION_COLOR[log.action] ?? "bg-bg-chip text-ink-mid";
          const label = ACTION_LABEL[log.action] ?? log.action;
          const link = log.entity_type === "Sortie"
            ? `/sorties/${log.entity_id}`
            : log.entity_type === "Aircraft"
            ? "/aircraft"
            : log.entity_type === "TrainingProgress"
            ? "/training"
            : "/audit";
          return (
            <Link
              key={log.id}
              to={link}
              onClick={onClose}
              className="flex items-start gap-3 px-5 py-3 hover:bg-bg-card2 transition border-b border-bg-line/30"
            >
              <span className={`chip ${color} shrink-0 mt-0.5`}>
                {log.action.split("_")[0].slice(0, 3)}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-ink-high text-sm font-medium">{label}</div>
                <div className="text-ink-low text-xs mt-0.5">
                  {log.entity_type} #{log.entity_id}
                  {actor && <> · by {actor.full_name.split(" ")[0]}</>}
                </div>
              </div>
              <span className="text-[11px] text-ink-dim shrink-0">
                {timeAgo(log.created_at)}
              </span>
            </Link>
          );
        })}
      </div>

      {/* Footer */}
      <Link
        to="/audit"
        onClick={onClose}
        className="block px-5 py-3 border-t border-bg-line/60 text-center text-xs text-ink-low hover:text-lime transition"
      >
        View full audit log →
      </Link>
    </div>
  );
}
