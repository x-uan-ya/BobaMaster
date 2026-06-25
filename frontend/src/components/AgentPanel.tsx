/**
 * AgentPanel — Interactive AI Agent Control Panel
 *
 * Three direct entry points into the multi-agent pipeline:
 *  1. Run AI Evaluation  — full OpsDecider → Gemini → WebSocket pipeline
 *  2. Simulate POS Sale  — DecompoAgent → InventoryAgent deduction
 *  3. Get Demand Forecast — PredictorAgent + ContextAgent
 *
 * Plus a live "All Agents Status" section showing decisions for all
 * 5 tracked ingredients from OpsDeciderAgent.
 */

import React, { useState, useCallback } from "react";
import {
  Brain, ShoppingCart, TrendingUp, ChevronDown, ChevronUp,
  Loader2, CheckCircle, AlertCircle, Activity, RefreshCw,
} from "lucide-react";
import { useDashboard } from "../store/dashboardStore";
import type { NavPage } from "./NavigationRail";

const API  = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SHOP = import.meta.env.VITE_SHOP_ID  ?? "00000000-0000-0000-0000-000000000001";

type S = "idle" | "loading" | "ok" | "err";

interface ForecastResult {
  ingredient_id: string;
  t30_grams: number; t60_grams: number; t120_grams: number;
  school_multiplier: number; temp_multiplier: number; rain_multiplier: number;
}

interface Decision {
  ingredient_id: string;
  action: "BREW_NOW" | "WARN" | "WAIT";
  current_stock_grams: number;
  predicted_consumption_grams: number;
  target_runway_grams: number;
  evaluated_at: string;
}

interface Deduction { ingredient_id: string; qty_grams_ml: number; }

// ── Helpers ────────────────────────────────────────────────────────────────

const fmtG = (g: number) => g >= 1000 ? `${(g/1000).toFixed(1)}kg` : `${Math.round(g)}g`;
const fmtId = (id: string) => id.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());

const ACTION_COLOR: Record<string,string> = {
  BREW_NOW: "#b52235", WARN: "#d97706", WAIT: "#16a34a",
};
const ACTION_BG: Record<string,string> = {
  BREW_NOW: "#fde8eb", WARN: "#fef3c7", WAIT: "#dcfce7",
};
const ACTION_ICON: Record<string,string> = {
  BREW_NOW: "🔴", WARN: "🟡", WAIT: "🟢",
};

// ── Tiny status badge ──────────────────────────────────────────────────────

const Badge: React.FC<{ state: S; msg?: string }> = ({ state, msg }) => {
  if (state === "idle") return null;
  const map = {
    loading: { bg:"#fef3c7", color:"#d97706", icon:<Loader2 size={13} className="animate-spin"/>, text: msg ?? "Working…" },
    ok:      { bg:"#dcfce7", color:"#16a34a", icon:<CheckCircle size={13}/>, text: msg ?? "Done!" },
    err:     { bg:"#fde8eb", color:"#b52235", icon:<AlertCircle size={13}/>, text: msg ?? "Failed — is backend running?" },
  }[state];
  return (
    <div style={{display:"flex",alignItems:"center",gap:5,padding:"4px 10px",
      borderRadius:99,backgroundColor:map.bg,color:map.color,fontSize:11,fontWeight:600,marginTop:6}}>
      {map.icon}{map.text}
    </div>
  );
};

// ── Agent decision row ─────────────────────────────────────────────────────

const DecisionRow: React.FC<{ d: Decision }> = ({ d }) => (
  <div style={{
    display:"flex", alignItems:"center", justifyContent:"space-between",
    padding:"8px 12px", borderRadius:8, marginBottom:4,
    backgroundColor: ACTION_BG[d.action] ?? "#f9f9f9",
    border:`1px solid ${ACTION_COLOR[d.action] ?? "#e5e7eb"}`,
  }}>
    <div style={{display:"flex",alignItems:"center",gap:8}}>
      <span style={{fontSize:14}}>{ACTION_ICON[d.action]}</span>
      <div>
        <p style={{fontSize:12,fontWeight:700,color:"#1f2937",margin:0}}>{fmtId(d.ingredient_id)}</p>
        <p style={{fontSize:10,color:"#6b7280",margin:0}}>
          Stock: {fmtG(d.current_stock_grams)} · Demand: {fmtG(d.predicted_consumption_grams)}
        </p>
      </div>
    </div>
    <span style={{
      backgroundColor: ACTION_COLOR[d.action], color:"#fff",
      borderRadius:6, padding:"3px 10px", fontSize:11, fontWeight:700,
    }}>
      {d.action}
    </span>
  </div>
);

