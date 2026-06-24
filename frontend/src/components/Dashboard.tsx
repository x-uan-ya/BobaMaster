import React from "react";
import { useDashboard } from "../store/dashboardStore";
import { CircularProgress } from "./CircularProgress";
import { AlertBanner } from "./AlertBanner";
import { ActiveTimers } from "./ActiveTimers";
import type { InventoryIngredient } from "../types";

const MAX_GRAMS: Record<string, number> = {
  tapioca_pearls: 4000,
  black_tea:      8000,
  jasmine_tea:    8000,
  oolong_tea:     8000,
  matcha_powder:  1000,
};

function fmt(grams: number) {
  return grams >= 1000 ? `${(grams / 1000).toFixed(1)}kg` : `${Math.round(grams)}g`;
}

function fmtExpiry(iso: string | null): { text: string; urgent: boolean } {
  if (!iso) return { text: "—", urgent: false };
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return { text: "Expired", urgent: true };
  const mins = Math.floor(diff / 60_000);
  const hrs = Math.floor(mins / 60);
  const rem = mins % 60;
  const urgent = mins < 30;
  return { text: hrs > 0 ? `${hrs}h ${rem}m` : `${mins}m`, urgent };
}

function fmtLabel(id: string) {
  return id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ── Ingredient Card ────────────────────────────────────────────────────────

const IngredientCard: React.FC<{ ingredient: InventoryIngredient }> = ({ ingredient }) => {
  const max  = MAX_GRAMS[ingredient.ingredient_id] ?? 4000;
  const pct  = Math.round((ingredient.total_remaining_grams / max) * 100);
  const { text: expiryText, urgent: expiryUrgent } = fmtExpiry(ingredient.nearest_expiry);
  const isCritical = pct < 10;
  const isLow      = pct < 30;

  const statusBg    = isCritical ? "#fde8eb" : isLow ? "#fef3c7" : "#dcfce7";
  const statusColor = isCritical ? "#b52235" : isLow ? "#d97706" : "#16a34a";
  const statusText  = isCritical ? "🔴 Low Stock" : isLow ? "🟠 Warning" : "🟢 Healthy";

  return (
    <div
      className="animate-fade-in"
      style={{
        backgroundColor: "#ffffff",
        borderRadius: 14,
        boxShadow: "0 2px 8px rgba(0,0,0,0.09)",
        padding: "18px 14px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 10,
        border: expiryUrgent ? "2px solid #d97706" : "2px solid transparent",
      }}
    >
      <h3 style={{ fontSize: 12, fontWeight: 700, color: "#374151", margin: 0, textAlign: "center" }}>
        {fmtLabel(ingredient.ingredient_id)}
      </h3>

      <CircularProgress
        value={pct}
        size={110}
        stroke={11}
        label={fmt(ingredient.total_remaining_grams)}
        sublabel={`${pct}%`}
      />

      <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 5 }}>
        {/* Status badge */}
        <div style={{
          backgroundColor: statusBg, color: statusColor,
          borderRadius: 8, padding: "4px 8px",
          fontSize: 11, fontWeight: 700, textAlign: "center",
        }}>
          {statusText}
        </div>

        {/* Brewing */}
        {ingredient.active_brewing_qty_grams > 0 && (
          <div style={{
            backgroundColor: "#d0f0eb", color: "#1a6b5e",
            borderRadius: 8, padding: "4px 8px",
            fontSize: 11, fontWeight: 600, textAlign: "center",
          }}>
            🍳 {fmt(ingredient.active_brewing_qty_grams)} brewing
          </div>
        )}

        {/* Expiry */}
        <div style={{
          backgroundColor: expiryUrgent ? "#fde8eb" : "#f3f4f6",
          color: expiryUrgent ? "#b52235" : "#6b7280",
          borderRadius: 8, padding: "4px 8px",
          fontSize: 11, fontWeight: 600, textAlign: "center",
        }}>
          ⏳ {expiryText}
        </div>

        <p style={{ fontSize: 11, color: "#9ca3af", textAlign: "center", margin: 0 }}>
          {ingredient.active_batches.length} batch{ingredient.active_batches.length !== 1 ? "es" : ""}
        </p>
      </div>
    </div>
  );
};

// ── Dashboard ──────────────────────────────────────────────────────────────

const PLACEHOLDER_IDS = ["tapioca_pearls", "black_tea", "jasmine_tea", "matcha_powder"];

export const Dashboard: React.FC = () => {
  const { state } = useDashboard();
  const { ingredients, alerts, connectionStatus } = state;

  const ingredientList = Object.values(ingredients);
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

  const topAlert =
    alerts.find((a) => a.action === "BREW_NOW") ??
    alerts.find((a) => a.action === "WARN") ??
    alerts[0] ?? null;

  return (
    <main
      aria-label="Operations Dashboard"
      style={{
        flex: 1,
        overflowY: "auto",
        padding: 20,
        display: "flex",
        flexDirection: "column",
        gap: 20,
        backgroundColor: "#f4f6f8",
        minHeight: 0,
      }}
    >
      {/* 1. Alert banner — full width */}
      <AlertBanner alert={topAlert} />

      {/* 2. Two-column: ingredient grid (left) + timers (right) */}
      <div style={{ display: "flex", flexDirection: "row", gap: 20, flex: 1, minHeight: 0 }}>

        {/* Left — ingredient cards */}
        <section style={{ flex: "0 0 calc(66% - 10px)", minWidth: 0 }} aria-label="Ingredient Status">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700, color: "#1f2937", margin: 0 }}>📦 Ingredient Inventory</h2>
            <span style={{ fontSize: 12, color: "#9ca3af" }}>Live Status</span>
          </div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
            gap: 14,
          }}>
            {displayIngredients.map((ing) => (
              <IngredientCard key={ing.ingredient_id} ingredient={ing} />
            ))}
          </div>
        </section>

        {/* Right — timers */}
        <section style={{ flex: "0 0 calc(34% - 10px)", minWidth: 200 }} aria-label="Active Cooking Timers">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <h2 style={{ fontSize: 15, fontWeight: 700, color: "#1f2937", margin: 0 }}>⏱️ Active Timers</h2>
            <span style={{ fontSize: 12, color: "#9ca3af" }}>Real-time</span>
          </div>
          <div style={{ backgroundColor: "#ffffff", borderRadius: 14, boxShadow: "0 2px 8px rgba(0,0,0,0.08)", padding: 16 }}>
            <ActiveTimers />
          </div>
        </section>
      </div>

      {/* 3. Offline notice */}
      {connectionStatus === "offline" && (
        <div
          role="alert"
          style={{
            backgroundColor: "#fde8eb", border: "2px solid #b52235",
            borderRadius: 12, padding: "14px 18px",
            display: "flex", alignItems: "center", gap: 12,
          }}
        >
          <span style={{ fontSize: 24 }}>⚠️</span>
          <div>
            <p style={{ fontWeight: 700, color: "#b52235", margin: 0 }}>Connection Lost</p>
            <p style={{ fontSize: 13, color: "#6b7280", margin: 0 }}>Attempting to reconnect to backend…</p>
          </div>
        </div>
      )}
    </main>
  );
};
