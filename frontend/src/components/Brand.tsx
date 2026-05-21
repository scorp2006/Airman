// Brand logo - circular lime "S" inspired by the Nixtio reference.

export function Brand({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sz = { sm: "w-9 h-9 text-base", md: "w-11 h-11 text-lg", lg: "w-14 h-14 text-2xl" }[size];
  return (
    <div className={`${sz} rounded-pill bg-lime text-black grid place-items-center font-display font-bold`}>
      S
    </div>
  );
}

export function Wordmark() {
  return (
    <div className="flex items-center gap-3">
      <Brand size="md" />
      <div className="leading-tight">
        <div className="font-display font-bold text-ink-high text-base tracking-tight">
          SKYNET
        </div>
        <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-ink-low">
          AIRMAN · OPS
        </div>
      </div>
    </div>
  );
}
