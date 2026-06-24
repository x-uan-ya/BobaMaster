/**
 * Dashboard — Live Operations View (Milestone 8 primary deliverable).
 *
 * Layout (12-col grid):
 *  ┌─────────────────────────── 12 cols ────────────────────────────────┐
 *  │  Critical Operations Banner (full width)                           │
 *  ├─────────────────────── 8 cols ─────┬──────── 4 cols ──────────────┤
 *  │  Live Ingredient State Cards       │  Active Cooking Timers        │
 *  └────────────────────────────────────┴─────────────────────────────-┘
 */

import React from "react";
import { useDashboard } from "../store/dashboardStore";
import { CircularProgress } from "./CircularProgress";
import { AlertBanner } from "./AlertBanner";
import { ActiveTimers } from "./ActiveTimers";
import type { InventoryIngredient } from "../types";

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

// ── Ingredient State Card ──────────────────────────────────────────────────

const IngredientCard: React.FC<{ ingredient: InventoryIngredient }> = ({
  ingredient,
}) => {
  const max = getMaxGrams(ingredient.ingredient_id);
  const pct = Math.round((ingredient.total_remaining_grams / max) * 100);
  const expiryLabel = formatExpiry(ingredient.nearest_expiry);

  const expiryColor =
    ingredient.nearest_expiry &&
    new Date(ingredient.nearest_expiry).getTime() - Date.now() < 30 * 60_000
      ? "text-error"
      : "text-on-surface-muted";

  return (
    <div className="m3-card flex flex-col items-center gap-3 animate-fade-in">
      <CircularProgress
        value={pct}
        size={110}
        stroke={10}
        label={formatGrams(ingredient.total_remaining_grams)}
        sublabel={formatIngredientLabel(ingredient.ingredient_id)}
      />

      <div className="w-full text-center space-y-0.5">
        {ingredient.active_brewing_qty_grams > 0 && (
          <p className="text-xs text-primary font-medium">
            🍳 {formatGrams(ingredient.active_brewing_qty_grams)} brewing
          </p>
        )}
        <p className={`text-xs font-medium ${expiryColor}`}>
          ⏳ Expires: {expiryLabel}
        </p>
        <p className="text-xs text-on-surface-muted">
          {ingredient.active_batches.length} active batch
          {ingredient.active_batches.length !== 1 ? "es" : ""}
        </p>
      </div>
    </div>
  );
};

// ── Dashboard ──────────────────────────────────────────────────────────────

export const Dashboard: React.FC = () => {
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
    <main className="flex-1 overflow-auto p-4 space-y-4" aria-label="Operations Dashboard">
      {/* ── 1. Critical Operations Banner ─────────────────────────── */}
      <AlertBanner alert={topAlert} />

      {/* ── 2. Ingredient grid + Timers ───────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* Left — 8 cols: Live ingredient state cards */}
        <section
          className="lg:col-span-8"
          aria-label="Live Ingredient Status"
        >
          <h2 className="text-sm font-semibold text-on-surface-muted uppercase tracking-wide mb-3">
            Ingredient Status
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {displayIngredients.map((ing) => (
              <IngredientCard key={ing.ingredient_id} ingredient={ing} />
            ))}
          </div>
        </section>

        {/* Right — 4 cols: Active Cooking Timers */}
        <section
          className="lg:col-span-4"
          aria-label="Active Cooking Timers"
        >
          <h2 className="text-sm font-semibold text-on-surface-muted uppercase tracking-wide mb-3">
            Active Timers
          </h2>
          <ActiveTimers />
        </section>
      </div>

      {/* ── 3. Connection offline notice ──────────────────────────── */}
      {connectionStatus === "offline" && (
        <div
          className="m3-card border border-error text-error text-sm flex items-center gap-2"
          role="alert"
        >
          <span className="font-bold">⚠</span>
          <span>
            Backend connection lost. Data may be stale. Reconnecting…
          </span>
        </div>
      )}
    </main>
  );
};
