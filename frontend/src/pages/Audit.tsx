// Audit Log - clean filterable list.

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listAuditLogs, listUsers } from "../api/endpoints";
import { PageHeader } from "../components/PageHeader";
import { Loading, Empty } from "../components/Empty";

const ENTITIES = ["", "Sortie", "Aircraft", "TrainingProgress", "Defect"];
const ACTIONS = [
  "",
  "SORTIE_CREATED", "SORTIE_RELEASED", "SORTIE_AIRBORNE", "SORTIE_LANDED",
  "SORTIE_CANCELLED", "SORTIE_CLOSED",
  "AIRCRAFT_GROUNDED", "AIRCRAFT_READY",
  "TRAINING_SUBMITTED", "TRAINING_APPROVED", "TRAINING_REJECTED",
  "DEFECT_CREATED", "DEFECT_RESOLVED",
];

export default function AuditPage() {
  const [entityType, setEntityType] = useState("");
  const [action, setAction] = useState("");

  const usersQ = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const auditQ = useQuery({
    queryKey: ["audit-logs", entityType, action],
    queryFn: () => listAuditLogs({ entity_type: entityType, action }),
  });
  const userById = Object.fromEntries((usersQ.data ?? []).map((u) => [u.id, u]));

  return (
    <>
      <PageHeader title="Audit" subtitle="Append-only history of every operational action." />

      <div className="card p-5 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Entity Type</label>
            <select className="input" value={entityType} onChange={(e) => setEntityType(e.target.value)}>
              {ENTITIES.map((e) => <option key={e} value={e}>{e || "All entities"}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Action</label>
            <select className="input" value={action} onChange={(e) => setAction(e.target.value)}>
              {ACTIONS.map((a) => <option key={a} value={a}>{a || "All actions"}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <button className="pill-ghost" onClick={() => { setEntityType(""); setAction(""); }}>
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {auditQ.isLoading && <Loading label="Loading audit log" />}
      {auditQ.data && auditQ.data.length === 0 && <Empty label="No audit entries match" />}

      {auditQ.data && auditQ.data.length > 0 && (
        <div className="space-y-2">
          {auditQ.data.map((log) => (
            <div key={log.id} className="card p-5 flex items-start gap-4">
              <div className="w-10 h-10 rounded-pill bg-lime/15 text-lime grid place-items-center shrink-0 font-mono font-bold text-xs">
                {log.action.split("_")[0].slice(0, 3)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="font-mono text-ink-high font-semibold">{log.action}</span>
                  <span className="text-ink-low text-xs">
                    on {log.entity_type} <span className="font-mono">#{log.entity_id}</span>
                  </span>
                  <span className="text-ink-dim text-xs ml-auto">
                    {new Date(log.created_at).toLocaleString("en-IN", { hour12: false })}
                  </span>
                </div>
                <div className="text-ink-low text-xs mt-1">
                  by{" "}
                  <span className="text-ink-mid">
                    {userById[log.actor_id]?.full_name ?? `User ${log.actor_id}`}
                  </span>
                  {userById[log.actor_id] && (
                    <> · <span className="font-mono">{userById[log.actor_id].role}</span></>
                  )}
                </div>
                {(log.old_value || log.new_value) && (
                  <div className="font-mono text-xs text-ink-dim mt-2 truncate">
                    {log.old_value ?? "∅"} → {log.new_value ?? "∅"}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
