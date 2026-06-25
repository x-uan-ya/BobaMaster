/**
 * AlertBanner — Critical Operations Banner.
 * Uses inline styles (no Tailwind tokens) so it renders correctly
 * regardless of which Tailwind config is active.
 */

import React, { useEffect, useRef, useState } from "react";
import { AlertTriangle, Clock, ChefHat, CheckCircle } from "lucide-react";
import { useDashboard } from "../store/dashboardStore";
import type { RecommendationAlert } from "../types";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const COOK_TIME: Record<string, number> = {
  tapioca_pearls: 50, black_tea: 15, jasmine_tea: 15, oolong_tea: 15, matcha_powder: 10,
};
const BATCH_SIZE: Record<string, number> = {
  tapioca_pearls: 2000, black_tea: 4000, jasmine_tea: 4000, oolong_tea: 4000, matcha_powder: 500,
};

function fmtShortage(iso: string | null): string {
  if (!iso) return "";
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return "now";
  return `in ~${Math.ceil(diff / 60_000)} min`;
}

interface Props { alert: RecommendationAlert | null; }

export const AlertBanner: React.FC<Props> = ({ alert }) => {
  const { dispatch } = useDashboard();
  const [starting, setStarting] = useState(false);
  const snoozeRef = useRef<number | null>(null);
  useEffect(() => () => { if (snoozeRef.current) clearTimeout(snoozeRef.current); }, []);

  // ── All clear ─────────────────────────────────────────────────────────────
  if (!alert) {
    return (
      <div style={{
        display:"flex", alignItems:"center", gap:12,
        backgroundColor:"#dcfce7", border:"2px solid #16a34a",
        borderRadius:12, padding:"14px 18px",
      }}>
        <CheckCircle size={22} color="#16a34a" />
        <div>
          <p style={{fontWeight:700, color:"#16a34a", margin:0}}>All Clear</p>
          <p style={{fontSize:13, color:"#4b5563", margin:0}}>
            No active alerts. Inventory levels are within safe operating limits.
          </p>
        </div>
      </div>
    );
  }

  const critical = alert.action === "BREW_NOW";
  const borderColor = critical ? "#b52235" : "#d97706";
  const bgColor     = critical ? "#fff5f5" : "#fffbeb";

  const dismiss = () => {
    dispatch({ type:"DISMISS_ALERT", payload: alert.recommendation_id ?? alert.dispatched_at });
  };

  const handleStartCooking = async () => {
    setStarting(true);
    try {
      const res = await fetch(`${API}/api/v1/inventory/brew/start`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
          shop_id: alert.shop_id,
          ingredient_id: alert.ingredient_id,
          initial_qty_grams: BATCH_SIZE[alert.ingredient_id] ?? 2000,
        }),
      });
      const data = await res.json();
      dismiss();
      dispatch({
        type:"START_BREW_TIMER",
        payload: {
          id: crypto.randomUUID(),
          batch_id: data.batch_id ?? "",
          ingredient_id: alert.ingredient_id,
          label: alert.ingredient_id.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase()),
          started_at: Date.now(),
          cook_time_ms: (COOK_TIME[alert.ingredient_id] ?? 30) * 60_000,
        },
      });
    } catch (e) { console.error(e); }
    finally { setStarting(false); }
  };

  const handleSnooze = () => {
    const id = alert.recommendation_id ?? alert.dispatched_at;
    dispatch({ type:"DISMISS_ALERT", payload: id });
    snoozeRef.current = window.setTimeout(() =>
      dispatch({ type:"PUSH_ALERT", payload: { ...alert, recommendation_id: null } }),
      5 * 60_000
    );
  };

  return (
    <div role="alert" aria-live="assertive" style={{
      backgroundColor: bgColor,
      border: `2px solid ${borderColor}`,
      borderRadius: 12,
      padding: "16px 20px",
      display: "flex", alignItems: "flex-start", gap: 16,
      animation: critical ? "alert-flash 1.4s ease-in-out infinite" : undefined,
    }}>
      {/* Icon */}
      <div style={{
        width:44, height:44, borderRadius:10, flexShrink:0,
        backgroundColor: borderColor + "20",
        display:"flex", alignItems:"center", justifyContent:"center",
      }}>
        <AlertTriangle size={22} color={borderColor} />
      </div>

      {/* Content */}
      <div style={{flex:1, minWidth:0}}>
        <div style={{display:"flex", alignItems:"center", gap:8, flexWrap:"wrap", marginBottom:4}}>
          <span style={{
            backgroundColor: borderColor, color:"#fff",
            borderRadius:6, padding:"2px 8px", fontSize:11, fontWeight:700,
          }}>
            {critical ? "CRITICAL" : "WARNING"}
          </span>
          <span style={{fontSize:15, fontWeight:700, color:"#1f2937"}}>
            {alert.action_string}
          </span>
        </div>

        <p style={{fontSize:13, color:"#374151", margin:"0 0 8px", lineHeight:1.5}}>
          {alert.explanation_text}
        </p>

        <div style={{display:"flex", flexWrap:"wrap", gap:14, fontSize:12, color:"#6b7280"}}>
          {alert.predicted_shortage_at && (
            <span style={{display:"flex", alignItems:"center", gap:4}}>
              <Clock size={12}/> Stockout {fmtShortage(alert.predicted_shortage_at)}
            </span>
          )}
          <span>Stock: {Math.round(alert.current_stock_grams)}g</span>
          <span>Demand: {Math.round(alert.predicted_consumption_grams)}g</span>
          {!alert.llm_used && <span style={{fontStyle:"italic", opacity:0.6}}>(fallback — add GEMINI_API_KEY)</span>}
        </div>
      </div>

      {/* Action buttons */}
      <div style={{display:"flex", flexDirection:"column", gap:8, flexShrink:0}}>
        <button onClick={handleStartCooking} disabled={starting} style={{
          display:"flex", alignItems:"center", gap:6,
          backgroundColor: starting ? "#9ca3af" : "#b52235",
          color:"#fff", border:"none", borderRadius:10, cursor: starting ? "not-allowed" : "pointer",
          padding:"10px 16px", fontWeight:700, fontSize:13, minHeight:44, whiteSpace:"nowrap",
        }}>
          <ChefHat size={16}/>{starting ? "Starting…" : "Start Cooking"}
        </button>
        <button onClick={handleSnooze} style={{
          backgroundColor:"transparent", color:"#6b7280", border:"none",
          borderRadius:10, cursor:"pointer", padding:"8px 16px",
          fontWeight:500, fontSize:13, minHeight:40,
        }}>
          Snooze 5m
        </button>
      </div>
    </div>
  );
};
