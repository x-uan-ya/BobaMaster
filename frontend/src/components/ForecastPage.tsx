/**
 * ForecastPage — Demand Forecasting Engine (PredictorAgent + ContextAgent)
 *
 * Shows live 30 / 60 / 120-minute demand projections for each ingredient.
 * Staff can adjust the velocity inputs (how fast stock is selling right now)
 * and see how context factors (school session, weather, rain) shift the forecast.
 */

import React, { useState } from "react";
import { RefreshCw, TrendingUp, Info } from "lucide-react";

const API  = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SHOP = import.meta.env.VITE_SHOP_ID  ?? "00000000-0000-0000-0000-000000000001";

const INGREDIENTS = [
  { id: "tapioca_pearls", cold: true,  hot: false },
  { id: "black_tea",      cold: false, hot: true  },
  { id: "jasmine_tea",    cold: false, hot: true  },
  { id: "oolong_tea",     cold: false, hot: true  },
  { id: "matcha_powder",  cold: true,  hot: false },
];

const fmtId = (id: string) => id.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
const fmtG  = (g: number)  => g >= 1000 ? `${(g / 1000).toFixed(1)} kg` : `${Math.round(g)} g`;

interface ForecastResult {
  ingredient_id: string;
  t30_grams: number;
  t60_grams: number;
  t120_grams: number;
  school_multiplier: number;
  temp_multiplier: number;
  rain_multiplier: number;
}

interface ContextResult {
  weather: { temp_c: number; rain_prob: number; sky_condition: string; humidity_pct: number };
  calendar: { is_school_day: boolean; is_public_holiday: boolean; hour_of_day: number };
  local_events: { has_nearby_event: boolean; event_type: string | null; crowd_score: number };
}

// ── Forecast bar ───────────────────────────────────────────────────────────

const ForecastBar: React.FC<{ label: string; grams: number; maxGrams: number; color: string }> = ({
  label, grams, maxGrams, color,
}) => {
  const pct = Math.min(100, Math.round((grams / maxGrams) * 100));
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
        <span style={{ fontWeight: 600, color: "#374151" }}>{label}</span>
        <span style={{ fontWeight: 800, color }}>{fmtG(grams)}</span>
      </div>
      <div style={{ backgroundColor: "#f3f4f6", borderRadius: 99, height: 8 }}>
        <div style={{
          width: `${pct}%`, height: "100%", borderRadius: 99,
          backgroundColor: color, transition: "width 0.5s ease",
        }} />
      </div>
    </div>
  );
};

// ── Multiplier badge ───────────────────────────────────────────────────────

const MultBadge: React.FC<{ label: string; value: number }> = ({ label, value }) => {
  if (value <= 1) return null;
  const pct = Math.round((value - 1) * 100);
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 3,
      backgroundColor: "#fef3c7", color: "#b45309",
      borderRadius: 6, padding: "2px 7px", fontSize: 11, fontWeight: 700, marginRight: 4,
    }}>
      {label} +{pct}%
    </span>
  );
};

// ── Ingredient forecast card ───────────────────────────────────────────────

