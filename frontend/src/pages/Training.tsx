// Training screen - 2-column: sortie picker + form/approval.

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listSorties, listUsers, getTrainingBySortie, submitTraining, approveTraining, rejectTraining,
} from "../api/endpoints";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Loading, Empty } from "../components/Empty";
import { toast } from "../components/Toast";
import { useAuth } from "../context/AuthContext";

export default function TrainingPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const sortiesQ = useQuery({ queryKey: ["sorties"], queryFn: listSorties });
  const usersQ = useQuery({ queryKey: ["users"], queryFn: listUsers });

  const [selectedId, setSelectedId] = useState<number | null>(null);

  const relevant = useMemo(() => {
    if (!user) return [];
    const list = sortiesQ.data ?? [];
    if (user.role === "INSTRUCTOR")
      return list.filter((s) => s.instructor_id === user.id && ["LANDED", "TRAINING_SUBMITTED", "TRAINING_APPROVED"].includes(s.status));
    if (user.role === "CFI" || user.role === "ADMIN")
      return list.filter((s) => ["TRAINING_SUBMITTED", "TRAINING_APPROVED", "LANDED"].includes(s.status));
    if (user.role === "CADET")
      return list.filter((s) => s.cadet_id === user.id && ["TRAINING_SUBMITTED", "TRAINING_APPROVED", "CLOSED"].includes(s.status));
    return list;
  }, [user, sortiesQ.data]);

  if (selectedId === null && relevant.length > 0) setSelectedId(relevant[0].id);
  if (sortiesQ.isLoading) return <Loading />;

  return (
    <>
      <PageHeader
        title="Training"
        subtitle="Instructor → submit · CFI → approve · Cadet → view"
      />

      <div className="grid grid-cols-12 gap-4">
        {/* Sortie picker */}
        <div className="card col-span-12 lg:col-span-4 p-5">
          <div className="eyebrow mb-4">Eligible Sorties · {relevant.length}</div>
          {relevant.length === 0 ? (
            <div className="text-ink-low text-sm">Nothing in scope right now.</div>
          ) : (
            <ul className="space-y-2">
              {relevant.map((s) => (
                <li key={s.id}>
                  <button
                    onClick={() => setSelectedId(s.id)}
                    className={`w-full text-left p-4 rounded-2xl border transition ${
                      selectedId === s.id
                        ? "bg-bg-card2 border-lime/60"
                        : "border-bg-line/40 hover:bg-bg-card2"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-ink-high font-semibold">{s.sortie_number}</span>
                      <StatusBadge status={s.status} />
                    </div>
                    <div className="text-ink-low text-xs">{s.lesson_type}</div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Panel */}
        <div className="col-span-12 lg:col-span-8">
          {selectedId ? (
            <TrainingPanel
              sortieId={selectedId}
              users={usersQ.data ?? []}
              onChanged={() => {
                qc.invalidateQueries({ queryKey: ["sorties"] });
                qc.invalidateQueries({ queryKey: ["training", selectedId] });
              }}
            />
          ) : (
            <Empty label="Select a sortie" />
          )}
        </div>
      </div>
    </>
  );
}

function TrainingPanel({
  sortieId, onChanged,
}: {
  sortieId: number;
  users: { id: number; full_name: string }[];
  onChanged: () => void;
}) {
  const { user } = useAuth();
  const trainingQ = useQuery({
    queryKey: ["training", sortieId],
    queryFn: () => getTrainingBySortie(sortieId),
    retry: false,
  });
  const sortiesQ = useQuery({ queryKey: ["sorties"], queryFn: listSorties });
  const sortie = (sortiesQ.data ?? []).find((s) => s.id === sortieId);

  const [scores, setScores] = useState({ m: 4, c: 4, s: 4, remarks: "" });

  const submitMut = useMutation({
    mutationFn: submitTraining,
    onSuccess: () => { toast("Training submitted"); onChanged(); trainingQ.refetch(); },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Submission failed", "err"),
  });

  const approveMut = useMutation({
    mutationFn: (id: number) => approveTraining(id),
    onSuccess: () => { toast("Training approved"); onChanged(); trainingQ.refetch(); },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Approval failed", "err"),
  });

  const [rejectReason, setRejectReason] = useState("");
  const rejectMut = useMutation({
    mutationFn: ({ id, remarks }: { id: number; remarks: string }) => rejectTraining(id, remarks),
    onSuccess: () => { toast("Training rejected"); onChanged(); trainingQ.refetch(); setRejectReason(""); },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Reject failed", "err"),
  });

  const isInstructor = user?.role === "INSTRUCTOR" || user?.role === "ADMIN";
  const isCFI = user?.role === "CFI" || user?.role === "ADMIN";
  const t = trainingQ.data;

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="eyebrow">Sortie {sortie?.sortie_number}</div>
          <div className="text-ink-high font-semibold text-lg mt-1">{sortie?.lesson_type}</div>
        </div>
        {t && <StatusBadge status={t.status} size="md" />}
      </div>

      {/* Submit form: instructor + sortie LANDED + no record yet */}
      {!t && isInstructor && sortie?.status === "LANDED" && (
        <SubmitForm
          scores={scores}
          setScores={setScores}
          pending={submitMut.isPending}
          onSubmit={() =>
            submitMut.mutate({
              sortie_id: sortieId,
              maneuver_score: scores.m,
              communication_score: scores.c,
              situational_awareness_score: scores.s,
              remarks: scores.remarks,
            })
          }
        />
      )}

      {/* Existing record */}
      {t && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-5">
            <ScoreCard label="Maneuver" v={t.maneuver_score} />
            <ScoreCard label="Communication" v={t.communication_score} />
            <ScoreCard label="Situational" v={t.situational_awareness_score} />
          </div>
          <div className="mb-5">
            <div className="label">Remarks</div>
            <div className="card-2 p-4 text-sm text-ink-mid whitespace-pre-wrap">{t.remarks ?? "—"}</div>
          </div>

          {/* CFI actions */}
          {isCFI && t.status === "SUBMITTED" && (
            <div className="pt-5 border-t border-bg-line/60 space-y-4">
              <div className="flex gap-2">
                <button
                  className="pill-primary"
                  disabled={approveMut.isPending}
                  onClick={() => approveMut.mutate(t.id)}
                >
                  Approve Training
                </button>
              </div>
              <div>
                <div className="label">Or reject with a reason</div>
                <div className="flex gap-2">
                  <input
                    className="input"
                    placeholder="Why are you rejecting this?"
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                  />
                  <button
                    className="pill-danger shrink-0"
                    disabled={rejectMut.isPending || !rejectReason.trim()}
                    onClick={() => rejectMut.mutate({ id: t.id, remarks: rejectReason })}
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {!t && !isInstructor && <Empty label="No progress record yet" />}
      {!t && isInstructor && sortie?.status !== "LANDED" && (
        <div className="text-ink-low text-sm">
          Sortie must be in LANDED state before training progress can be submitted.
        </div>
      )}
    </div>
  );
}

function ScoreCard({ label, v }: { label: string; v: number | null }) {
  return (
    <div className="card-2 p-4 text-center">
      <div className="text-[11px] uppercase tracking-wider text-ink-low mb-2">{label}</div>
      <div className="font-display font-bold text-4xl text-lime tabular-nums">{v ?? "—"}</div>
      <div className="text-[11px] text-ink-dim">/ 5</div>
    </div>
  );
}

function SubmitForm({
  scores, setScores, pending, onSubmit,
}: {
  scores: { m: number; c: number; s: number; remarks: string };
  setScores: (v: { m: number; c: number; s: number; remarks: string }) => void;
  pending: boolean;
  onSubmit: () => void;
}) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-3">
        <NumField label="Maneuver" value={scores.m} onChange={(v) => setScores({ ...scores, m: v })} />
        <NumField label="Communication" value={scores.c} onChange={(v) => setScores({ ...scores, c: v })} />
        <NumField label="Situational" value={scores.s} onChange={(v) => setScores({ ...scores, s: v })} />
      </div>
      <div>
        <label className="label">Remarks</label>
        <textarea
          className="input min-h-[120px]"
          value={scores.remarks}
          onChange={(e) => setScores({ ...scores, remarks: e.target.value })}
          placeholder="Notes about the cadet's performance, areas to improve, what went well…"
        />
      </div>
      <button
        className="pill-primary"
        disabled={pending || !scores.remarks.trim()}
        onClick={onSubmit}
      >
        {pending ? "Submitting…" : "Submit Training Progress"}
      </button>
    </div>
  );
}

function NumField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label className="label">{label} (1-5)</label>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            className={`flex-1 h-12 rounded-2xl font-display font-bold text-lg transition ${
              value === n ? "bg-lime text-black" : "bg-bg-card2 text-ink-low hover:bg-bg-chip"
            }`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}
