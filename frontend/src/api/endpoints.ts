// Thin wrappers around our API endpoints. Each function returns a Promise.
// Components call these via React Query (see hooks/).

import { api } from "./client";
import type {
  Aircraft, AuditLog, Defect, Sortie, TrainingProgress, User,
} from "../types";

// ---------- Auth ----------
export const login = (email: string) =>
  api.post<User>("/auth/login", { email }).then((r) => r.data);

export const fetchMe = () => api.get<User>("/auth/me").then((r) => r.data);

// ---------- Users ----------
export const listUsers = () => api.get<User[]>("/users").then((r) => r.data);

// ---------- Aircraft ----------
export const listAircraft = () =>
  api.get<Aircraft[]>("/aircraft").then((r) => r.data);

export const groundAircraft = (id: number) =>
  api.patch<Aircraft>(`/aircraft/${id}/ground`).then((r) => r.data);

export const readyAircraft = (id: number) =>
  api.patch<Aircraft>(`/aircraft/${id}/ready`).then((r) => r.data);

// ---------- Sorties ----------
export const listSorties = () =>
  api.get<Sortie[]>("/sorties").then((r) => r.data);

export const getSortie = (id: number) =>
  api.get<Sortie>(`/sorties/${id}`).then((r) => r.data);

export const sortieAction = (id: number, action: string) =>
  api.patch<Sortie>(`/sorties/${id}/${action}`).then((r) => r.data);

export interface SortieCreatePayload {
  sortie_number: string;
  cadet_id: number;
  instructor_id: number;
  aircraft_id: number;
  base_id: number;
  lesson_type: string;
  scheduled_start: string;
  scheduled_end: string;
}
export const createSortie = (payload: SortieCreatePayload) =>
  api.post<Sortie>("/sorties", payload).then((r) => r.data);

// ---------- Training Progress ----------
export interface TrainingSubmitPayload {
  sortie_id: number;
  maneuver_score: number;
  communication_score: number;
  situational_awareness_score: number;
  remarks: string;
}
export const submitTraining = (payload: TrainingSubmitPayload) =>
  api.post<TrainingProgress>("/training-progress", payload).then((r) => r.data);

export const getTrainingBySortie = (sortieId: number) =>
  api.get<TrainingProgress>(`/training-progress/${sortieId}`).then((r) => r.data);

export const approveTraining = (id: number) =>
  api.patch<TrainingProgress>(`/training-progress/${id}/approve`).then((r) => r.data);

export const rejectTraining = (id: number, remarks: string) =>
  api.patch<TrainingProgress>(`/training-progress/${id}/reject`, { remarks }).then((r) => r.data);

// ---------- Defects ----------
export interface DefectCreatePayload {
  aircraft_id: number;
  sortie_id?: number | null;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  description: string;
}
export const listDefects = () =>
  api.get<Defect[]>("/defects").then((r) => r.data);
export const createDefect = (payload: DefectCreatePayload) =>
  api.post<Defect>("/defects", payload).then((r) => r.data);
export const resolveDefect = (id: number) =>
  api.patch<Defect>(`/defects/${id}/resolve`).then((r) => r.data);

// ---------- Audit logs ----------
export const listAuditLogs = (filters: Record<string, string | number | undefined> = {}) => {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== ""),
  );
  return api.get<AuditLog[]>("/audit-logs", { params }).then((r) => r.data);
};
