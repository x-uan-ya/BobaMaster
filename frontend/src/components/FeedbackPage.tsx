/**
 * FeedbackPage — Closed-Loop Daily Audit (FeedbackAgent, Milestone 10).
 *
 * Runs the FeedbackAgent for a selected date and displays:
 *  - Forecast accuracy (MAPE)
 *  - Waste ratio and total waste
 *  - Staff compliance (acceptance vs ignored rate)
 *  - Safety buffer adjustments applied
 */

import React, { useState } from "react";
import { RefreshCw } from "lucide-react";

const API  = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SHOP = import.meta.env.VITE_SHOP_ID  ?? "00000000-0000-0000-0000-000000000001";

const fmtG  = (g: number)   => g >= 1000 ? `${(g / 1000).toFixed(1)} kg` : `${Math.round(g)} g`;
const fmtPct = (v: number)  => `${Math.round(v * 100)}%`;

interface Report {
  shop_id: string;
  date: string;
  total_transactions: number;
  total_waste_grams: number;
  total_prepared_grams: number;
  mape: number;
  acceptance_rate: number;
  ignored_rate: number;
  delayed_rate: number;
  pearl_waste_ratio: number;
  stockout_minutes: number;
  pearl_safety_factor_before: number;
  pearl_safety_factor_after: number;
  updated: boolean;
  generated_at: string;
  demo_mode: boolean;
}

// ── Metric tile ────────────────────────────────────────────────────────────

const Tile: React.FC<{
  label: string;
  value: string;
  sub?: string;
  color?: string;
}> = ({ label, value, sub, color = "#111827" }) => (
  <div style={{
    backgroundColor: "#fff", borderRadius: 12, padding: "14px 16px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
  }}>
    <p style={{ fontSize: 11, color: "#9ca3af", fontWeight: 600, margin: "0 0 4px", textTransform: "uppercase" }}>
      {label}
    </p>
    <p style={{ fontSize: 22, fontWeight: 800, color, margin: 0 }}>{value}</p>
    {sub && <p style={{ fontSize: 11, color: "#9ca3af", margin: "3px 0 0" }}>{sub}</p>}
  </div>
);

// ── Horizontal bar ─────────────────────────────────────────────────────────

const Bar: React.FC<{ label: string; value: number; color: string; max?: number }> = ({
  label, value, color, max = 1,
}) => {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
        <span style={{ color: "#6b7280" }}>{label}</span>
        <span style={{ fontWeight: 700, color }}>{fmtPct(value)}</span>
      </div>
      <div style={{ backgroundColor: "#f3f4f6", borderRadius: 99, height: 7 }}>
        <div style={{
          width: `${pct}%`, height: "100%", borderRadius: 99,
          backgroundColor: color, transition: "width 0.5s",
        }} />
      </div>
    </div>
  );
};

// ── Main page ──────────────────────────────────────────────────────────────

