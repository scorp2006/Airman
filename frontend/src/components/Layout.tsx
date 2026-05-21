// Main app shell.
// - Wider sidebar with icon + LABEL for every nav item (no more guessing)
// - Topbar has NO duplicate brand (sidebar already shows it)
// - Topbar shows page-level greeting + bell + user chip

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listAuditLogs } from "../api/endpoints";
import { NotificationPanel } from "./NotificationPanel";
import type { UserRole } from "../types";
import {
  IconGrid, IconPlane, IconBook, IconWrench, IconClipboard,
  IconBell, IconLogout, IconSearch,
} from "./Icons";

// Same filters used inside NotificationPanel - kept here for the badge count.
const ROLE_FILTERS: Record<UserRole, string[]> = {
  ADMIN: [],
  DISPATCHER: ["SORTIE_CREATED","SORTIE_RELEASED","SORTIE_AIRBORNE","SORTIE_LANDED","AIRCRAFT_GROUNDED","DEFECT_CREATED"],
  INSTRUCTOR: ["SORTIE_LANDED", "TRAINING_REJECTED"],
  CFI: ["TRAINING_SUBMITTED"],
  CADET: ["TRAINING_APPROVED", "SORTIE_CLOSED"],
  MAINTENANCE_OFFICER: ["DEFECT_CREATED", "AIRCRAFT_GROUNDED", "SORTIE_LANDED"],
};

interface NavItem {
  to: string;
  label: string;
  Icon: typeof IconGrid;
}

const NAV: NavItem[] = [
  { to: "/dashboard", label: "Operations", Icon: IconGrid },
  { to: "/sorties",   label: "Sorties",    Icon: IconPlane },
  { to: "/training",  label: "Training",   Icon: IconBook },
  { to: "/aircraft",  label: "Aircraft",   Icon: IconWrench },
  { to: "/audit",     label: "Audit Log",  Icon: IconClipboard },
];

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [notifOpen, setNotifOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const initials = user
    ? user.full_name.split(" ").map((p) => p[0]).slice(0, 2).join("")
    : "?";

  // Live notification count - filtered to what this role cares about.
  const auditQ = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => listAuditLogs({}),
    refetchInterval: 15000,  // poll every 15s
  });
  const filterList = user ? ROLE_FILTERS[user.role] : [];
  const unreadCount = (auditQ.data ?? []).filter((log) =>
    filterList.length === 0 ? true : filterList.includes(log.action),
  ).slice(0, 10).length;

  return (
    <div className="min-h-screen flex">
      {/* Sidebar — wider, with labels. Sticks full-height so sign-out is always visible. */}
      <aside className="w-56 shrink-0 flex flex-col py-6 border-r border-bg-line/60 bg-bg-base h-screen sticky top-0">
        {/* Brand at top of sidebar (only place it appears) */}
        <div className="px-5 mb-8 flex items-center gap-3">
          <div className="w-10 h-10 rounded-pill bg-lime text-black grid place-items-center font-display font-bold text-lg shrink-0">
            S
          </div>
          <div className="leading-tight">
            <div className="font-display font-bold text-ink-high text-base tracking-tight">
              SKYNET
            </div>
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-ink-low">
              Flight Ops
            </div>
          </div>
        </div>

        {/* Nav with icon + label */}
        <nav className="flex-1 px-3 space-y-1">
          {NAV.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-2xl transition text-sm ${
                  isActive
                    ? "bg-lime text-black font-semibold"
                    : "text-ink-mid hover:text-ink-high hover:bg-bg-card"
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Sign out at bottom */}
        <div className="px-3 mt-4">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-2xl text-ink-low hover:text-red-400 hover:bg-bg-card transition text-sm"
          >
            <IconLogout className="w-5 h-5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main column */}
      <main className="flex-1 min-w-0 flex flex-col">
        {/* Topbar - search + bell + user chip (NO duplicate brand) */}
        <header className="px-8 py-5 flex items-center justify-between gap-6 border-b border-bg-line/40">
          {/* Search pill */}
          <div className="flex-1 max-w-md">
            <div className="pill-ghost w-full justify-start cursor-text">
              <IconSearch className="w-4 h-4 text-ink-low" />
              <span className="text-ink-low text-sm">
                Search sorties, aircraft, cadets…
              </span>
            </div>
          </div>

          {/* User chip */}
          {user && (
            <div className="flex items-center gap-3">
              <div className="relative">
                <button
                  onClick={() => setNotifOpen((v) => !v)}
                  className="icon-btn relative"
                  title="Notifications"
                >
                  <IconBell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-pill bg-tang text-black text-[10px] font-bold grid place-items-center">
                      {unreadCount > 9 ? "9+" : unreadCount}
                    </span>
                  )}
                </button>
                <NotificationPanel open={notifOpen} onClose={() => setNotifOpen(false)} />
              </div>
              <div className="flex items-center gap-3 pl-3 border-l border-bg-line">
                <div className="text-right leading-tight">
                  <div className="text-ink-high text-sm font-semibold">
                    {user.full_name}
                  </div>
                  <div className="text-ink-low text-[11px] font-mono uppercase tracking-wider">
                    {user.role.replace("_", " ")}
                  </div>
                </div>
                <div className="w-11 h-11 rounded-pill bg-bg-card border border-bg-line grid place-items-center text-ink-high font-display font-semibold">
                  {initials}
                </div>
              </div>
            </div>
          )}
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-auto px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