// ── Forecast result card ───────────────────────────────────────────────────

const ForecastCard: React.FC<{ r: ForecastResult }> = ({ r }) => {
  const mults = [
    r.school_multiplier > 1 && `School +${Math.round((r.school_multiplier-1)*100)}%`,
    r.temp_multiplier   > 1 && `Heat +${Math.round((r.temp_multiplier-1)*100)}%`,
    r.rain_multiplier   > 1 && `Rain +${Math.round((r.rain_multiplier-1)*100)}%`,
  ].filter(Boolean);
  return (
    <div style={{marginTop:10,backgroundColor:"#f0fdf4",border:"1px solid #86efac",borderRadius:10,padding:"12px 14px"}}>
      <p style={{fontWeight:700,fontSize:12,color:"#15803d",marginBottom:8}}>
        📈 Forecast — {fmtId(r.ingredient_id)}
      </p>
      <div style={{display:"flex",gap:8}}>
        {[{h:"30 min",g:r.t30_grams},{h:"60 min",g:r.t60_grams},{h:"120 min",g:r.t120_grams}].map(({h,g})=>(
          <div key={h} style={{flex:1,backgroundColor:"#fff",borderRadius:8,padding:"8px 6px",
            textAlign:"center",border:"1px solid #d1fae5"}}>
            <p style={{fontSize:10,color:"#6b7280",margin:"0 0 2px"}}>{h}</p>
            <p style={{fontSize:15,fontWeight:800,color:"#15803d",margin:0}}>{fmtG(g)}</p>
          </div>
        ))}
      </div>
      {mults.length > 0 && (
        <p style={{fontSize:11,color:"#16a34a",marginTop:6}}>
          Boosts: {mults.join(" · ")}
        </p>
      )}
    </div>
  );
};

// ── Main component ─────────────────────────────────────────────────────────

const INGREDIENTS = ["tapioca_pearls","black_tea","jasmine_tea","oolong_tea","matcha_powder"];

interface Props { onNavigate?: (page: NavPage) => void; }

