// CreateSortieModal - dispatcher-only form to schedule a new sortie.
//
// Dropdowns auto-populate from /users and /aircraft. We default scheduled
// times to "an hour from now → an hour after that" so the form is fillable
// in seconds.

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createSortie, listAircraft, listUsers } from "../api/endpoints";
import { toast } from "./Toast";
import { IconX } from "./Icons";

const LESSON_TYPES = [
  "Circuits",
  "Navigation",
  "Stalls",
  "Landings",
  "Emergency Procedures",
  "Instrument Flying",
  "Solo Cross Country",
];

// Format a Date as the `datetime-local` input expects: YYYY-MM-DDTHH:mm
function toLocalInputValue(d: Date) {
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function CreateSortieModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const usersQ = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const aircraftQ = useQuery({ queryKey: ["aircraft"], queryFn: listAircraft });

  // Build defaults: next hour + one hour duration
  const now = new Date();
  const start = new Date(now.getTime() + 60 * 60 * 1000);
  const end = new Date(start.getTime() + 60 * 60 * 1000);

  const [form, setForm] = useState({
    sortie_number: "",
    cadet_id: 0,
    instructor_id: 0,
    aircraft_id: 0,
    lesson_type: "Circuits",
    scheduled_start: toLocalInputValue(start),
    scheduled_end: toLocalInputValue(end),
  });

  // Auto-generate a sortie number and pre-select first valid options on open.
  useEffect(() => {
    if (!open) return;
    const seq = Math.floor(Math.random() * 900 + 100); // SOR-XXX random 3-digit
    const cadet = (usersQ.data ?? []).find((u) => u.role === "CADET");
    const instructor = (usersQ.data ?? []).find((u) => u.role === "INSTRUCTOR");
    const aircraft = (aircraftQ.data ?? []).find((a) => a.status !== "GROUNDED");
    setForm((f) => ({
      ...f,
      sortie_number: `SOR-${seq}`,
      cadet_id: cadet?.id ?? 0,
      instructor_id: instructor?.id ?? 0,
      aircraft_id: aircraft?.id ?? 0,
    }));
  }, [open, usersQ.data, aircraftQ.data]);

  const createMut = useMutation({
    mutationFn: createSortie,
    onSuccess: () => {
      toast("Sortie scheduled");
      qc.invalidateQueries({ queryKey: ["sorties"] });
      qc.invalidateQueries({ queryKey: ["audit-logs"] });
      onClose();
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast(e.response?.data?.detail ?? "Could not create sortie", "err"),
  });

  if (!open) return null;

  const cadets = (usersQ.data ?? []).filter((u) => u.role === "CADET");
  const instructors = (usersQ.data ?? []).filter((u) => u.role === "INSTRUCTOR");
  const availableAircraft = (aircraftQ.data ?? []).filter((a) => a.status !== "GROUNDED");
  const groundedAircraft = (aircraftQ.data ?? []).filter((a) => a.status === "GROUNDED");

  const valid =
    form.sortie_number.trim() &&
    form.cadet_id > 0 &&
    form.instructor_id > 0 &&
    form.aircraft_id > 0 &&
    form.scheduled_start &&
    form.scheduled_end;

  function submit() {
    const cadet = cadets.find((c) => c.id === form.cadet_id);
    if (!cadet) return;
    createMut.mutate({
      ...form,
      base_id: cadet.base_id ?? 1, // use cadet's base
      scheduled_start: new Date(form.scheduled_start).toISOString(),
      scheduled_end: new Date(form.scheduled_end).toISOString(),
    });
  }

  return (
    <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm grid place-items-center p-6">
      <div className="card w-full max-w-2xl p-6 md:p-8 relative max-h-[90vh] overflow-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 icon-btn"
          aria-label="Close"
        >
          <IconX />
        </button>

        <div className="mb-6">
          <div className="eyebrow mb-1">Dispatcher · New Schedule</div>
          <h2 className="font-display font-bold text-3xl text-ink-high tracking-tight">
            Schedule a sortie
          </h2>
          <p className="text-ink-low text-sm mt-2">
            Create a new training flight. It will start in SCHEDULED status and can be
            released when the cadet and instructor are ready to fly.
          </p>
        </div>

        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Sortie Number</label>
              <input
                className="input"
                value={form.sortie_number}
                onChange={(e) => setForm({ ...form, sortie_number: e.target.value })}
                placeholder="SOR-101"
              />
            </div>
            <div>
              <label className="label">Lesson Type</label>
              <select
                className="input"
                value={form.lesson_type}
                onChange={(e) => setForm({ ...form, lesson_type: e.target.value })}
              >
                {LESSON_TYPES.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Cadet</label>
              <select
                className="input"
                value={form.cadet_id}
                onChange={(e) => setForm({ ...form, cadet_id: Number(e.target.value) })}
              >
                {cadets.length === 0 && <option value={0}>No cadets found</option>}
                {cadets.map((u) => (
                  <option key={u.id} value={u.id}>{u.full_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Instructor</label>
              <select
                className="input"
                value={form.instructor_id}
                onChange={(e) => setForm({ ...form, instructor_id: Number(e.target.value) })}
              >
                {instructors.length === 0 && <option value={0}>No instructors</option>}
                {instructors.map((u) => (
                  <option key={u.id} value={u.id}>{u.full_name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="label">Aircraft</label>
            <select
              className="input"
              value={form.aircraft_id}
              onChange={(e) => setForm({ ...form, aircraft_id: Number(e.target.value) })}
            >
              {availableAircraft.length === 0 && <option value={0}>No aircraft available</option>}
              {availableAircraft.map((a) => (
                <option key={a.id} value={a.id}>
                  [{a.registration}] {a.aircraft_type} — {a.status}
                </option>
              ))}
            </select>
            {groundedAircraft.length > 0 && (
              <div className="text-[11px] text-ink-dim mt-2">
                {groundedAircraft.length} aircraft hidden (grounded — cannot be scheduled).
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Scheduled Start</label>
              <input
                type="datetime-local"
                className="input"
                value={form.scheduled_start}
                onChange={(e) => setForm({ ...form, scheduled_start: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Scheduled End</label>
              <input
                type="datetime-local"
                className="input"
                value={form.scheduled_end}
                onChange={(e) => setForm({ ...form, scheduled_end: e.target.value })}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button className="pill-ghost" onClick={onClose}>Cancel</button>
            <button
              className="pill-primary"
              disabled={!valid || createMut.isPending}
              onClick={submit}
            >
              {createMut.isPending ? "Scheduling…" : "Schedule Sortie"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
