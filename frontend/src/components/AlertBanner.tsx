/**
 * AlertBanner — Critical Operations Banner (top of dashboard).
 *
 * Milestone 8: Renders the current highest-priority alert with flashing
 * border animation and Start Cooking / Snooze actions.
 * Milestone 9 will add audio chime and full interaction cycle.
 */

import React, { useEffect, useRef, useState } from "react";
import { AlertTriangle, Clock, ChefHat } from "lucide-react";
import { useDashboard } from "../store/dashboardStore";
import type { RecommendationAlert } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface AlertBannerProps {
  alert: RecommendationAlert | null;
}

function formatShortageTime(iso: string | null): string {
  if (!iso) return "";
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return "now";
  const mins = Math.ceil(diff / 60_000);
  return `in ~${mins} min`;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ alert }) => {
  const { dispatch } = useDashboard();
  const [isStarting, setIsStarting] = useState(false);

  const snoozeTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (snoozeTimerRef.current !== null) {
        window.clearTimeout(snoozeTimerRef.current);
      }
    };
  }, []);

  const handleStartCooking = async () => {
    if (!alert) return;
    setIsStarting(true);

    const cookTimeMap: Record<string, number> = {
      tapioca_pearls: 50,
      black_tea: 15,
      jasmine_tea: 15,
      oolong_tea: 15,
      matcha_powder: 10,
    };

    const batchSizes: Record<string, number> = {
      tapioca_pearls: 1600,
      black_tea: 1800,
      jasmine_tea: 1800,
      oolong_tea: 1800,
      matcha_powder: 1200,
    };

    const initialQty = batchSizes[alert.ingredient_id] ?? 1200;
    const cookMins = cookTimeMap[alert.ingredient_id] ?? 30;
    const alertId = alert.recommendation_id ?? alert.dispatched_at;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/inventory/brew/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          shop_id: alert.shop_id,
          ingredient_id: alert.ingredient_id,
          initial_qty_grams: initialQty,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start brew: ${response.statusText}`);
      }

      const data = await response.json();
      dispatch({ type: "DISMISS_ALERT", payload: alertId });
      dispatch({
        type: "START_BREW_TIMER",
        payload: {
          id: crypto.randomUUID(),
          batch_id: data.batch_id,
          ingredient_id: alert.ingredient_id,
          label: alert.ingredient_id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
          started_at: Date.now(),
          cook_time_ms: cookMins * 60 * 1000,
        },
      });
    } catch (error) {
      console.error(error);
    } finally {
      setIsStarting(false);
    }
  };

  const handleSnooze = () => {
    if (!alert) return;
    const alertId = alert.recommendation_id ?? alert.dispatched_at;
    dispatch({ type: "DISMISS_ALERT", payload: alertId });
    snoozeTimerRef.current = window.setTimeout(() => {
      dispatch({ type: "PUSH_ALERT", payload: alert });
    }, 5 * 60_000);
  };

  // No active alert → show a calm "all-clear" card
  if (!alert) {
    return (
      <div className="m3-card border border-success text-sm text-success flex items-center gap-3">
        <span className="text-xl">✅</span>
        <div>
          <p className="font-semibold">All Clear</p>
          <p className="text-on-surface-muted text-xs">
            No active alerts. Inventory levels are within safe operating limits.
          </p>
        </div>
      </div>
    );
  }

  const isCritical = alert.action === "BREW_NOW";

  return (
    <div
      className={`
        m3-card border-2 
        ${isCritical
          ? "border-error animate-alert-pulse"
          : "border-warning"
        }
      `}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        {/* Icon */}
        <div
          className={`
            shrink-0 w-12 h-12 rounded-m3-lg flex items-center justify-center
            ${isCritical ? "bg-error-light text-error" : "bg-warning-light text-warning"}
          `}
          aria-hidden="true"
        >
          <AlertTriangle size={24} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span
              className={`
                status-chip font-bold text-xs
                ${isCritical ? "bg-error text-error-on" : "bg-warning text-warning-on"}
              `}
            >
              {isCritical ? "CRITICAL" : "WARNING"}
            </span>
            <span className="font-semibold text-on-surface text-sm sm:text-base truncate">
              {alert.action_string}
            </span>
          </div>

          <p className="text-sm text-on-surface mb-2 leading-relaxed">
            {alert.explanation_text}
          </p>

          <div className="flex flex-wrap items-center gap-4 text-xs text-on-surface-muted">
            {alert.predicted_shortage_at && (
              <span className="flex items-center gap-1">
                <Clock size={12} />
                Stockout expected {formatShortageTime(alert.predicted_shortage_at)}
              </span>
            )}
            <span className="flex items-center gap-1">
              Stock: {Math.round(alert.current_stock_grams)}g
            </span>
            <span className="flex items-center gap-1">
              Demand: {Math.round(alert.predicted_consumption_grams)}g
            </span>
            {!alert.llm_used && (
              <span className="italic opacity-60">(fallback explanation)</span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2 shrink-0">
          <button
            onClick={handleStartCooking}
            disabled={isStarting}
            className="btn-error flex items-center gap-2"
            aria-label={`Start cooking ${alert.ingredient_id}`}
          >
            <ChefHat size={18} />
            {isStarting ? "Starting…" : "Start Cooking"}
          </button>
          <button
            onClick={handleSnooze}
            className="btn-text text-on-surface-muted"
            aria-label="Snooze alert for 5 minutes"
          >
            Snooze 5m
          </button>
        </div>
      </div>
    </div>
  );
};
