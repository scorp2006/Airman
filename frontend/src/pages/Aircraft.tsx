// Aircraft Readiness - bento style.

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listAircraft, listDefects, createDefect, resolveDefect, groundAircraft, readyAircraft,
} from "../api/endpoints";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Loading, Empty } from "../components/Empty";
import { toast } from "../components/Toast";
import { useAuth } from "../context/AuthContext";
import type { DefectSeverity } from "../types";

export default function AircraftPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const aircraftQ = useQuery({ queryKey: ["aircraft"], queryFn: listAircraft });
  const defectsQ = useQuery({ queryKey: ["defects"], queryFn: listDefects });

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [form, setForm] = useState<{ severity: DefectSeverity; description: string }>({
    severity: "MEDIUM",
    description: "",
  });

  if (aircraftQ.isLoading) return <Loading />;
  const aircraft = aircraftQ.data ?? [];
  const defects = defectsQ.data ?? [];

  if (selectedId === null && aircraft.length > 0) setSelectedId(aircraft[0].id);
  const selected = aircraft.find((a) => a.id === selectedId);
  const selectedDefects = defects.filter((d) => d.aircraft_id === selectedId);
  const openCount = selectedDefects.filter((d) => d.status === "OPEN").length;

  const isMaint = user?.role === "MAINTENANCE_OFFICER" || user?.role === "ADMIN";

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["aircraft"] });
    qc.invalidateQueries({ queryKey: ["defects"] });
  };

  const groundMut = useMutation({
    mutationFn: (id: number) => groundAircraft(id),
    onSuccess: () => { toast("Aircraft grounded"); invalidate(); },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Failed", "err"),
  });
  const readyMut = useMutation({
    mutationFn: (id: number) => readyAircraft(id),
    onSuccess: () => { toast("Aircraft marked READY"); invalidate(); },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Failed", "err"),
  });
  const defectMut = useMutation({
    mutationFn: createDefect,
    onSuccess: () => {
      toast("Defect filed - aircraft grounded");
      setForm({ severity: "MEDIUM", description: "" });
      invalidate();
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Failed", "err"),
  });
  const resolveMut = useMutation({
    mutationFn: (id: number) => resolveDefect(id),
    onSuccess: () => { toast("Defect resolved"); invalidate(); },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Failed", "err"),
  });

  return (
    <>
      <PageHeader title="Aircraft" subtitle="Fleet readiness, defects, and maintenance." />

      <div className="grid grid-cols-12 gap-4">
        {/* Fleet list */}
        <div className="col-span-12 lg:col-span-4 space-y-3">
          {aircraft.map((a) => {
            const open = defects.filter((d) => d.aircraft_id === a.id && d.status === "OPEN").length;
            return (
              <button
                key={a.id}
                onClick={() => setSelectedId(a.id)}
                className={`w-full text-left card p-5 transition ${
                  selectedId === a.id ? "border-lime/60" : "hover:border-bg-line"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-ink-high font-bold text-lg">[{a.registration}]</span>
                  <StatusBadge status={a.status} />
                </div>
                <div className="text-ink-low text-sm">{a.aircraft_type}</div>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-[11px] uppercase tracking-wider text-ink-low">TBO Remaining</span>
                  <span className="font-mono text-sm text-ink-high">{a.tbo_remaining_hours} h</span>
                </div>
                {open > 0 && (
                  <div className="chip bg-tang/15 text-tang border border-tang/30 mt-3">
                    {open} open defect{open > 1 ? "s" : ""}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Detail */}
        <div className="col-span-12 lg:col-span-8 space-y-4">
          {selected ? (
            <>
              <div className="card p-6">
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <div className="font-mono text-3xl font-bold text-ink-high">[{selected.registration}]</div>
                    <div className="text-ink-low text-sm mt-1">{selected.aircraft_type}</div>
                  </div>
                  <StatusBadge status={selected.status} size="md" />
                </div>
                {isMaint && (
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="pill-danger"
                      disabled={selected.status === "GROUNDED" || groundMut.isPending}
                      onClick={() => groundMut.mutate(selected.id)}
                    >
                      Ground Aircraft
                    </button>
                    <button
                      className="pill-primary"
                      disabled={openCount > 0 || selected.status === "READY" || readyMut.isPending}
                      onClick={() => readyMut.mutate(selected.id)}
                    >
                      Mark Ready
                    </button>
                    {openCount > 0 && selected.status === "GROUNDED" && (
                      <span className="text-xs text-ink-low self-center">
                        Resolve all defects before marking ready
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Defects */}
              <div className="card p-6">
                <div className="eyebrow mb-4">Defects</div>
                {selectedDefects.length === 0 ? (
                  <div className="text-ink-low text-sm">No defects on record.</div>
                ) : (
                  <ul className="space-y-2">
                    {selectedDefects.map((d) => (
                      <li
                        key={d.id}
                        className="flex items-start justify-between gap-4 p-4 card-2 border border-bg-line/40"
                      >
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <StatusBadge status={d.severity} />
                            <StatusBadge status={d.status} />
                            <span className="text-xs text-ink-dim font-mono">
                              {new Date(d.created_at).toLocaleString("en-IN", { hour12: false })}
                            </span>
                          </div>
                          <div className="text-sm text-ink-mid">{d.description}</div>
                        </div>
                        {isMaint && d.status === "OPEN" && (
                          <button
                            className="pill-ghost shrink-0"
                            disabled={resolveMut.isPending}
                            onClick={() => resolveMut.mutate(d.id)}
                          >
                            Resolve
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Report defect form */}
              {isMaint && (
                <div className="card p-6">
                  <div className="eyebrow mb-4">Report a Defect</div>
                  <div className="space-y-4">
                    <div>
                      <label className="label">Severity</label>
                      <div className="flex gap-2 flex-wrap">
                        {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as DefectSeverity[]).map((s) => (
                          <button
                            key={s}
                            type="button"
                            onClick={() => setForm({ ...form, severity: s })}
                            className={form.severity === s ? "pill bg-lime text-black" : "pill-ghost"}
                          >
                            {s}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="label">Description</label>
                      <textarea
                        className="input min-h-[100px]"
                        value={form.description}
                        onChange={(e) => setForm({ ...form, description: e.target.value })}
                        placeholder="What's wrong with the aircraft? Be specific — this triggers grounding."
                      />
                    </div>
                    <button
                      className="pill-primary"
                      disabled={!form.description.trim() || defectMut.isPending}
                      onClick={() =>
                        defectMut.mutate({
                          aircraft_id: selected.id,
                          severity: form.severity,
                          description: form.description,
                        })
                      }
                    >
                      {defectMut.isPending ? "Filing…" : "File Defect & Ground Aircraft"}
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <Empty label="Select an aircraft" />
          )}
        </div>
      </div>
    </>
  );
}
