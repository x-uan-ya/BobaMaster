/**
 * ActiveTimers — Right-column panel showing active brewing countdowns.
 * Uses a 1-second interval to update the displayed remaining time.
 */

import React, { useEffect, useState } from "react";
import { useDashboard } from "../store/dashboardStore";
import type { ActiveBrewTimer } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SHOP_ID = import.meta.env.VITE_SHOP_ID ?? "00000000-0000-0000-0000-000000000001";

function formatRemaining(timer: ActiveBrewTimer): {
  label: string;
  pct: number;
  done: boolean;
} {
  const elapsed = Date.now() - timer.started_at;
  const remaining = Math.max(0, timer.cook_time_ms - elapsed);
  const pct = Math.round((elapsed / timer.cook_time_ms) * 100);
  const done = remaining === 0;

  if (done) return { label: "Ready!", pct: 100, done: true };

  const totalSecs = Math.ceil(remaining / 1000);
  const mins = Math.floor(totalSecs / 60);
  const secs = totalSecs % 60;
  return {
    label: `${mins}:${secs.toString().padStart(2, "0")} remaining`,
    pct,
    done: false,
  };
}

const TimerCard: React.FC<{ timer: ActiveBrewTimer }> = ({ timer }) => {
  const { dispatch } = useDashboard();
  const [, setTick] = useState(0);
  const [hasCompleted, setHasCompleted] = useState(false);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const playCompletionChime = () => {
    try {
      const audioCtx = new AudioContext();
      const oscillator = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      oscillator.type = "triangle";
      oscillator.frequency.value = 880;
      gain.gain.value = 0.08;

      oscillator.connect(gain);
      gain.connect(audioCtx.destination);
      oscillator.start();
      oscillator.stop(audioCtx.currentTime + 0.22);
      oscillator.onended = () => {
        audioCtx.close();
      };
    } catch {
      // Browser may block autoplay if there has been no interaction,
      // but this is a best-effort notification chime.
    }
  };

  useEffect(() => {
    if (!timer.batch_id || hasCompleted) return;
    if (Date.now() - timer.started_at >= timer.cook_time_ms) {
      setHasCompleted(true);
      const completeBrew = async () => {
        try {
          await fetch(`${API_BASE_URL}/api/v1/inventory/brew/complete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              shop_id: SHOP_ID,
              batch_id: timer.batch_id,
              ingredient_id: timer.ingredient_id,
            }),
          });
          playCompletionChime();
        } catch (error) {
          console.error("Failed to complete brew batch", error);
        } finally {
          dispatch({ type: "REMOVE_BREW_TIMER", payload: timer.id });
        }
      };
      completeBrew();
    }
  }, [hasCompleted, timer, dispatch]);

  const { label, pct, done } = formatRemaining(timer);

  const barColor = done
    ? "bg-success"
    : pct > 75
    ? "bg-primary"
    : pct > 40
    ? "bg-warning"
    : "bg-primary-light";

  return (
    <div
      className={`
        m3-card-outlined p-3 space-y-2 animate-fade-in
        ${done ? "border-success" : ""}
      `}
      role="status"
      aria-label={`${timer.label} brew timer: ${label}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-on-surface truncate">
          🍳 {timer.label}
        </span>
        <button
          onClick={() => dispatch({ type: "REMOVE_BREW_TIMER", payload: timer.id })}
          className="text-xs text-on-surface-muted hover:text-error px-2 py-1
                     rounded-m3-sm transition-colors min-h-0 min-w-0"
          aria-label={`Remove ${timer.label} timer`}
        >
          ✕
        </button>
      </div>

      {/* Linear progress bar */}
      <div
        className="w-full h-2 rounded-full bg-surface-variant overflow-hidden"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={`h-full rounded-full transition-all duration-1000 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className={`text-xs font-medium ${done ? "text-success" : "text-on-surface-muted"}`}>
        {label}
      </p>
    </div>
  );
};

export const ActiveTimers: React.FC = () => {
  const { state } = useDashboard();
  const { activeTimers } = state;

  if (activeTimers.length === 0) {
    return (
      <div className="m3-card-outlined text-sm text-on-surface-muted text-center py-8">
        <p className="text-2xl mb-2">🫙</p>
        <p>No active brews.</p>
        <p className="text-xs mt-1">Start cooking to see timers here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {activeTimers.map((timer) => (
        <TimerCard key={timer.id} timer={timer} />
      ))}
    </div>
  );
};
