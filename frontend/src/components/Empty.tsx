// Loading / empty / error states.

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-ink-low text-sm">
      <span className="inline-block w-2 h-2 rounded-pill bg-lime animate-pulse-soft" />
      {label}…
    </div>
  );
}

export function Empty({ label = "Nothing here yet" }: { label?: string }) {
  return (
    <div className="card p-10 text-center">
      <div className="text-ink-low text-sm">{label}</div>
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="card p-6 border-red-500/40">
      <div className="text-red-400 text-xs font-semibold uppercase tracking-wider mb-2">Error</div>
      <div className="text-ink-mid text-sm">{message}</div>
    </div>
  );
}
