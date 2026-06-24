import React from "react";
import { AlertTriangle, Clock, ChefHat } from "lucide-react";
import { useDashboard } from "../store/dashboardStore";
import type { RecommendationAlert } from "../types";

interface Props { alert: RecommendationAlert | null; }

const COOK_TIMES: Record<string, number> = {
  tapioca_pearls: 50, black_tea: 15, jasmine_tea: 15, oolong_tea: 15, matcha_powder: 10,
};

function shortageLabel(iso: string | null): string {
  if (!iso) return "";
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return "now";
  return `in ~${Math.ceil(diff / 60_000)} min`;
}

export const AlertBanner: React.FC<Props> = ({ alert }) => {
  const { dispatch } = useDashboard();

  if (!alert) {
    return (
      <div style={{
        backgroundColor: "#dcfce7", border: "2px solid #16a34a",
        borderRadius: 14, padding: "14px 18px",
        display: "flex", alignItems: "center", gap: 12,
      }}>
        <span style={{ fontSize: 22 }}>✅</span>
        <div>
          <p style={{ fontWeight: 700, color: "#16a34a", margin: 0 }}>All Clear</p>
          <p style={{ fontSize: 13, color: "#4b5563", margin: 0 }}>
            Inventory levels are within safe operating limits.
          </p>
        </div>
      </div>
    );
  }

  const isCritical = alert.action === "BREW_NOW";
  const borderColor = isCritical ? "#b52235" : "#d97706";
  const bgColor     = isCritical ? "#fff5f5" : "#fffbeb";
  const badgeBg     = isCritical ? "#b52235" : "#d97706";

  const dismiss = () => {
    const id = alert.recommendation_id ?? alert.dispatched_at;
    dispatch({ type: "DISMISS_ALERT", payload: id });
  };

  const handleStartCooking = () => {
    dismiss();
    dispatch({
      type: "START_BREW_TIMER",
      payload: {
        id: crypto.randomUUID(),
        ingredient_id: alert.ingredient_id,
        label: alert.ingredient_id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        started_at: Date.now(),
        cook_time_ms: (COOK_TIMES[alert.ingredient_id] ?? 30) * 60 * 1000,
      },
    });
  };

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={isCritical ? "animate-alert-flash" : ""}
      style={{
        backgroundColor: bgColor,
        border: `2px solid ${borderColor}`,
        borderRadius: 14,
        padding: "16px 20px",
        display: "flex",
        alignItems: "flex-start",
        gap: 16,
        animation: isCritical ? "alert-flash 1.4s ease-in-out infinite" : undefined,
      }}
    >
      {/* Icon */}
      <div style={{
        width: 44, height: 44, borderRadius: 10, flexShrink: 0,
        backgroundColor: badgeBg + "22",
        display: "flex", alignItems: "center", justifyContent: "center",
        color: borderColor,
      }}>
        <AlertTriangle size={22} />
      </div>

      {/* Text */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
          <span style={{
            backgroundColor: badgeBg, color: "#fff",
            borderRadius: 6, padding: "2px 8px",
            fontSize: 11, fontWeight: 700, textTransform: "uppercase",
          }}>
            {isCritical ? "Critical" : "Warning"}
          </span>
          <span style={{ fontSize: 15, fontWeight: 700, color: "#1f2937" }}>
            {alert.action_string}
          </span>
        </div>

        <p style={{ fontSize: 13, color: "#374151", margin: "0 0 8px 0", lineHeight: 1.5 }}>
          {alert.explanation_text}
        </p>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 14, fontSize: 12, color: "#6b7280" }}>
          {alert.predicted_shortage_at && (
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <Clock size={12} /> Stockout {shortageLabel(alert.predicted_shortage_at)}
            </span>
          )}
          <span>Stock: {Math.round(alert.current_stock_grams)}g</span>
          <span>Demand: {Math.round(alert.predicted_consumption_grams)}g</span>
          {!alert.llm_used && <span style={{ fontStyle: "italic", opacity: 0.6 }}>(fallback)</span>}
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>
        <button
          onClick={handleStartCooking}
          style={{
            display: "flex", alignItems: "center", gap: 6,
            backgroundColor: "#b52235", color: "#fff",
            border: "none", borderRadius: 10, cursor: "pointer",
            padding: "10px 16px", fontWeight: 700, fontSize: 13,
            minHeight: 44, whiteSpace: "nowrap",
          }}
        >
          <ChefHat size={16} /> Start Cooking
        </button>
        <button
          onClick={dismiss}
          style={{
            backgroundColor: "transparent", color: "#6b7280",
            border: "none", borderRadius: 10, cursor: "pointer",
            padding: "8px 16px", fontWeight: 500, fontSize: 13, minHeight: 40,
          }}
        >
          Snooze 5m
        </button>
      </div>
    </div>
  );
};
