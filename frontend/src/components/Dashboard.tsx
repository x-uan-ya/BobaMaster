/**
 * Dashboard — Live Operations View (Milestone 8 - ENHANCED)
 *
 * Premium, modern layout showing:
 *  - Critical operations banner (red alert)
 *  - AI agent quick controls
 *  - Live ingredient status with color coding
 *  - Active cooking timers
 *  - Quick access cards for key actions
 */

import React from "react";
import { useDashboard } from "../store/dashboardStore";
import { CircularProgress } from "./CircularProgress";
import { AlertBanner } from "./AlertBanner";
import { ActiveTimers } from "./ActiveTimers";
import { AgentPanel } from "./AgentPanel";
import { Activity, Clock } from "lucide-react";
import type { InventoryIngredient } from "../types";
import type { NavPage } from "./NavigationRail";

// Maximum grams considered "full" for percentage calculation
const INGREDIENT_MAX_GRAMS: Record<string, number> = {
  tapioca_pearls:  4000,
  black_tea:       8000,
  jasmine_tea:     8000,
  oolong_tea:      8000,
  matcha_powder:   1000,
};

function getMaxGrams(ingredient_id: string): number {
  return INGREDIENT_MAX_GRAMS[ingredient_id] ?? 4000;
}

function formatGrams(grams: number): string {
  if (grams >= 1000) return `${(grams / 1000).toFixed(1)}kg`;
  return `${Math.round(grams)}g`;
}

function formatExpiry(iso: string | null): string {
  if (!iso) return "—";
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return "Expired";
  const mins = Math.floor(diff / 60_000);
  const hrs = Math.floor(mins / 60);
  const rem = mins % 60;
  if (hrs > 0) return `${hrs}h ${rem}m`;
  return `${mins}m`;
}

function formatIngredientLabel(id: string): string {
  return id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ── Enhanced Ingredient Status Card ────────────────────────────────────────

const IngredientCard: React.FC<{ ingredient: InventoryIngredient }> = ({
  ingredient,
}) => {
  const max = getMaxGrams(ingredient.ingredient_id);
  const pct = Math.round((ingredient.total_remaining_grams / max) * 100);
  const expiryLabel = formatExpiry(ingredient.nearest_expiry);

  // Status colors
  const statusColor = pct < 15 ? "#b52235" : pct < 40 ? "#d97706" : "#16a34a";
  const statusLabel = pct < 15 ? "Critical" : pct < 40 ? "Low" : "Healthy";
  const bgColor = pct < 15 ? "#fde8eb" : pct < 40 ? "#fff7ed" : "#f0fdf4";
  const borderColor = pct < 15 ? "#fca5a5" : pct < 40 ? "#fed7aa" : "#86efac";

  return (
    <div
      style={{
        backgroundColor: bgColor,
        border: `1.5px solid ${borderColor}`,
        borderRadius: 12,
        padding: 16,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        transition: "all 0.3s",
        cursor: "pointer",
        position: "relative",
        overflow: "hidden",
      }}
      className="hover:shadow-lg"
    >
      {/* Top bar indicator */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          backgroundColor: statusColor,
        }}
      />

      <CircularProgress
        value={pct}
        size={110}
        stroke={10}
        label={formatGrams(ingredient.total_remaining_grams)}
        sublabel={formatIngredientLabel(ingredient.ingredient_id)}
      />

      <div style={{ width: "100%", textAlign: "center" }}>
        {ingredient.active_brewing_qty_grams > 0 && (
          <p
            style={{
              fontSize: 11,
              color: "#0891b2",
              fontWeight: 600,
              margin: "0 0 4px",
            }}
          >
            <Clock size={12} style={{ display: "inline", marginRight: 4 }} />
            Brewing: {formatGrams(ingredient.active_brewing_qty_grams)}
          </p>
        )}
        <p
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: statusColor,
            margin: "0 0 4px",
          }}
        >
          {statusLabel}
        </p>
        <p style={{ fontSize: 10, color: "#6b7280", margin: 0 }}>
          Expires {expiryLabel}
        </p>
        <p style={{ fontSize: 9, color: "#9ca3af", margin: "4px 0 0" }}>
          {ingredient.active_batches.length} batch
          {ingredient.active_batches.length !== 1 ? "es" : ""}
        </p>
      </div>
    </div>
  );
};

// ── Quick Action Card ──────────────────────────────────────────────────────

