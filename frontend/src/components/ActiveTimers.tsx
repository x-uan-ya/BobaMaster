import React, { useEffect, useState } from "react";
import { useDashboard } from "../store/dashboardStore";
import type { ActiveBrewTimer } from "../types";

function remaining(timer: ActiveBrewTimer): { label: string; pct: number; done: boolean } {
  const elapsed = Date.now() - timer.started_at;
  const left = Math.max(0, timer.cook_time_ms - elapsed);
  const pct  = Math.min(100, Math.round((elapsed / timer.cook_time_ms) * 100));
  if (left === 0) return { label: "✅ Ready!", pct: 100, done: true };
  const mins = Math.floor(left / 60_000);
  const secs = Math.floor((left % 60_000) / 1000);
  return { label: `${mins}:${secs.toString().padStart(2, "0")} remaining`, pct, done: false };
}

const TimerCard: React.FC<{ timer: ActiveBrewTimer }> = ({ timer }) => {
  const { dispatch } = useDashboard();
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const { label, pct, done } = remaining(timer);
  const barColor = done ? "#16a34a" : pct > 70 ? "#1a6b5e" : "#d97706";

  return (
    <div
      role="status"
      aria-label={`${timer.label}: ${label}`}
      style={{
        backgroundColor: done ? "#dcfce7" : "#f9f9f9",
        border: `1px solid ${done ? "#16a34a" : "#e5e7eb"}`,
        borderRadius: 10, padding: "12px 14px",
        marginBottom: 10,
        animation: "fade-in 0.2s ease-out",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: "#1f2937" }}>🍳 {timer.label}</span>
        <button
          onClick={() => dispatch({ type: "REMOVE_BREW_TIMER", payload: timer.id })}
          aria-label={`Remove ${timer.label} timer`}
          style={{
            background: "none", border: "none", cursor: "pointer",
            color: "#9ca3af", fontSize: 14, padding: "2px 6px",
            borderRadius: 4, lineHeight: 1,
          }}
        >✕</button>
      </div>

      {/* Progress bar */}
      <div style={{ backgroundColor: "#e5e7eb", borderRadius: 99, height: 8, overflow: "hidden", marginBottom: 6 }}
           role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div style={{
          width: `${pct}%`, height: "100%",
          backgroundColor: barColor, borderRadius: 99,
          transition: "width 1s linear",
        }} />
      </div>

      <p style={{ fontSize: 12, color: done ? "#16a34a" : "#6b7280", margin: 0, fontWeight: 600 }}>
        {label}
      </p>
    </div>
  );
};

export const ActiveTimers: React.FC = () => {
  const { state } = useDashboard();
  if (state.activeTimers.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "24px 0", color: "#9ca3af" }}>
        <p style={{ fontSize: 28, margin: "0 0 8px" }}>🫙</p>
        <p style={{ fontSize: 13, margin: 0 }}>No Active Brews</p>
        <p style={{ fontSize: 12, margin: "4px 0 0" }}>Timers will appear here when you start cooking.</p>
      </div>
    );
  }
  return (
    <div>
      {state.activeTimers.map((t) => <TimerCard key={t.id} timer={t} />)}
    </div>
  );
};
