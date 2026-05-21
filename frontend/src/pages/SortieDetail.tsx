// Sortie Detail - bento layout with clean flight strip timeline.

import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  getSortie, listUsers, listAircraft, getTrainingBySortie, listAuditLogs,
} from "../api/endpoints";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Loading, ErrorBox } from "../components/Empty";
import { IconChevron, IconCheck } from "../components/Icons";
import type { SortieStatus } from "../types";

const TIMELINE: SortieStatus[] = [
  "SCHEDULED",
  "RELEASED",
  "AIRBORNE",
  "LANDED",
  "TRAINING_SUBMITTED",
  "TRAINING_APPROVED",
  "CLOSED",
];

function StateTimeline({ current }: { current: SortieStatus }) {
  const currentIdx = TIMELINE.indexOf(current);
  return (
    <div className="card p-6">
      <div className="eyebrow mb-5">Flight Strip</div>
      <div className="flex items-stretch gap-2 overflow-x-auto">
        {TIMELINE.map((step, i) => {
          const done = currentIdx > i;
          const active = currentIdx === i;
          return (
            <div key={step} className="flex items-center gap-2 shrink-0">
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`w-10 h-10 rounded-pill grid place-items-center font-display font-bold text-sm
                    ${active ? "bg-lime text-black" : done ? "bg-lime/30 text-lime" : "bg-bg-card2 text-ink-dim border border-bg-line"}`}
                >
                  {done ? <IconCheck /> : i + 1}
                </div>
                <span
                  className={`text-[10px] font-semibold uppercase tracking-wider text-center max-w-[80px]
                    ${active ? "text-lime" : done ? "text-ink-mid" : "text-ink-dim"}`}
                >
                  {step.replace(/_/g, " ")}
                </span>
              </div>
              {i < TIMELINE.length - 1 && (
                <div className={`w-12 h-px mt-5 ${done ? "bg-lime/50" : "bg-bg-line"}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function SortieDetailPage() {
  const { id } = useParams<{ id: string }>();
  const sortieId = Number(id);

  const sortieQ = useQuery({ queryKey: ["sortie", sortieId], queryFn: () => getSortie(sortieId), enabled: !!sortieId });
  const usersQ = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const aircraftQ = useQuery({ queryKey: ["aircraft"], queryFn: listAircraft });
  const trainingQ = useQuery({
    queryKey: ["training", sortieId],
    queryFn: () => getTrainingBySortie(sortieId),
    enabled: !!sortieId,
    retry: false,
  });
  const auditQ = useQuery({
    queryKey: ["audit", "Sortie", sortieId],
    queryFn: () => listAuditLogs({ entity_type: "Sortie", entity_id: sortieId }),
    enabled: !!sortieId,
  });

  if (sortieQ.isLoading) return <Loading />;
  if (sortieQ.isError || !sortieQ.data) return <ErrorBox message="Sortie not found." />;

  const s = sortieQ.data;
  const userById = Object.fromEntries((usersQ.data ?? []).map((u) => [u.id, u]));
  const acft = (aircraftQ.data ?? []).find((a) => a.id === s.aircraft_id);
  const training = trainingQ.data;

  return (
    <>
      <PageHeader
        title={s.sortie_number}
        subtitle={`${s.lesson_type} · ${new Date(s.scheduled_start).toLocaleString("en-IN", { hour12: false })}`}
        right={
          <>
            <Link to="/sorties" className="pill-ghost">
              <IconChevron className="w-3 h-3 rotate-180" /> Back to board
            </Link>
            <StatusBadge status={s.status} size="md" />
          </>
        }
      />

      <div className="space-y-4">
        <StateTimeline current={s.status} />

        {/* 3-column bento: crew, aircraft, timing */}
        <div className="grid grid-cols-12 gap-4">
          <div className="card col-span-12 md:col-span-4 p-6">
            <div className="eyebrow mb-4">Crew</div>
            <div className="space-y-4">
              <div>
                <div className="text-[11px] uppercase tracking-wider text-ink-low">Cadet</div>
                <div className="text-ink-high text-lg font-semibold mt-0.5">
                  {userById[s.cadet_id]?.full_name ?? "—"}
                </div>
              </div>
              <div>
                <div className="text-[11px] uppercase tracking-wider text-ink-low">Instructor</div>
                <div className="text-ink-high text-lg font-semibold mt-0.5">
                  {userById[s.instructor_id]?.full_name ?? "—"}
                </div>
              </div>
            </div>
          </div>

          <div className="card col-span-12 md:col-span-4 p-6">
            <div className="eyebrow mb-4">Aircraft</div>
            {acft ? (
              <>
                <div className="font-mono text-2xl text-ink-high font-bold">[{acft.registration}]</div>
                <div className="text-ink-low text-sm">{acft.aircraft_type}</div>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-[11px] uppercase tracking-wider text-ink-low">Status</span>
                  <StatusBadge status={acft.status} />
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-[11px] uppercase tracking-wider text-ink-low">TBO</span>
                  <span className="font-mono text-sm text-ink-high">{acft.tbo_remaining_hours} h</span>
                </div>
              </>
            ) : <div className="text-ink-dim">—</div>}
          </div>

          <div className="card col-span-12 md:col-span-4 p-6">
            <div className="eyebrow mb-4">Timing</div>
            <Row label="Scheduled" v={fmtTime(s.scheduled_start)} />
            <Row label="Actual Start" v={fmtTime(s.actual_start)} />
            <Row label="Actual End" v={fmtTime(s.actual_end)} />
            <Row
              label="Delay"
              v={`${s.delay_minutes} min`}
              valueClass={s.delay_minutes > 0 ? "text-tang" : ""}
            />
          </div>
        </div>

        {/* Training panel */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="eyebrow">Training Progress</div>
            <Link to="/training" className="pill-ghost text-xs">
              Open in panel <IconChevron className="w-3 h-3" />
            </Link>
          </div>
          {training ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <ScoreTile label="Maneuver" v={training.maneuver_score} />
              <ScoreTile label="Communication" v={training.communication_score} />
              <ScoreTile label="Situational" v={training.situational_awareness_score} />
              <div className="card-2 p-4">
                <div className="text-[11px] uppercase tracking-wider text-ink-low mb-2">Status</div>
                <StatusBadge status={training.status} size="md" />
              </div>
              <div className="col-span-full">
                <div className="text-[11px] uppercase tracking-wider text-ink-low mb-2">Remarks</div>
                <div className="card-2 p-4 text-sm text-ink-mid whitespace-pre-wrap">
                  {training.remarks ?? "—"}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-ink-low text-sm">No training record yet for this sortie.</div>
          )}
        </div>

        {/* Audit */}
        <div className="card p-6">
          <div className="eyebrow mb-5">Audit Timeline</div>
          {auditQ.data && auditQ.data.length > 0 ? (
            <ol className="space-y-3">
              {auditQ.data.map((log) => (
                <li key={log.id} className="flex items-start gap-3 text-sm">
                  <div className="w-2 h-2 mt-2 rounded-full bg-lime shrink-0" />
                  <div className="flex-1">
                    <div className="text-ink-high font-mono text-sm">{log.action}</div>
                    <div className="text-xs text-ink-low">
                      {userById[log.actor_id]?.full_name ?? `User ${log.actor_id}`} ·{" "}
                      {new Date(log.created_at).toLocaleString("en-IN", { hour12: false })}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <div className="text-ink-low text-sm">No audit entries yet.</div>
          )}
        </div>
      </div>
    </>
  );
}

function fmtTime(s: string | null) {
  return s ? new Date(s).toLocaleTimeString("en-IN", { hour12: false }) : "—";
}
function Row({ label, v, valueClass = "" }: { label: string; v: string; valueClass?: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 text-sm">
      <span className="text-ink-low">{label}</span>
      <span className={`font-mono ${valueClass || "text-ink-high"}`}>{v}</span>
    </div>
  );
}
function ScoreTile({ label, v }: { label: string; v: number | null }) {
  return (
    <div className="card-2 p-4 text-center">
      <div className="text-[11px] uppercase tracking-wider text-ink-low mb-2">{label}</div>
      <div className="font-display font-bold text-4xl text-lime tabular-nums">{v ?? "—"}</div>
      <div className="text-[11px] text-ink-dim">/ 5</div>
    </div>
  );
}
