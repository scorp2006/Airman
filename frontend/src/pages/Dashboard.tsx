// Operations Dashboard - Nixtio-inspired bento grid with big numbers + charts.

import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  listAircraft, listSorties, listDefects, listAuditLogs, listUsers,
} from "../api/endpoints";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Loading } from "../components/Empty";
import { IconChevron } from "../components/Icons";
import { useAuth } from "../context/AuthContext";
import { RoleBanner } from "../components/RoleBanner";

export default function DashboardPage() {
  const { user } = useAuth();
  const sortiesQ = useQuery({ queryKey: ["sorties"], queryFn: listSorties });
  const aircraftQ = useQuery({ queryKey: ["aircraft"], queryFn: listAircraft });
  const defectsQ = useQuery({ queryKey: ["defects"], queryFn: listDefects });
  const usersQ = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const auditQ = useQuery({ queryKey: ["audit-logs"], queryFn: () => listAuditLogs({}) });

  if (sortiesQ.isLoading || aircraftQ.isLoading) return <Loading />;

  const sorties = sortiesQ.data ?? [];
  const aircraft = aircraftQ.data ?? [];
  const defects = defectsQ.data ?? [];
  const audit = auditQ.data ?? [];
  const userById = Object.fromEntries((usersQ.data ?? []).map((u) => [u.id, u]));

  // Aggregations
  const today = new Date().toDateString();
  const todaySorties = sorties.filter((s) => new Date(s.scheduled_start).toDateString() === today);
  const airborne = sorties.filter((s) => s.status === "AIRBORNE").length;
  const released = sorties.filter((s) => s.status === "RELEASED").length;
  const landed = sorties.filter((s) => s.status === "LANDED").length;
  const grounded = aircraft.filter((a) => a.status === "GROUNDED").length;
  const ready = aircraft.filter((a) => a.status === "READY").length;
  const pendingApproval = sorties.filter((s) => s.status === "TRAINING_SUBMITTED").length;
  const openDefects = defects.filter((d) => d.status === "OPEN").length;
  const totalSorties = sorties.length;

  // Fleet readiness %
  const fleetReady = aircraft.length > 0 ? Math.round((ready / aircraft.length) * 100) : 0;

  return (
    <>
      <PageHeader
        title="Operations"
        right={
          <>
            <button className="pill-ghost">Date: Today <IconChevron className="w-3 h-3" /></button>
            <button className="pill-ghost">Base: All <IconChevron className="w-3 h-3" /></button>
          </>
        }
      />

      {/* Role-aware welcome banner */}
      {user && <RoleBanner user={user} sorties={sorties} />}

      {/* Bento grid */}
      <div className="grid grid-cols-12 gap-4">
        {/* Big stat: today's ops */}
        <BigStat
          className="col-span-12 md:col-span-4"
          eyebrow="Sorties Today"
          value={todaySorties.length}
          sub={`${airborne} airborne · ${released} released`}
          accent="lime"
        />
        {/* Big stat: fleet readiness */}
        <BigStat
          className="col-span-12 md:col-span-4"
          eyebrow="Fleet Readiness"
          value={`${fleetReady}%`}
          sub={`${ready} of ${aircraft.length} aircraft ready`}
          accent={fleetReady >= 70 ? "lime" : "tang"}
        />
        {/* Big stat: training queue */}
        <BigStat
          className="col-span-12 md:col-span-4"
          eyebrow="Awaiting CFI"
          value={pendingApproval}
          sub="Training records to approve"
          accent="tang"
        />

        {/* Mini KPI strip */}
        <div className="col-span-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          <MiniStat label="Airborne" value={airborne} dot="lime" />
          <MiniStat label="Released" value={released} dot="white" />
          <MiniStat label="Landed" value={landed} dot="white" />
          <MiniStat label="Open Defects" value={openDefects} dot="tang" />
        </div>

        {/* Live sorties */}
        <div className="card col-span-12 lg:col-span-7 p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="eyebrow">Live Sorties</div>
              <div className="text-ink-high font-semibold text-lg">{totalSorties} total</div>
            </div>
            <Link to="/sorties" className="pill-ghost text-xs">View all <IconChevron className="w-3 h-3" /></Link>
          </div>
          <div className="space-y-2">
            {sorties.slice(0, 5).map((s) => {
              const acft = aircraft.find((a) => a.id === s.aircraft_id);
              return (
                <Link
                  key={s.id}
                  to={`/sorties/${s.id}`}
                  className="flex items-center justify-between gap-4 py-3 px-4 rounded-2xl bg-bg-card2 hover:bg-bg-chip transition border border-bg-line/40"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <span className="font-mono text-ink-high font-semibold">{s.sortie_number}</span>
                    <span className="text-ink-low text-sm truncate">{s.lesson_type}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {acft && <span className="font-mono text-ink-low text-xs">[{acft.registration}]</span>}
                    <StatusBadge status={s.status} />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Fleet */}
        <div className="card col-span-12 lg:col-span-5 p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="eyebrow">Fleet</div>
              <div className="text-ink-high font-semibold text-lg">{aircraft.length} aircraft</div>
            </div>
            <Link to="/aircraft" className="pill-ghost text-xs">Manage <IconChevron className="w-3 h-3" /></Link>
          </div>
          <div className="space-y-3">
            {aircraft.map((a) => {
              const aDefects = defects.filter((d) => d.aircraft_id === a.id && d.status === "OPEN").length;
              return (
                <div
                  key={a.id}
                  className="flex items-center justify-between gap-3 py-3 px-4 rounded-2xl bg-bg-card2 border border-bg-line/40"
                >
                  <div className="min-w-0">
                    <div className="font-mono text-ink-high font-semibold">[{a.registration}]</div>
                    <div className="text-ink-low text-xs">{a.aircraft_type}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {aDefects > 0 && (
                      <span className="chip bg-tang/15 text-tang border border-tang/30 px-2 py-0.5 text-[10px]">
                        {aDefects} DEF
                      </span>
                    )}
                    <StatusBadge status={a.status} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent activity */}
        <div className="card col-span-12 p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="eyebrow">Recent Activity</div>
              <div className="text-ink-high font-semibold text-lg">Last 10 events</div>
            </div>
            <Link to="/audit" className="pill-ghost text-xs">View audit log <IconChevron className="w-3 h-3" /></Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {audit.slice(0, 10).map((log) => (
              <div
                key={log.id}
                className="flex items-center gap-3 py-2 px-3 rounded-xl bg-bg-card2 border border-bg-line/30"
              >
                <span className="w-2 h-2 rounded-full bg-lime shrink-0" />
                <span className="font-mono text-xs text-ink-mid">{log.action}</span>
                <span className="text-xs text-ink-low truncate flex-1">
                  · {log.entity_type} #{log.entity_id}
                </span>
                <span className="text-[11px] text-ink-dim shrink-0">
                  {userById[log.actor_id]?.full_name?.split(" ")[0] ?? `#${log.actor_id}`}
                </span>
              </div>
            ))}
            {audit.length === 0 && (
              <div className="text-ink-low text-sm">No activity yet.</div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function BigStat({
  className, eyebrow, value, sub, accent,
}: {
  className?: string;
  eyebrow: string;
  value: number | string;
  sub: string;
  accent: "lime" | "tang" | "white";
}) {
  const numColor = { lime: "text-lime", tang: "text-tang", white: "text-ink-high" }[accent];
  return (
    <div className={`card p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <span className="eyebrow">{eyebrow}</span>
        <span className={`w-2 h-2 rounded-full ${accent === "lime" ? "bg-lime" : accent === "tang" ? "bg-tang" : "bg-white"} animate-pulse-soft`} />
      </div>
      <div className={`font-display font-bold text-6xl tracking-tight ${numColor} tabular-nums`}>
        {value}
      </div>
      <div className="text-ink-low text-xs mt-3">{sub}</div>
    </div>
  );
}

function MiniStat({ label, value, dot }: { label: string; value: number; dot: "lime" | "tang" | "white" }) {
  const dotCls = { lime: "bg-lime", tang: "bg-tang", white: "bg-white" }[dot];
  return (
    <div className="card-2 p-4 flex items-center justify-between">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-low">{label}</div>
        <div className="font-display font-bold text-3xl text-ink-high mt-1 tabular-nums">{value}</div>
      </div>
      <span className={`w-2.5 h-2.5 rounded-full ${dotCls}`} />
    </div>
  );
}