const QuickActionCard: React.FC<{
  label: string;
  description: string;
  icon: string;
  color: string;
  onClick: () => void;
}> = ({ label, description, icon, color, onClick }) => (
  <button
    onClick={onClick}
    style={{
      backgroundColor: color,
      border: "none",
      borderRadius: 12,
      padding: 16,
      color: "#fff",
      cursor: "pointer",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 8,
      textAlign: "center",
      transition: "all 0.2s",
      transform: "scale(1)",
    }}
    onMouseEnter={(e) => {
      (e.currentTarget as HTMLButtonElement).style.transform = "scale(1.05)";
      (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 8px 16px rgba(0,0,0,0.2)";
    }}
    onMouseLeave={(e) => {
      (e.currentTarget as HTMLButtonElement).style.transform = "scale(1)";
      (e.currentTarget as HTMLButtonElement).style.boxShadow = "none";
    }}
  >
    <div style={{ fontSize: 24 }}>{icon}</div>
    <div>
      <p style={{ fontSize: 12, fontWeight: 700, margin: 0 }}>{label}</p>
      <p style={{ fontSize: 10, opacity: 0.9, margin: "2px 0 0" }}>{description}</p>
    </div>
  </button>
);

// ── Dashboard ──────────────────────────────────────────────────────────────

export const Dashboard: React.FC<{ onNavigate?: (page: NavPage) => void }> = ({ onNavigate }) => {
  const { state } = useDashboard();
  const { ingredients, alerts, connectionStatus } = state;

  const ingredientList = Object.values(ingredients);

  // Show a placeholder grid when no real data has arrived yet
  const PLACEHOLDER_IDS = [
    "tapioca_pearls",
    "black_tea",
    "jasmine_tea",
    "matcha_powder",
  ];

  const displayIngredients: InventoryIngredient[] =
    ingredientList.length > 0
      ? ingredientList
      : PLACEHOLDER_IDS.map((id) => ({
          ingredient_id: id,
          total_remaining_grams: 0,
          active_brewing_qty_grams: 0,
          nearest_expiry: null,
          active_batches: [],
        }));

  // Top-priority alert (first BREW_NOW, then WARN, then whatever is first)
  const topAlert =
    alerts.find((a) => a.action === "BREW_NOW") ??
    alerts.find((a) => a.action === "WARN") ??
    alerts[0] ??
    null;

  return (
    <main
      style={{
        flex: 1,
        overflowY: "auto",
        padding: 20,
        backgroundColor: "#f4f6f8",
      }}
      aria-label="Operations Dashboard"
    >
      <div style={{ maxWidth: "1400px", margin: "0 auto", display: "flex", flexDirection: "column", gap: 20 }}>
        {/* Header with greeting */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: "#111827", margin: 0 }}>
              Operations Center
            </h1>
            <p style={{ fontSize: 13, color: "#9ca3af", margin: "4px 0 0" }}>
              Real-time monitoring and AI-powered recommendations
            </p>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              backgroundColor: connectionStatus === "online" ? "#dcfce7" : "#fde8eb",
              color: connectionStatus === "online" ? "#16a34a" : "#b52235",
              borderRadius: 8,
              padding: "6px 12px",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            <span style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "currentColor" }} />
            {connectionStatus === "online" ? "Connected" : "Offline"}
          </div>
        </div>

        {/* Alert Banner */}
        <AlertBanner alert={topAlert} />

        {/* AI Controls */}
        <AgentPanel onNavigate={onNavigate} />

        {/* Quick Actions */}
        <section style={{ marginTop: 8 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: "#6b7280", margin: "0 0 12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Quick Actions
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
            <QuickActionCard
              label="Log Sale"
              description="Record customer order"
              icon="🛒"
              color="#ea580c"
              onClick={() => onNavigate?.("inventory")}
            />
            <QuickActionCard
              label="Cook Batch"
              description="Start brewing"
              icon="🔥"
              color="#16a34a"
              onClick={() => onNavigate?.("inventory")}
            />
            <QuickActionCard
              label="View Forecast"
              description="Demand prediction"
              icon="📈"
              color="#0891b2"
              onClick={() => onNavigate?.("forecast")}
            />
            <QuickActionCard
              label="Insights"
              description="Business analytics"
              icon="📊"
              color="#7c3aed"
              onClick={() => onNavigate?.("insights")}
            />
          </div>
        </section>

        {/* Main grid: Ingredients + Timers */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          {/* Ingredients */}
          <section>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: "#6b7280", margin: "0 0 12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Ingredient Status
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {displayIngredients.map((ing) => (
                <IngredientCard key={ing.ingredient_id} ingredient={ing} />
              ))}
            </div>
          </section>

          {/* Timers */}
          <section>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: "#6b7280", margin: "0 0 12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Active Timers
            </h2>
            <ActiveTimers />
          </section>
        </div>

        {/* Offline notice */}
        {connectionStatus === "offline" && (
          <div
            style={{
              backgroundColor: "#fde8eb",
              border: "1.5px solid #fca5a5",
              borderRadius: 12,
              padding: "12px 16px",
              color: "#b52235",
              fontSize: 12,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
            role="alert"
          >
            <Activity size={16} />
            Backend connection lost. Data may be stale. Reconnecting…
          </div>
        )}
      </div>
    </main>
  );
};
