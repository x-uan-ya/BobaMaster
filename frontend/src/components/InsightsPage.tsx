/**
 * InsightsPage — LLM Operational Logs & Agent Decision Feed.
 *
 * Shows:
 *  - All-agent evaluation feed (decisions from OpsDeciderAgent)
 *  - Run AI Evaluation inline — triggers Gemini explanation
 *  - Live alert history from the current session
 */

import React, { useState, useCallback } from "react";
import { RefreshCw, Brain, Activity } from "lucide-react";
import { useDashboard } from "../store/dashboardStore";
import type { RecommendationAlert } from "../types";

const API  = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SHOP = import.meta.env.VITE_SHOP_ID  ?? "00000000-0000-0000-0000-000000000001";

const fmtId = (id: string) => id.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
const fmtG  = (g: number)  => g >= 1000 ? `${(g / 1000).toFixed(1)} kg` : `${Math.round(g)} g`;

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60_000);
  if (m < 1)  return "just now";
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ${m % 60}m ago`;
}

const ACTION_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  BREW_NOW: { bg: "#fff5f5", text: "#b52235", border: "#fca5a5" },
  WARN:     { bg: "#fffbeb", text: "#d97706", border: "#fde68a" },
  WAIT:     { bg: "#f0fdf4", text: "#16a34a", border: "#86efac" },
};

// ── Decision card ──────────────────────────────────────────────────────────

interface Decision {
  ingredient_id: string;
  action: string;
  current_stock_grams: number;
  predicted_consumption_grams: number;
  target_runway_grams: number;
  evaluated_at: string;
}

const DecisionCard: React.FC<{ d: Decision }> = ({ d }) => {
  const c = ACTION_COLORS[d.action] ?? ACTION_COLORS.WAIT;
  return (
    <div style={{
      backgroundColor: c.bg, border: `1.5px solid ${c.border}`,
      borderRadius: 12, padding: "14px 16px", marginBottom: 10,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div>
          <span style={{
            backgroundColor: c.text, color: "#fff", borderRadius: 6,
            padding: "2px 8px", fontSize: 11, fontWeight: 700, marginRight: 8,
          }}>
            {d.action}
          </span>
          <span style={{ fontSize: 14, fontWeight: 700, color: "#111827" }}>
            {fmtId(d.ingredient_id)}
          </span>
        </div>
        <span style={{ fontSize: 11, color: "#9ca3af" }}>{timeAgo(d.evaluated_at)}</span>
      </div>
      <div style={{ display: "flex", gap: 16, fontSize: 12, color: "#6b7280", flexWrap: "wrap" }}>
        <span>Stock: <strong style={{ color: "#111827" }}>{fmtG(d.current_stock_grams)}</strong></span>
        <span>Demand: <strong style={{ color: "#111827" }}>{fmtG(d.predicted_consumption_grams)}</strong></span>
        <span>Runway: <strong style={{ color: d.target_runway_grams < 0 ? "#b52235" : "#111827" }}>
          {fmtG(d.target_runway_grams)}
        </strong></span>
      </div>
    </div>
  );
};

// ── Alert log card ─────────────────────────────────────────────────────────

const AlertLogCard: React.FC<{ alert: RecommendationAlert }> = ({ alert }) => {
  const c = ACTION_COLORS[alert.action] ?? ACTION_COLORS.WAIT;
  return (
    <div style={{
      backgroundColor: c.bg, border: `1.5px solid ${c.border}`,
      borderRadius: 12, padding: "14px 16px", marginBottom: 10,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            backgroundColor: c.text, color: "#fff",
            borderRadius: 6, padding: "2px 8px", fontSize: 11, fontWeight: 700,
          }}>
            {alert.action}
          </span>
          <span style={{ fontSize: 13, fontWeight: 700, color: "#111827" }}>
            {alert.action_string}
          </span>
        </div>
        <span style={{ fontSize: 11, color: "#9ca3af" }}>{timeAgo(alert.dispatched_at)}</span>
      </div>
      <p style={{ fontSize: 13, color: "#374151", margin: "0 0 6px", lineHeight: 1.5 }}>
        {alert.explanation_text}
      </p>
      <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#9ca3af" }}>
        <span>Stock: {fmtG(alert.current_stock_grams)}</span>
        <span>Demand: {fmtG(alert.predicted_consumption_grams)}</span>
        {!alert.llm_used && <span style={{ fontStyle: "italic" }}>fallback explanation</span>}
        {alert.llm_used  && <span style={{ color: "#7c3aed", fontWeight: 600 }}>Gemini 1.5 Flash</span>}
      </div>
    </div>
  );
};

// ── Main page ──────────────────────────────────────────────────────────────

export const InsightsPage: React.FC = () => {
  const { state, dispatch } = useDashboard();
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [decidingLoading, setDecidingLoading] = useState(false);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalMsg, setEvalMsg] = useState<string | null>(null);

  const runDecisions = useCallback(async () => {
    setDecidingLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/operations/decisions/${SHOP}`);
      if (res.ok) {
        const data = await res.json();
        setDecisions(data.decisions ?? []);
      }
    } catch { /* silent */ }
    finally { setDecidingLoading(false); }
  }, []);

  const runEval = useCallback(async () => {
    setEvalLoading(true); setEvalMsg(null);
    try {
      const res = await fetch(`${API}/api/v1/dispatcher/trigger-test-alert?shop_id=${SHOP}`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      dispatch({
        type: "PUSH_ALERT",
        payload: {
          event_type: "recommendation_alert",
          shop_id:    data.shop_id,
          ingredient_id: data.ingredient_id,
          action:     data.action,
          action_string: data.action_string,
          explanation_text: data.explanation_text,
          current_stock_grams: data.current_stock_grams,
          predicted_consumption_grams: data.predicted_consumption_grams,
          target_runway_grams: data.target_runway_grams,
          recommendation_id: data.recommendation_id ?? null,
          predicted_shortage_at: data.predicted_shortage_at ?? null,
          dispatched_at: data.dispatched_at,
          llm_used: data.llm_used,
        },
      });
      setEvalMsg(data.llm_used
        ? "Gemini 1.5 Flash explanation generated. Check Dashboard for the alert."
        : "Fallback explanation used — set GEMINI_API_KEY for real LLM output.");
    } catch (e) {
      setEvalMsg(e instanceof Error ? e.message : "Failed");
    } finally { setEvalLoading(false); }
  }, [dispatch]);

  const sessionAlerts = state.alerts;

  return (
    <main style={{ flex: 1, overflowY: "auto", padding: 20, backgroundColor: "#f4f6f8" }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: "#111827", margin: 0 }}>
          Insights & Logs
        </h1>
        <p style={{ fontSize: 13, color: "#9ca3af", margin: "4px 0 0" }}>
          Agent decisions, LLM explanations, and operational alerts
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, alignItems: "start" }}>

        {/* Left — OpsDecider sweep */}
        <div>
          <div style={{
            backgroundColor: "#fff", borderRadius: 14, padding: 18,
            boxShadow: "0 2px 8px rgba(0,0,0,0.07)", marginBottom: 16,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Activity size={16} color="#0891b2" />
                <span style={{ fontSize: 14, fontWeight: 800, color: "#111827" }}>
                  Agent Decision Sweep
                </span>
              </div>
              <button onClick={runDecisions} disabled={decidingLoading} style={{
                display: "flex", alignItems: "center", gap: 5,
                backgroundColor: "#0891b2", color: "#fff", border: "none",
                borderRadius: 8, padding: "7px 13px", fontWeight: 700, fontSize: 12,
                cursor: "pointer",
              }}>
                <RefreshCw size={13} />
                {decidingLoading ? "Running…" : "Evaluate All"}
              </button>
            </div>
            <p style={{ fontSize: 12, color: "#9ca3af", margin: "0 0 12px" }}>
              Chains: InventoryAgent + ContextAgent + PredictorAgent + OpsDeciderAgent
            </p>

            {decisions.length === 0 && !decidingLoading && (
              <div style={{ textAlign: "center", padding: "24px 0", color: "#9ca3af", fontSize: 13 }}>
                Click "Evaluate All" to run the full agent sweep
              </div>
            )}
            {decisions.map(d => <DecisionCard key={d.ingredient_id} d={d} />)}
          </div>

          {/* Gemini evaluation */}
          <div style={{
            backgroundColor: "#faf5ff", borderRadius: 14, padding: 18,
            border: "1.5px solid #d8b4fe", boxShadow: "0 2px 8px rgba(0,0,0,0.07)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <Brain size={16} color="#7c3aed" />
              <span style={{ fontSize: 14, fontWeight: 800, color: "#111827" }}>
                Gemini 1.5 Flash Evaluation
              </span>
            </div>
            <p style={{ fontSize: 12, color: "#6b7280", margin: "0 0 12px", lineHeight: 1.5 }}>
              Triggers the full pipeline: OpsDeciderAgent evaluates stock levels,
              DispatcherAgent calls Gemini 1.5 Flash to generate a natural language
              explanation, then broadcasts the alert over WebSocket.
            </p>
            <button onClick={runEval} disabled={evalLoading} style={{
              display: "flex", alignItems: "center", gap: 6,
              backgroundColor: evalLoading ? "#a78bfa" : "#7c3aed",
              color: "#fff", border: "none", borderRadius: 9,
              padding: "10px 18px", fontWeight: 700, fontSize: 13,
              cursor: evalLoading ? "not-allowed" : "pointer", minHeight: 44,
            }}>
              <Brain size={15} />
              {evalLoading ? "Calling Gemini…" : "Run AI Evaluation"}
            </button>
            {evalMsg && (
              <div style={{
                marginTop: 10, padding: "8px 12px", borderRadius: 8, fontSize: 12,
                backgroundColor: evalMsg.includes("Failed") || evalMsg.includes("HTTP") ? "#fde8eb" : "#f3e8ff",
                color: evalMsg.includes("Failed") || evalMsg.includes("HTTP") ? "#b52235" : "#7c3aed",
                border: `1px solid ${evalMsg.includes("Failed") ? "#fca5a5" : "#d8b4fe"}`,
              }}>
                {evalMsg}
              </div>
            )}
          </div>
        </div>

        {/* Right — session alert log */}
        <div style={{
          backgroundColor: "#fff", borderRadius: 14, padding: 18,
          boxShadow: "0 2px 8px rgba(0,0,0,0.07)",
        }}>
          <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
            Session Alert Log
          </h3>
          <p style={{ fontSize: 12, color: "#9ca3af", margin: "0 0 14px" }}>
            Alerts generated during this session (cleared on page refresh)
          </p>
          {sessionAlerts.length === 0 ? (
            <div style={{ textAlign: "center", padding: "32px 0", color: "#9ca3af", fontSize: 13 }}>
              No alerts this session yet.
              <br />Run an AI Evaluation to generate one.
            </div>
          ) : (
            sessionAlerts.map((a, i) => <AlertLogCard key={a.recommendation_id ?? i} alert={a} />)
          )}
        </div>
      </div>
    </main>
  );
};