export const AgentPanel: React.FC<Props> = ({ onNavigate }) => {
  const { dispatch } = useDashboard();
  const [open,  setOpen]  = useState(true);

  // Per-action state
  const [evalS,    setEvalS]    = useState<S>("idle");
  const [evalMsg,  setEvalMsg]  = useState<string>();
  const [saleS,    setSaleS]    = useState<S>("idle");
  const [saleMsg,  setSaleMsg]  = useState<string>();
  const [saleDeductions, setSaleDeductions] = useState<Deduction[]>([]);
  const [forecastS,  setForecastS]  = useState<S>("idle");
  const [forecastR,  setForecastR]  = useState<ForecastResult | null>(null);
  const [ingredient, setIngredient] = useState("tapioca_pearls");
  const [decisionsS, setDecisionsS] = useState<S>("idle");
  const [decisions,  setDecisions]  = useState<Decision[]>([]);
  const [decisionsMsg, setDecisionsMsg] = useState<string>();

  // ── 1. Run full AI evaluation (DispatcherAgent → Gemini → WS) ────────────
  const handleEval = useCallback(async () => {
    setEvalS("loading"); setEvalMsg("OpsDecider → Gemini 1.5 Flash → WebSocket…");
    try {
      const res = await fetch(`${API}/api/v1/dispatcher/trigger-test-alert?shop_id=${SHOP}`,
        { method:"POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const data = await res.json();
      // DispatchMessage → push as RecommendationAlert shape into store
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
      const llm = data.llm_used ? "Gemini 1.5 Flash ✨" : "fallback (set GEMINI_API_KEY for real LLM)";
      setEvalMsg(`Alert visible above ↑ — used ${llm}`);
      setEvalS("ok");
    } catch (e) {
      setEvalMsg(e instanceof Error ? e.message : String(e));
      setEvalS("err");
    }
  }, [dispatch]);

  // ── 2. Simulate POS sale (DecompoAgent → InventoryAgent) ─────────────────
  const handleSale = useCallback(async () => {
    setSaleS("loading"); setSaleMsg("Sending POS transaction…"); setSaleDeductions([]);
    try {
      const payload = {
        transaction_id: `demo-${Date.now()}`,
        shop_id: SHOP,
        timestamp: new Date().toISOString(),   // ← required field
        items: [{
          name: "Classic Milk Tea",            // ← "name" not "item_name"
          quantity: 5,
          size: "L",
          ice_level: "normal ice",
          modifiers: ["extra pearls"],
        }],
      };
      const res = await fetch(`${API}/api/v1/pos/webhook`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const data = await res.json();
      const deductions: Deduction[] = data.deductions ?? [];
      setSaleDeductions(deductions);
      const summary = deductions.map(d=>`${fmtId(d.ingredient_id)}: ${fmtG(d.qty_grams_ml)}`).join(" · ");
      setSaleMsg(`Deducted — ${summary || "see inventory"}`);
      setSaleS("ok");

      // Refresh inventory in the store so ingredient rings update
      const invRes = await fetch(`${API}/api/v1/inventory/shop/${SHOP}`);
      if (invRes.ok) {
        const list: any[] = await invRes.json();
        list.forEach(item => dispatch({ type:"UPSERT_INGREDIENT", payload: item }));
      }
      // Navigate to inventory page if handler provided
      if (onNavigate) onNavigate("inventory");
    } catch (e) {
      setSaleMsg(e instanceof Error ? e.message : String(e));
      setSaleS("err");
    }
  }, [dispatch, onNavigate]);

  // ── 3. Demand forecast (PredictorAgent + ContextAgent) ───────────────────
  const handleForecast = useCallback(async () => {
    setForecastS("loading"); setForecastR(null);
    try {
      const params = new URLSearchParams({
        grams_per_min_10m: "8",
        grams_per_min_30m: "7",
        grams_per_min_60m: "6",
      });
      const res = await fetch(`${API}/api/v1/forecast/${SHOP}/${ingredient}?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const data = await res.json();
      setForecastR({ ...data, ingredient_id: ingredient });
      setForecastS("ok");
      if (onNavigate) onNavigate("forecast");
    } catch (e) {
      setForecastS("err");
    }
  }, [ingredient, onNavigate]);

  // ── 4. All-agents decision sweep ─────────────────────────────────────────
  const handleDecisions = useCallback(async () => {
    setDecisionsS("loading"); setDecisionsMsg("Running safety-stock evaluation…");
    try {
      const res = await fetch(`${API}/api/v1/operations/decisions/${SHOP}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const data = await res.json();
      setDecisions(data.decisions ?? []);
      const critical = (data.decisions ?? []).filter((d:Decision)=>d.action==="BREW_NOW").length;
      setDecisionsMsg(critical > 0 ? `${critical} ingredient(s) need brewing now!` : "All ingredients within safe range.");
      setDecisionsS("ok");
    } catch (e) {
      setDecisionsMsg(e instanceof Error ? e.message : String(e));
      setDecisionsS("err");
    }
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────

  const btnBase: React.CSSProperties = {
    width:"100%", padding:"9px 0", color:"#fff", border:"none",
    borderRadius:8, fontWeight:700, fontSize:13, cursor:"pointer",
    display:"flex", alignItems:"center", justifyContent:"center", gap:6, minHeight:40,
  };

  return (
    <div style={{backgroundColor:"#fff",border:"2px solid #e0f2fe",borderRadius:14,
      overflow:"hidden",boxShadow:"0 2px 8px rgba(0,0,0,0.08)"}}>

      {/* Header */}
      <button onClick={()=>setOpen(o=>!o)} aria-expanded={open}
        style={{width:"100%",display:"flex",alignItems:"center",justifyContent:"space-between",
          padding:"12px 16px",background:"linear-gradient(135deg,#0ea5e9 0%,#1a6b5e 100%)",
          border:"none",cursor:"pointer"}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <Brain size={20} color="#fff"/>
          <span style={{color:"#fff",fontWeight:700,fontSize:14}}>AI Agent Controls</span>
          <span style={{backgroundColor:"rgba(255,255,255,0.2)",color:"#fff",
            borderRadius:99,padding:"2px 8px",fontSize:11,fontWeight:600}}>
            7 Agents
          </span>
        </div>
        {open ? <ChevronUp size={18} color="#fff"/> : <ChevronDown size={18} color="#fff"/>}
      </button>

      {open && (
        <div style={{padding:16,display:"flex",flexDirection:"column",gap:14}}>
          <p style={{fontSize:12,color:"#6b7280",margin:0}}>
            Interact directly with the agent pipeline — no POS system required.
          </p>

          {/* ── Top row: 3 action cards ──────────────────────────── */}
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12}}>

            {/* 1 — Run AI Evaluation */}
            <div style={{backgroundColor:"#faf5ff",border:"1px solid #d8b4fe",borderRadius:12,padding:14}}>
              <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
                <div style={{width:30,height:30,borderRadius:7,backgroundColor:"#7c3aed",
                  display:"flex",alignItems:"center",justifyContent:"center"}}>
                  <Brain size={15} color="#fff"/>
                </div>
                <div>
                  <p style={{fontSize:12,fontWeight:700,color:"#1f2937",margin:0}}>Run AI Evaluation</p>
                  <p style={{fontSize:10,color:"#6b7280",margin:0}}>OpsDecider → Gemini → WS</p>
                </div>
              </div>
              <p style={{fontSize:11,color:"#6b7280",marginBottom:10,lineHeight:1.4}}>
                Triggers the full pipeline: evaluates tapioca pearl stock, calls Gemini 1.5 Flash, broadcasts alert card above.
              </p>
              <button onClick={handleEval} disabled={evalS==="loading"}
                style={{...btnBase,backgroundColor:evalS==="loading"?"#a78bfa":"#7c3aed"}}>
                {evalS==="loading"
                  ? <><Loader2 size={13} className="animate-spin"/>Calling Gemini…</>
                  : <><Brain size={13}/>Run Evaluation</>}
              </button>
              <Badge state={evalS} msg={evalMsg}/>
            </div>

            {/* 2 — Simulate POS Sale */}
            <div style={{backgroundColor:"#fff7ed",border:"1px solid #fed7aa",borderRadius:12,padding:14}}>
              <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
                <div style={{width:30,height:30,borderRadius:7,backgroundColor:"#ea580c",
                  display:"flex",alignItems:"center",justifyContent:"center"}}>
                  <ShoppingCart size={15} color="#fff"/>
                </div>
                <div>
                  <p style={{fontSize:12,fontWeight:700,color:"#1f2937",margin:0}}>Simulate POS Sale</p>
                  <p style={{fontSize:10,color:"#6b7280",margin:0}}>DecompoAgent → InventoryAgent</p>
                </div>
              </div>
              <p style={{fontSize:11,color:"#6b7280",marginBottom:10,lineHeight:1.4}}>
                Fires 5× Large Classic Milk Tea (extra pearls) — deducts from FIFO inventory. Opens Inventory page.
              </p>
              <button onClick={handleSale} disabled={saleS==="loading"}
                style={{...btnBase,backgroundColor:saleS==="loading"?"#fb923c":"#ea580c"}}>
                {saleS==="loading"
                  ? <><Loader2 size={13} className="animate-spin"/>Processing…</>
                  : <><ShoppingCart size={13}/>Simulate Sale</>}
              </button>
              <Badge state={saleS} msg={saleMsg}/>
              {saleDeductions.length > 0 && saleS==="ok" && (
                <div style={{marginTop:8,backgroundColor:"#fff",borderRadius:8,padding:"8px 10px",
                  border:"1px solid #fed7aa"}}>
                  {saleDeductions.map(d=>(
                    <div key={d.ingredient_id} style={{display:"flex",justifyContent:"space-between",
                      fontSize:11,color:"#374151",padding:"2px 0"}}>
                      <span>{fmtId(d.ingredient_id)}</span>
                      <span style={{fontWeight:700,color:"#ea580c"}}>−{fmtG(d.qty_grams_ml)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 3 — Demand Forecast */}
            <div style={{backgroundColor:"#f0fdf4",border:"1px solid #86efac",borderRadius:12,padding:14}}>
              <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
                <div style={{width:30,height:30,borderRadius:7,backgroundColor:"#16a34a",
                  display:"flex",alignItems:"center",justifyContent:"center"}}>
                  <TrendingUp size={15} color="#fff"/>
                </div>
                <div>
                  <p style={{fontSize:12,fontWeight:700,color:"#1f2937",margin:0}}>Get Demand Forecast</p>
                  <p style={{fontSize:10,color:"#6b7280",margin:0}}>PredictorAgent + ContextAgent</p>
                </div>
              </div>
              <select value={ingredient} onChange={e=>setIngredient(e.target.value)}
                style={{width:"100%",padding:"5px 8px",marginBottom:8,borderRadius:6,
                  border:"1px solid #86efac",fontSize:12,color:"#374151",backgroundColor:"#fff",cursor:"pointer"}}>
                {INGREDIENTS.map(id=>(
                  <option key={id} value={id}>{fmtId(id)}</option>
                ))}
              </select>
              <button onClick={handleForecast} disabled={forecastS==="loading"}
                style={{...btnBase,backgroundColor:forecastS==="loading"?"#4ade80":"#16a34a"}}>
                {forecastS==="loading"
                  ? <><Loader2 size={13} className="animate-spin"/>Forecasting…</>
                  : <><TrendingUp size={13}/>Get Forecast</>}
              </button>
              {forecastS==="err" && <Badge state="err"/>}
            </div>
          </div>

          {/* Forecast result */}
          {forecastR && forecastS==="ok" && <ForecastCard r={forecastR}/>}

          {/* ── All Agents Decision Sweep ──────────────────────── */}
          <div style={{backgroundColor:"#f8fafc",border:"1px solid #e2e8f0",borderRadius:12,padding:14}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:10}}>
              <div style={{display:"flex",alignItems:"center",gap:8}}>
                <Activity size={16} color="#0891b2"/>
                <span style={{fontSize:13,fontWeight:700,color:"#1f2937"}}>All-Agent Decision Sweep</span>
                <span style={{fontSize:11,color:"#6b7280"}}>
                  OpsDeciderAgent · InventoryAgent · PredictorAgent · ContextAgent · FeedbackAgent
                </span>
              </div>
              <button onClick={handleDecisions} disabled={decisionsS==="loading"}
                style={{display:"flex",alignItems:"center",gap:5,padding:"6px 14px",
                  backgroundColor:"#0891b2",color:"#fff",border:"none",borderRadius:8,
                  fontSize:12,fontWeight:700,cursor:"pointer",minHeight:36}}>
                {decisionsS==="loading"
                  ? <><Loader2 size={13} className="animate-spin"/>Running…</>
                  : <><RefreshCw size={13}/>Evaluate All</>}
              </button>
            </div>

            {decisionsS==="idle" && (
              <p style={{fontSize:12,color:"#9ca3af",textAlign:"center",padding:"12px 0"}}>
                Click "Evaluate All" to run OpsDeciderAgent across all 5 tracked ingredients.
              </p>
            )}
            <Badge state={decisionsS==="ok"?"ok":decisionsS==="err"?"err":"idle"} msg={decisionsMsg}/>
            {decisions.length > 0 && (
              <div style={{marginTop:10}}>
                {decisions.map(d=><DecisionRow key={d.ingredient_id} d={d}/>)}
              </div>
            )}
          </div>

          {/* Pipeline legend */}
          <div style={{display:"flex",gap:12,flexWrap:"wrap",padding:"8px 12px",
            backgroundColor:"#f8fafc",borderRadius:8,border:"1px solid #e2e8f0",alignItems:"center"}}>
            <span style={{fontSize:11,color:"#64748b",fontWeight:600}}>Pipeline:</span>
            {[
              {c:"#ea580c",l:"DecompoAgent"},{c:"#0891b2",l:"ContextAgent"},
              {c:"#16a34a",l:"PredictorAgent"},{c:"#1a6b5e",l:"InventoryAgent"},
              {c:"#d97706",l:"OpsDeciderAgent"},{c:"#7c3aed",l:"DispatcherAgent → Gemini 1.5 Flash"},
              {c:"#6b7280",l:"FeedbackAgent"},
            ].map(({c,l})=>(
              <span key={l} style={{display:"flex",alignItems:"center",gap:4,fontSize:11,color:"#374151"}}>
                <span style={{width:7,height:7,borderRadius:"50%",backgroundColor:c,flexShrink:0}}/>
                {l}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
