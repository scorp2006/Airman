// Sortie Board - card-based grid (mobile friendly), big readable status, role-aware actions.

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { listSorties, listUsers, listAircraft, sortieAction } from "../api/endpoints";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Loading, Empty, ErrorBox } from "../components/Empty";
import { toast } from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import { IconSearch, IconChevron } from "../components/Icons";
import { CreateSortieModal } from "../components/CreateSortieModal";
import type { SortieStatus, UserRole } from "../types";

const ACTION_ROLES: Record<string, UserRole[]> = {
  release:  ["ADMIN", "DISPATCHER"],
  airborne: ["ADMIN", "DISPATCHER"],
  landed:   ["ADMIN", "DISPATCHER"],
  cancel:   ["ADMIN", "DISPATCHER"],
  close:    ["ADMIN", "DISPATCHER", "CFI"],
};
const ACTION_LABEL: Record<string, string> = {
  release: "Release",
  airborne: "Mark Airborne",
  landed: "Mark Landed",
  cancel: "Cancel",
  close: "Close Sortie",
};
function actionsFor(status: SortieStatus): string[] {
  switch (status) {
    case "SCHEDULED": return ["release", "cancel"];
    case "RELEASED": return ["airborne", "cancel"];
    case "AIRBORNE": return ["landed"];
    case "TRAINING_APPROVED": return ["close"];
    default: return [];
  }
}

const FILTERS: { key: string; label: string }[] = [
  { key: "all", label: "All" },
  { key: "active", label: "Active" },
  { key: "scheduled", label: "Scheduled" },
  { key: "airborne", label: "Airborne" },
  { key: "completed", label: "Completed" },
];

export default function SortieBoardPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [createOpen, setCreateOpen] = useState(false);

  const sortiesQ = useQuery({ queryKey: ["sorties"], queryFn: listSorties });
  const usersQ = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const aircraftQ = useQuery({ queryKey: ["aircraft"], queryFn: listAircraft });

  const mut = useMutation({
    mutationFn: ({ id, action }: { id: number; action: string }) => sortieAction(id, action),
    onSuccess: (_, v) => {
      toast(`${ACTION_LABEL[v.action]} — done`);
      qc.invalidateQueries({ queryKey: ["sorties"] });
      qc.invalidateQueries({ queryKey: ["aircraft"] });
      qc.invalidateQueries({ queryKey: ["audit-logs"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Action failed", "err"),
  });

  if (sortiesQ.isLoading) return <Loading />;
  if (sortiesQ.isError) return <ErrorBox message="Unable to load sorties." />;

  const userById = Object.fromEntries((usersQ.data ?? []).map((u) => [u.id, u]));
  const acftById = Object.fromEntries((aircraftQ.data ?? []).map((a) => [a.id, a]));

  // Filter pipeline
  let list = sortiesQ.data ?? [];
  if (filter === "active") list = list.filter((s) => ["SCHEDULED", "RELEASED", "AIRBORNE", "LANDED"].includes(s.status));
  if (filter === "scheduled") list = list.filter((s) => s.status === "SCHEDULED");
  if (filter === "airborne") list = list.filter((s) => s.status === "AIRBORNE");
  if (filter === "completed") list = list.filter((s) => ["CLOSED", "CANCELLED"].includes(s.status));
  if (search) {
    const q = search.toLowerCase();
    list = list.filter(
      (s) =>
        s.sortie_number.toLowerCase().includes(q) ||
        s.lesson_type.toLowerCase().includes(q) ||
        s.status.toLowerCase().includes(q),
    );
  }

  function canDo(action: string): boolean {
    if (!user) return false;
    return (ACTION_ROLES[action] ?? []).includes(user.role);
  }

  const canCreate = user?.role === "DISPATCHER" || user?.role === "ADMIN";

  return (
    <>
      <PageHeader
        title="Sortie Board"
        subtitle={`${list.length} of ${(sortiesQ.data ?? []).length} sorties · actions scoped to your role`}
        right={
          <>
            {FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={filter === f.key ? "pill bg-lime text-black" : "pill-ghost"}
              >
                {f.label}
              </button>
            ))}
            {canCreate && (
              <button onClick={() => setCreateOpen(true)} className="pill-primary">
                + New Sortie
              </button>
            )}
          </>
        }
      />
      <CreateSortieModal open={createOpen} onClose={() => setCreateOpen(false)} />

      {/* Search */}
      <div className="card-2 px-4 py-2 mb-6 flex items-center gap-3">
        <IconSearch className="w-4 h-4 text-ink-low" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by sortie number, lesson, or status…"
          className="flex-1 bg-transparent outline-none text-ink-high placeholder:text-ink-dim text-sm"
        />
      </div>

      {list.length === 0 ? (
        <Empty label="No sorties match your filters" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {list.map((s) => {
            const validActions = actionsFor(s.status).filter(canDo);
            const acft = acftById[s.aircraft_id];
            return (
              <div key={s.id} className="card p-5 flex flex-col">
                {/* Header: number + status */}
                <div className="flex items-center justify-between mb-4">
                  <Link
                    to={`/sorties/${s.id}`}
                    className="font-mono text-ink-high font-bold text-lg hover:text-lime transition"
                  >
                    {s.sortie_number}
                  </Link>
                  <StatusBadge status={s.status} size="md" />
                </div>

                {/* Body */}
                <div className="space-y-3 mb-5">
                  <Field label="Lesson" value={s.lesson_type} />
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Cadet" value={userById[s.cadet_id]?.full_name ?? "—"} />
                    <Field label="Instructor" value={userById[s.instructor_id]?.full_name ?? "—"} />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="Aircraft" value={acft ? `[${acft.registration}]` : "—"} mono />
                    <Field
                      label="Scheduled"
                      value={new Date(s.scheduled_start).toLocaleString("en-IN", {
                        day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", hour12: false,
                      })}
                      mono
                    />
                  </div>
                  {s.delay_minutes > 0 && (
                    <div className="chip bg-tang/15 text-tang border border-tang/30">
                      Delayed +{s.delay_minutes} min
                    </div>
                  )}
                </div>

                {/* Footer actions */}
                <div className="mt-auto pt-4 border-t border-bg-line/50 flex flex-wrap gap-2">
                  <Link to={`/sorties/${s.id}`} className="pill-ghost text-xs">
                    Open <IconChevron className="w-3 h-3" />
                  </Link>
                  {validActions.length === 0 ? (
                    <span className="text-ink-dim text-xs self-center ml-auto">
                      No actions available
                    </span>
                  ) : (
                    validActions.map((a) => (
                      <button
                        key={a}
                        disabled={mut.isPending}
                        onClick={() => mut.mutate({ id: s.id, action: a })}
                        className={
                          a === "cancel"
                            ? "pill-danger text-xs"
                            : a === "close"
                            ? "pill-primary text-xs"
                            : "pill-white text-xs"
                        }
                      >
                        {ACTION_LABEL[a]}
                      </button>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-low">{label}</div>
      <div className={`text-ink-high text-sm mt-0.5 ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  );
}
