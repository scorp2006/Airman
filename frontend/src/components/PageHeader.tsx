// Page title row - big bold heading + filter pills on the right.

import type { ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  right,
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-6 mb-8">
      <div>
        <h1 className="font-display font-bold text-5xl text-ink-high tracking-tight uppercase">
          {title}
        </h1>
        {subtitle && <p className="text-ink-low text-sm mt-2">{subtitle}</p>}
      </div>
      {right && <div className="flex items-center gap-2 flex-wrap">{right}</div>}
    </div>
  );
}