export const FeedbackPage: React.FC = () => {
  // Default to yesterday
  const yesterday = new Date(Date.now() - 86_400_000).toISOString().split("T")[0];
  const [targetDate, setTargetDate] = useState(yesterday);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runReport = async () => {
    setLoading(true); setError(null); setReport(null);
    try {
      const res = await fetch(`${API}/api/v1/feedback/report/${SHOP}?target_date=${targetDate}`);
      if (!res.ok) throw new Error(await res.text());
      setReport(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed — is backend running?");
    } finally { setLoading(false); }
  };

  return (
    <main style={{ flex: 1, overflowY: "auto", padding: 20, backgroundColor: "#f4f6f8" }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: "#111827", margin: 0 }}>
          Daily Feedback Audit
        </h1>
        <p style={{ fontSize: 13, color: "#9ca3af", margin: "4px 0 0" }}>
          FeedbackAgent — forecast accuracy, waste analysis, safety buffer tuning
        </p>
      </div>

      {/* Date selector + run button */}
      <div style={{
        backgroundColor: "#fff", borderRadius: 14, padding: 16, marginBottom: 20,
        boxShadow: "0 2px 8px rgba(0,0,0,0.07)", display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap",
      }}>
        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: "#6b7280", display: "block", marginBottom: 4 }}>
            ANALYSIS DATE
          </label>
          <input
            type="date" value={targetDate} onChange={e => setTargetDate(e.target.value)}
            style={{
              padding: "8px 12px", borderRadius: 8, border: "1.5px solid #d1d5db",
              fontSize: 13, outline: "none", color: "#111827",
            }}
          />
        </div>
        <button onClick={runReport} disabled={loading} style={{
          display: "flex", alignItems: "center", gap: 6, marginTop: 16,
          backgroundColor: loading ? "#86efac" : "#1a6b5e",
          color: "#fff", border: "none", borderRadius: 9,
          padding: "10px 20px", fontWeight: 700, fontSize: 13,
          cursor: loading ? "not-allowed" : "pointer", minHeight: 44,
        }}>
          <RefreshCw size={14} />
          {loading ? "Running Audit…" : "Run Feedback Agent"}
        </button>
        <p style={{ fontSize: 12, color: "#9ca3af", marginTop: 16, alignSelf: "flex-end" }}>
          Connects to FeedbackAgent — works in demo mode when PostgreSQL is offline.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          backgroundColor: "#fde8eb", border: "1.5px solid #fca5a5",
          borderRadius: 12, padding: "14px 16px", marginBottom: 20,
          fontSize: 13, color: "#b52235",
        }}>
          {error}
        </div>
      )}

      {/* Report results */}
      {report && (
        <>
          {/* Header */}
          <div style={{
            backgroundColor: report.updated ? "#f0fdf4" : "#f9fafb",
            border: `1.5px solid ${report.updated ? "#86efac" : "#e5e7eb"}`,
            borderRadius: 12, padding: "12px 16px", marginBottom: 20,
            display: "flex", alignItems: "center", gap: 10,
          }}>
            <div style={{
              width: 10, height: 10, borderRadius: "50%",
              backgroundColor: report.updated ? "#16a34a" : "#9ca3af",
            }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: "#374151" }}>
              Report for {report.date}
            </span>
            {report.updated && (
              <span style={{
                backgroundColor: "#dcfce7", color: "#16a34a",
                borderRadius: 6, padding: "2px 8px", fontSize: 11, fontWeight: 700,
              }}>
                Safety Buffer Updated
              </span>
            )}
            <span style={{ fontSize: 11, color: "#9ca3af", marginLeft: "auto" }}>
              Generated {new Date(report.generated_at).toLocaleTimeString()}
            </span>
          </div>

          {/* Demo mode notice */}
          {report.demo_mode && (
            <div style={{
              backgroundColor: "#eff6ff", border: "1.5px solid #93c5fd",
              borderRadius: 10, padding: "10px 16px", marginBottom: 20,
              display: "flex", alignItems: "flex-start", gap: 10,
            }}>
              <div style={{
                width: 20, height: 20, borderRadius: "50%", backgroundColor: "#3b82f6",
                display: "flex", alignItems: "center", justifyContent: "center",
                flexShrink: 0, marginTop: 1,
              }}>
                <span style={{ color: "#fff", fontSize: 11, fontWeight: 800 }}>i</span>
              </div>
              <div>
                <p style={{ fontSize: 13, fontWeight: 700, color: "#1d4ed8", margin: "0 0 3px" }}>
                  Demo Mode — Synthetic Data
                </p>
                <p style={{ fontSize: 12, color: "#1e40af", margin: 0, lineHeight: 1.5 }}>
                  PostgreSQL is not running so FeedbackAgent generated realistic synthetic data
                  for this date. The safety buffer tuning logic still runs on this data.
                  To use real historical data, start PostgreSQL with{" "}
                  <code style={{ backgroundColor: "#dbeafe", padding: "1px 4px", borderRadius: 3 }}>
                    docker-compose up -d
                  </code>.
                </p>
              </div>
            </div>
          )}

          {/* KPI grid */}
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
            gap: 12, marginBottom: 20,
          }}>
            <Tile label="Transactions" value={String(report.total_transactions)} />
            <Tile
              label="Forecast Error (MAPE)"
              value={fmtPct(report.mape)}
              color={report.mape > 0.2 ? "#b52235" : report.mape > 0.1 ? "#d97706" : "#16a34a"}
              sub={report.mape < 0.15 ? "On target" : "Needs improvement"}
            />
            <Tile label="Total Waste" value={fmtG(report.total_waste_grams)}
              color={report.pearl_waste_ratio > 0.15 ? "#b52235" : "#111827"}
              sub={`of ${fmtG(report.total_prepared_grams)} prepared`} />
            <Tile label="Waste Ratio" value={fmtPct(report.pearl_waste_ratio)}
              color={report.pearl_waste_ratio > 0.15 ? "#b52235" : "#16a34a"} />
            <Tile label="Stockout Minutes" value={String(report.stockout_minutes)}
              color={report.stockout_minutes > 0 ? "#b52235" : "#16a34a"}
              sub={report.stockout_minutes === 0 ? "No stockouts" : "Lost revenue"} />
          </div>

          {/* Two-column detail */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

            {/* Staff compliance */}
            <div style={{
              backgroundColor: "#fff", borderRadius: 14, padding: 18,
              boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
            }}>
              <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: "0 0 14px" }}>
                Staff Compliance
              </h3>
              <Bar label="Accepted Recommendations" value={report.acceptance_rate} color="#16a34a" />
              <Bar label="Ignored Recommendations"  value={report.ignored_rate}    color="#b52235" />
              <Bar label="Delayed Actions"          value={report.delayed_rate}    color="#d97706" />
            </div>

            {/* Safety factor */}
            <div style={{
              backgroundColor: "#fff", borderRadius: 14, padding: 18,
              boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
            }}>
              <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: "0 0 14px" }}>
                Pearl Safety Buffer
              </h3>
              <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 14 }}>
                <div style={{ textAlign: "center", flex: 1 }}>
                  <p style={{ fontSize: 11, color: "#9ca3af", margin: "0 0 4px" }}>BEFORE</p>
                  <p style={{ fontSize: 28, fontWeight: 800, color: "#6b7280", margin: 0 }}>
                    {report.pearl_safety_factor_before.toFixed(2)}x
                  </p>
                </div>
                <div style={{ fontSize: 20, color: "#9ca3af" }}>→</div>
                <div style={{ textAlign: "center", flex: 1 }}>
                  <p style={{ fontSize: 11, color: "#9ca3af", margin: "0 0 4px" }}>AFTER</p>
                  <p style={{ fontSize: 28, fontWeight: 800,
                    color: report.updated ? "#16a34a" : "#6b7280", margin: 0,
                  }}>
                    {report.pearl_safety_factor_after.toFixed(2)}x
                  </p>
                </div>
              </div>
              <p style={{ fontSize: 12, color: "#6b7280", lineHeight: 1.5, margin: 0 }}>
                {report.updated
                  ? report.pearl_waste_ratio > 0.15
                    ? "High waste detected — safety buffer decreased to avoid over-cooking."
                    : "Stockout detected — safety buffer increased to ensure earlier brew triggers."
                  : "Safety buffer unchanged — within acceptable thresholds."}
              </p>
            </div>
          </div>
        </>
      )}

      {!report && !loading && !error && (
        <div style={{
          textAlign: "center", padding: "48px 24px", backgroundColor: "#fff",
          borderRadius: 14, border: "2px dashed #e5e7eb",
        }}>
          <p style={{ fontSize: 28, margin: "0 0 12px" }}>
          </p>
          <p style={{ fontSize: 15, fontWeight: 700, color: "#374151", margin: "0 0 6px" }}>
            No report yet
          </p>
          <p style={{ fontSize: 13, color: "#6b7280" }}>
            Select a date and click "Run Feedback Agent" to analyze daily performance.
          </p>
        </div>
      )}
    </main>
  );
};
