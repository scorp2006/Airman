// Welcome banner shown at the top of the dashboard.
// Tells each role what they can do and surfaces the most relevant action.

import { Link } from "react-router-dom";
import type { Sortie, User } from "../types";
import { IconChevron } from "./Icons";

interface Props {
  user: User;
  sorties: Sortie[];
}

export function RoleBanner({ user, sorties }: Props) {
  // Compute role-specific call-to-action
  let cta: { label: string; to: string; sub: string } | null = null;
  let blurb = "";

  switch (user.role) {
    case "ADMIN":
      blurb = "You have full access. See every sortie, every aircraft, every audit entry.";
      cta = { label: "View Sortie Board", to: "/sorties", sub: "All sorties across all roles" };
      break;
    case "DISPATCHER": {
      const scheduled = sorties.filter((s) => s.status === "SCHEDULED").length;
      const released = sorties.filter((s) => s.status === "RELEASED").length;
      const airborne = sorties.filter((s) => s.status === "AIRBORNE").length;
      blurb = `You manage the day's flying program. ${scheduled} scheduled, ${released} released, ${airborne} airborne right now.`;
      cta = {
        label: scheduled > 0 ? "Release a sortie" : "Create new sortie",
        to: "/sorties",
        sub: scheduled > 0
          ? `${scheduled} sortie${scheduled > 1 ? "s" : ""} waiting to be released`
          : "Schedule a new training flight",
      };
      break;
    }
    case "INSTRUCTOR": {
      const landed = sorties.filter(
        (s) => s.instructor_id === user.id && s.status === "LANDED",
      ).length;
      blurb = `You grade your cadets after each flight. ${landed} landed sortie${landed === 1 ? "" : "s"} need${landed === 1 ? "s" : ""} grading.`;
      cta = {
        label: landed > 0 ? "Grade cadet" : "View training",
        to: "/training",
        sub: landed > 0 ? "Submit scores for landed flights" : "No flights awaiting grading",
      };
      break;
    }
    case "CFI": {
      const pending = sorties.filter((s) => s.status === "TRAINING_SUBMITTED").length;
      blurb = `You approve or reject training submissions. ${pending} submission${pending === 1 ? "" : "s"} awaiting your review.`;
      cta = {
        label: pending > 0 ? "Review submissions" : "View training",
        to: "/training",
        sub: pending > 0 ? `${pending} record${pending > 1 ? "s" : ""} pending approval` : "Nothing pending right now",
      };
      break;
    }
    case "CADET": {
      const mine = sorties.filter((s) => s.cadet_id === user.id);
      const upcoming = mine.filter((s) => s.status === "SCHEDULED" || s.status === "RELEASED").length;
      blurb = `You see only your own flights. You have ${mine.length} total · ${upcoming} upcoming.`;
      cta = { label: "View my sorties", to: "/sorties", sub: "Your training schedule" };
      break;
    }
    case "MAINTENANCE_OFFICER":
      blurb = "You keep the fleet airworthy. File defects, resolve them, ground & ready aircraft.";
      cta = {
        label: "Open Aircraft panel",
        to: "/aircraft",
        sub: "Check fleet readiness and open defects",
      };
      break;
  }

  return (
    <div className="card p-6 mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-pill bg-lime/15 text-lime grid place-items-center shrink-0 font-display font-bold">
          {user.full_name.split(" ").map((p) => p[0]).slice(0, 2).join("")}
        </div>
        <div>
          <div className="eyebrow mb-1">
            Welcome back · <span className="text-lime">{user.role.replace("_", " ")}</span>
          </div>
          <div className="text-ink-high font-semibold text-lg">
            Hi {user.full_name.split(" ")[0]}
          </div>
          <p className="text-ink-low text-sm mt-1 max-w-2xl">{blurb}</p>
        </div>
      </div>
      {cta && (
        <Link
          to={cta.to}
          className="pill-primary shrink-0 group"
          title={cta.sub}
        >
          {cta.label}
          <IconChevron className="w-3.5 h-3.5" />
        </Link>
      )}
    </div>
  );
}