const IngredientForecastCard: React.FC<{
  ingredientId: string;
  isCold: boolean;
  isHot: boolean;
  rate10m: number;
  rate30m: number;
  rate60m: number;
}> = ({ ingredientId, isCold, isHot, rate10m, rate30m, rate60m }) => {
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch_forecast = async () => {
    setLoading(true); setError(null);
    try {
      const params = new URLSearchParams({
        grams_per_min_10m: String(rate10m),
        grams_per_min_30m: String(rate30m),
        grams_per_min_60m: String(rate60m),
        is_cold_drink_ingredient: String(isCold),
        is_hot_drink_ingredient: String(isHot),
      });
      const res = await fetch(`${API}/api/v1/forecast/${SHOP}/${ingredientId}?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult({ ...data, ingredient_id: ingredientId });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally { setLoading(false); }
  };

  const maxG = result ? Math.max(result.t120_grams, 1) : 1;

  return (
    <div style={{
      backgroundColor: "#fff", borderRadius: 14,
      boxShadow: "0 2px 8px rgba(0,0,0,0.07)", padding: 18,
      border: "1px solid #f0f0f0",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: 0 }}>
          {fmtId(ingredientId)}
        </h3>
        <button onClick={fetch_forecast} disabled={loading} style={{
          display: "flex", alignItems: "center", gap: 5,
          backgroundColor: "#1a6b5e", color: "#fff", border: "none",
          borderRadius: 8, padding: "7px 13px", fontWeight: 700, fontSize: 12,
          cursor: loading ? "not-allowed" : "pointer",
        }}>
          <TrendingUp size={13} />
          {loading ? "Fetching…" : "Get Forecast"}
        </button>
      </div>

      {error && (
        <div style={{ backgroundColor: "#fde8eb", color: "#b52235", borderRadius: 8,
          padding: "8px 12px", fontSize: 12, marginBottom: 10 }}>
          {error} — is backend running?
        </div>
      )}

      {result && (
        <>
          {/* Multiplier badges */}
          <div style={{ marginBottom: 12 }}>
            <MultBadge label="School" value={result.school_multiplier} />
            <MultBadge label="Heat"   value={result.temp_multiplier} />
            <MultBadge label="Rain"   value={result.rain_multiplier} />
            {result.school_multiplier <= 1 && result.temp_multiplier <= 1 && result.rain_multiplier <= 1 && (
              <span style={{ fontSize: 11, color: "#9ca3af" }}>No context boosts active</span>
            )}
          </div>

          <ForecastBar label="Next 30 min"  grams={result.t30_grams}  maxGrams={maxG} color="#0891b2" />
          <ForecastBar label="Next 60 min"  grams={result.t60_grams}  maxGrams={maxG} color="#1a6b5e" />
          <ForecastBar label="Next 120 min" grams={result.t120_grams} maxGrams={maxG} color="#7c3aed" />

          <p style={{ fontSize: 11, color: "#9ca3af", marginTop: 8 }}>
            Based on {fmtG(rate60m * 60)} sold / hr average
          </p>
        </>
      )}

      {!result && !loading && !error && (
        <div style={{ textAlign: "center", padding: "20px 0", color: "#9ca3af", fontSize: 13 }}>
          Click "Get Forecast" to generate demand projections
        </div>
      )}
    </div>
  );
};

// ── Context panel ──────────────────────────────────────────────────────────

const ContextPanel: React.FC = () => {
  const [ctx, setCtx] = useState<ContextResult | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchCtx = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/context/${SHOP}`);
      if (res.ok) setCtx(await res.json());
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  return (
    <div style={{
      backgroundColor: "#fff", borderRadius: 14,
      boxShadow: "0 2px 8px rgba(0,0,0,0.07)", padding: 18,
      border: "1px solid #f0f0f0",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: 0 }}>
          Context Factors
        </h3>
        <button onClick={fetchCtx} disabled={loading} style={{
          display: "flex", alignItems: "center", gap: 5,
          backgroundColor: "#7c3aed", color: "#fff", border: "none",
          borderRadius: 8, padding: "7px 13px", fontWeight: 700, fontSize: 12,
          cursor: "pointer",
        }}>
          <RefreshCw size={13} />
          {loading ? "Loading…" : "Fetch Context"}
        </button>
      </div>

      {!ctx && !loading && (
        <p style={{ fontSize: 12, color: "#9ca3af", textAlign: "center", padding: "16px 0" }}>
          Click "Fetch Context" to load weather and calendar data
        </p>
      )}

      {ctx && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {[
            { label: "Temperature",    value: `${ctx.weather.temp_c}°C` },
            { label: "Rain Prob",      value: `${Math.round(ctx.weather.rain_prob * 100)}%` },
            { label: "Sky",            value: ctx.weather.sky_condition },
            { label: "Humidity",       value: `${ctx.weather.humidity_pct}%` },
            { label: "School Day",     value: ctx.calendar.is_school_day ? "Yes" : "No" },
            { label: "Public Holiday", value: ctx.calendar.is_public_holiday ? "Yes" : "No" },
            { label: "Hour of Day",    value: `${ctx.calendar.hour_of_day}:00` },
            { label: "Nearby Event",   value: ctx.local_events.has_nearby_event ? (ctx.local_events.event_type ?? "Yes") : "None" },
            { label: "Crowd Score",    value: `${Math.round(ctx.local_events.crowd_score * 100)}%` },
          ].map(({ label, value }) => (
            <div key={label} style={{
              display: "flex", justifyContent: "space-between",
              padding: "6px 10px", backgroundColor: "#f9fafb", borderRadius: 7,
              fontSize: 12,
            }}>
              <span style={{ color: "#6b7280" }}>{label}</span>
              <span style={{ fontWeight: 700, color: "#111827" }}>{value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Main page ──────────────────────────────────────────────────────────────

export const ForecastPage: React.FC = () => {
  // Shared velocity controls — user adjusts these to reflect current sales pace
  const [rate10m, setRate10m] = useState(8);
  const [rate30m, setRate30m] = useState(7);
  const [rate60m, setRate60m] = useState(6);

  return (
    <main style={{ flex: 1, overflowY: "auto", padding: 20, backgroundColor: "#f4f6f8" }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: "#111827", margin: 0 }}>
          Demand Forecast
        </h1>
        <p style={{ fontSize: 13, color: "#9ca3af", margin: "4px 0 0" }}>
          PredictorAgent × ContextAgent — 30 / 60 / 120-minute projections
        </p>
      </div>

      {/* Velocity controls */}
      <div style={{
        backgroundColor: "#fff", borderRadius: 14, padding: 16, marginBottom: 20,
        boxShadow: "0 2px 8px rgba(0,0,0,0.07)", border: "1px solid #f0f0f0",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <Info size={15} color="#6b7280" />
          <span style={{ fontSize: 13, fontWeight: 700, color: "#374151" }}>
            Sales Velocity (g/min) — adjust to match current pace
          </span>
        </div>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {[
            { label: "Last 10 min", value: rate10m, set: setRate10m },
            { label: "Last 30 min", value: rate30m, set: setRate30m },
            { label: "Last 60 min", value: rate60m, set: setRate60m },
          ].map(({ label, value, set }) => (
            <div key={label} style={{ flex: 1, minWidth: 120 }}>
              <label style={{ fontSize: 11, color: "#6b7280", fontWeight: 600, display: "block", marginBottom: 4 }}>
                {label}
              </label>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <input
                  type="number" min="0" step="1" value={value}
                  onChange={e => set(Number(e.target.value))}
                  style={{
                    width: 70, padding: "6px 8px", borderRadius: 7,
                    border: "1.5px solid #d1d5db", fontSize: 13, fontWeight: 700,
                    outline: "none", color: "#111827",
                  }}
                />
                <span style={{ fontSize: 12, color: "#9ca3af" }}>g/min</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Two-column layout: forecasts + context */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 16, alignItems: "start" }}>
        {/* Left — ingredient forecasts */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
          {INGREDIENTS.map(({ id, cold, hot }) => (
            <IngredientForecastCard
              key={id}
              ingredientId={id}
              isCold={cold}
              isHot={hot}
              rate10m={rate10m}
              rate30m={rate30m}
              rate60m={rate60m}
            />
          ))}
        </div>

        {/* Right — context factors */}
        <ContextPanel />
      </div>
    </main>
  );
};
