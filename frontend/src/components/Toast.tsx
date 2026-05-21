// Lightweight toast - pill-shaped, lime/red on black.

import { useEffect, useState } from "react";

type ToastKind = "ok" | "err";
interface Toast { id: number; msg: string; kind: ToastKind }

const listeners: ((t: Toast) => void)[] = [];

export function toast(msg: string, kind: ToastKind = "ok") {
  const t: Toast = { id: Date.now() + Math.random(), msg, kind };
  listeners.forEach((fn) => fn(t));
}

export function ToastHost() {
  const [items, setItems] = useState<Toast[]>([]);
  useEffect(() => {
    const fn = (t: Toast) => {
      setItems((prev) => [...prev, t]);
      setTimeout(() => setItems((prev) => prev.filter((x) => x.id !== t.id)), 3500);
    };
    listeners.push(fn);
    return () => {
      const i = listeners.indexOf(fn);
      if (i >= 0) listeners.splice(i, 1);
    };
  }, []);
  return (
    <div className="fixed bottom-6 right-6 z-50 space-y-2">
      {items.map((t) => (
        <div
          key={t.id}
          className={`pill text-sm shadow-xl ${
            t.kind === "ok" ? "bg-lime text-black" : "bg-red-500 text-black"
          }`}
        >
          <span className="font-bold">{t.kind === "ok" ? "✓" : "✕"}</span>
          {t.msg}
        </div>
      ))}
    </div>
  );
}
