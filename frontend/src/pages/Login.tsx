// Login - clean centered card with role picker.
// Fixed: cards now use a stable 3-column grid on wide screens with proper gap.

import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { listUsers, login as loginApi } from "../api/endpoints";
import { useAuth } from "../context/AuthContext";
import { Loading } from "../components/Empty";
import { toast } from "../components/Toast";

const ROLE_BLURB: Record<string, string> = {
  ADMIN: "Full system access",
  DISPATCHER: "Schedule and manage daily flights",
  INSTRUCTOR: "Submit cadet training scores",
  CFI: "Approve or reject training",
  CADET: "View your own training records",
  MAINTENANCE_OFFICER: "Aircraft readiness & defects",
};

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const usersQuery = useQuery({ queryKey: ["users"], queryFn: listUsers });

  async function pickUser(email: string) {
    try {
      const u = await loginApi(email);
      login(u);
      toast(`Signed in as ${u.role.replace("_", " ")}`);
      navigate("/dashboard");
    } catch {
      toast("Sign-in failed", "err");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 py-12">
      <div className="w-full max-w-5xl">
        {/* Brand header */}
        <div className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-pill bg-lime text-black grid place-items-center font-display font-bold text-2xl shrink-0">
              S
            </div>
            <div>
              <div className="font-display font-bold text-3xl text-ink-high tracking-tight">
                SKYNET
              </div>
              <div className="text-[11px] font-mono uppercase tracking-[0.22em] text-ink-low mt-0.5">
                AIRMAN · Flight Operations
              </div>
            </div>
          </div>
          <div className="text-right hidden md:block">
            <div className="text-ink-low text-xs">v0.1.0</div>
            <div className="text-ink-dim text-[11px]">Mock auth · pick a role</div>
          </div>
        </div>

        {/* Main card */}
        <div className="card p-8 md:p-10">
          <div className="mb-8">
            <h1 className="font-display font-bold text-4xl md:text-5xl text-ink-high tracking-tight">
              Sign in to console
            </h1>
            <p className="text-ink-low text-sm mt-3 max-w-2xl">
              Skynet is multi-role. Each operator sees a different set of actions and data
              scoped to what they're allowed to do. Click any role below to enter as that user.
            </p>
          </div>

          {usersQuery.isLoading && <Loading label="Loading operators" />}
          {usersQuery.isError && (
            <div className="text-red-400 text-sm">
              Cannot reach backend on port 8000. Make sure the FastAPI server is running.
            </div>
          )}

          {/* 3-column grid on large screens — gives each card breathing room */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {usersQuery.data?.map((u) => (
              <button
                key={u.id}
                onClick={() => pickUser(u.email)}
                className="card-2 hover:border-lime/60 hover:bg-bg-chip text-left p-5 transition group flex flex-col"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="chip bg-lime/15 text-lime border border-lime/40">
                    {u.role.replace("_", " ")}
                  </span>
                  <span className="text-[11px] font-mono text-ink-dim">#{u.id}</span>
                </div>
                <div className="text-ink-high font-semibold text-base">{u.full_name}</div>
                <div className="text-ink-low text-xs mt-1 mb-4 truncate">{u.email}</div>
                <div className="text-ink-dim text-xs mt-auto group-hover:text-ink-mid transition">
                  → {ROLE_BLURB[u.role]}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-8 text-center text-[11px] uppercase tracking-widest text-ink-dim">
          AIRMAN Aeronautics · Skynet Operations · Technical Assessment
        </div>
      </div>
    </div>
  );
}
