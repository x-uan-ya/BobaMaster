/**
 * InventoryPage — Live ingredient management for kitchen staff.
 *
 * Two core workflows:
 *  1. COOK  — Staff enters the amount cooked (grams).
 *             Creates a batch via POST /brew/start, then immediately
 *             completes it via POST /brew/complete so the stock is usable.
 *             (A real deployment would have a countdown before completion;
 *              for demo purposes we complete immediately so stock shows up.)
 *
 *  2. SELL  — Staff logs a customer order by selecting a drink and quantity.
 *             Calls POST /api/v1/pos/webhook which runs through DecompoAgent
 *             → InventoryAgent FIFO deduction automatically.
 *
 * Additional actions per-batch:
 *  - Mark Ready  — move a brewing batch to active (POST /brew/complete)
 *  - Log Waste   — discard a quantity from a specific batch
 *  - Recalibrate — override total with a physical scale reading
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  RefreshCw, Plus, ShoppingCart, Scale,
  CheckCircle, Trash2, ChevronDown, ChevronUp,
} from "lucide-react";
import { useDashboard } from "../store/dashboardStore";
import { CircularProgress } from "./CircularProgress";
import type { InventoryIngredient, PreparedBatch } from "../types";

const API  = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SHOP = import.meta.env.VITE_SHOP_ID  ?? "00000000-0000-0000-0000-000000000001";

// ── Configuration ──────────────────────────────────────────────────────────

const MAX_GRAMS: Record<string, number> = {
  tapioca_pearls: 4000, black_tea: 8000, jasmine_tea: 8000,
  oolong_tea: 8000, matcha_powder: 1000,
};

// Typical single-batch cook sizes (grams) shown as default in the cook form
const DEFAULT_BATCH: Record<string, number> = {
  tapioca_pearls: 2000, black_tea: 4000, jasmine_tea: 4000,
  oolong_tea: 4000, matcha_powder: 500,
};

// Drink menu mapped to the ingredient they primarily consume
const DRINKS: { name: string; primary: string }[] = [
  { name: "Classic Milk Tea",        primary: "tapioca_pearls" },
  { name: "Jasmine Milk Tea",        primary: "jasmine_tea" },
  { name: "Oolong Milk Tea",         primary: "oolong_tea" },
  { name: "Matcha Latte",            primary: "matcha_powder" },
  { name: "Matcha Milk Tea",         primary: "matcha_powder" },
  { name: "Brown Sugar Pearl Milk",  primary: "tapioca_pearls" },
  { name: "Taro Milk Tea",           primary: "tapioca_pearls" },
  { name: "Thai Milk Tea",           primary: "tapioca_pearls" },
  { name: "Caramel Milk Tea",        primary: "tapioca_pearls" },
];

const TRACKED = ["tapioca_pearls", "black_tea", "jasmine_tea", "oolong_tea", "matcha_powder"];

// ── Utilities ──────────────────────────────────────────────────────────────

const fmtG = (g: number) => g >= 1000 ? `${(g / 1000).toFixed(1)} kg` : `${Math.round(g)} g`;
const fmtId = (id: string) => id.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

function fmtExpiry(iso: string | null): { text: string; urgentPct: number; color: string } {
  if (!iso) return { text: "—", urgentPct: 0, color: "#9ca3af" };
  const diff = new Date(iso).getTime() - Date.now();
  if (diff <= 0) return { text: "Expired", urgentPct: 100, color: "#b52235" };
  const mins = Math.floor(diff / 60_000);
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  const text = h > 0 ? `${h}h ${m}m` : `${mins}m`;
  const urgentPct = Math.max(0, 100 - (diff / (240 * 60_000)) * 100); // 240-min shelf life
  const color = mins < 30 ? "#b52235" : mins < 60 ? "#d97706" : "#16a34a";
  return { text, urgentPct, color };
}

// ── Inline feedback toast ──────────────────────────────────────────────────

type ToastKind = "ok" | "err";
interface Toast { msg: string; kind: ToastKind; }

const ToastBubble: React.FC<{ toast: Toast | null }> = ({ toast }) => {
  if (!toast) return null;
  return (
    <div style={{
      padding: "7px 12px", borderRadius: 8, fontSize: 12, fontWeight: 600,
      backgroundColor: toast.kind === "ok" ? "#dcfce7" : "#fde8eb",
      color: toast.kind === "ok" ? "#16a34a" : "#b52235",
      border: `1px solid ${toast.kind === "ok" ? "#86efac" : "#fca5a5"}`,
      marginTop: 8,
    }}>
      {toast.msg}
    </div>
  );
};

// ── Batch row ──────────────────────────────────────────────────────────────

const BatchRow: React.FC<{
  batch: PreparedBatch;
  onComplete: (batchId: string, ingredientId: string) => Promise<void>;
  onWaste: (batchId: string, ingredientId: string, qty: number) => Promise<void>;
}> = ({ batch, onComplete, onWaste }) => {
  const { text, urgentPct, color } = fmtExpiry(batch.expires_at);
  const isBrewing = !batch.completed_at;
  const [wasteOpen, setWasteOpen] = useState(false);
  const [wasteVal, setWasteVal] = useState("");
  const [busy, setBusy] = useState(false);

  const handleComplete = async () => {
    setBusy(true);
    await onComplete(batch.batch_id, batch.ingredient_id);
    setBusy(false);
  };

  const handleWaste = async () => {
    const qty = parseFloat(wasteVal);
    if (isNaN(qty) || qty <= 0) return;
    setBusy(true);
    await onWaste(batch.batch_id, batch.ingredient_id, qty);
    setBusy(false);
    setWasteOpen(false);
    setWasteVal("");
  };

  return (
    <div style={{
      borderRadius: 10, padding: "12px 14px", marginBottom: 8,
      backgroundColor: isBrewing ? "#fff7ed" : (urgentPct > 70 ? "#fff5f5" : "#f9fafb"),
      border: `1.5px solid ${isBrewing ? "#fed7aa" : urgentPct > 70 ? "#fca5a5" : "#e5e7eb"}`,
    }}>
      {/* Row header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div>
          <span style={{ fontSize: 11, fontFamily: "monospace", color: "#6b7280" }}>
            #{batch.batch_id.slice(0, 8)}
          </span>
          {isBrewing && (
            <span style={{
              marginLeft: 8, backgroundColor: "#fed7aa", color: "#c2410c",
              borderRadius: 4, padding: "1px 6px", fontSize: 10, fontWeight: 700,
            }}>
              BREWING
            </span>
          )}
        </div>
        <span style={{ fontSize: 12, fontWeight: 700, color }}>
          {isBrewing ? "Not ready yet" : `Expires in ${text}`}
        </span>
      </div>

      {/* Quantities */}
      <div style={{ display: "flex", gap: 16, fontSize: 12, color: "#4b5563", marginBottom: 8 }}>
        <span>
          Remaining: <strong style={{ color: "#111827", fontSize: 13 }}>{fmtG(batch.remaining_qty)}</strong>
        </span>
        <span>Cooked: {fmtG(batch.initial_qty)}</span>
      </div>

      {/* Expiry bar (only for active batches) */}
      {!isBrewing && (
        <div style={{ backgroundColor: "#e5e7eb", borderRadius: 99, height: 4, marginBottom: 8 }}>
          <div style={{
            width: `${urgentPct}%`, height: "100%", borderRadius: 99,
            backgroundColor: color, transition: "width 60s linear",
          }} />
        </div>
      )}

      {/* Actions */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {isBrewing && (
          <button onClick={handleComplete} disabled={busy} style={{
            display: "flex", alignItems: "center", gap: 5,
            backgroundColor: "#16a34a", color: "#fff",
            border: "none", borderRadius: 7, padding: "6px 12px",
            fontSize: 12, fontWeight: 700, cursor: busy ? "not-allowed" : "pointer",
          }}>
            <CheckCircle size={13} /> Mark Ready
          </button>
        )}
        <button onClick={() => setWasteOpen(o => !o)} style={{
          display: "flex", alignItems: "center", gap: 5,
          backgroundColor: "#fef2f2", color: "#b52235",
          border: "1px solid #fca5a5", borderRadius: 7, padding: "6px 12px",
          fontSize: 12, fontWeight: 600, cursor: "pointer",
        }}>
          <Trash2 size={13} /> Log Waste
        </button>
      </div>

      {/* Waste input */}
      {wasteOpen && (
        <div style={{
          marginTop: 8, display: "flex", gap: 8, alignItems: "center",
          backgroundColor: "#fef2f2", borderRadius: 8, padding: "8px 10px",
          border: "1px solid #fca5a5",
        }}>
          <input
            type="number" min="1" placeholder="Grams to discard"
            value={wasteVal} onChange={e => setWasteVal(e.target.value)}
            style={{
              flex: 1, padding: "5px 8px", borderRadius: 6,
              border: "1px solid #fca5a5", fontSize: 12, outline: "none",
            }}
          />
          <button onClick={handleWaste} disabled={busy} style={{
            backgroundColor: "#b52235", color: "#fff", border: "none",
            borderRadius: 6, padding: "5px 12px", fontSize: 12, fontWeight: 700, cursor: "pointer",
          }}>
            Discard
          </button>
          <button onClick={() => setWasteOpen(false)} style={{
            backgroundColor: "transparent", border: "none",
            color: "#9ca3af", cursor: "pointer", fontSize: 14,
          }}>
            x
          </button>
        </div>
      )}
    </div>
  );
};

// ── Cook Form ──────────────────────────────────────────────────────────────
// Staff enters the amount they cooked and logs it as a new batch.

const CookForm: React.FC<{
  ingredientId: string;
  onDone: () => void;
}> = ({ ingredientId, onDone }) => {
  const defaultQty = DEFAULT_BATCH[ingredientId] ?? 1000;
  const [qty, setQty] = useState(String(defaultQty));
  const [cooking, setCooking] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);

  const handleCook = async () => {
    const amount = parseFloat(qty);
    if (isNaN(amount) || amount <= 0) {
      setToast({ msg: "Enter a valid amount in grams.", kind: "err" });
      return;
    }
    setCooking(true);
    setToast(null);
    try {
      // Step 1 — start brew (creates batch in BREWING state)
      const startRes = await fetch(`${API}/api/v1/inventory/brew/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shop_id: SHOP, ingredient_id: ingredientId, initial_qty_grams: amount }),
      });
      if (!startRes.ok) throw new Error(await startRes.text());
      const startData = await startRes.json();

      // Step 2 — immediately mark as complete so stock is usable now
      // (In a real shop you'd click "Mark Ready" after the actual cook time)
      const completeRes = await fetch(`${API}/api/v1/inventory/brew/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shop_id: SHOP, ingredient_id: ingredientId, batch_id: startData.batch_id }),
      });
      if (!completeRes.ok) throw new Error(await completeRes.text());

      setToast({ msg: `${fmtG(amount)} of ${fmtId(ingredientId)} added to active stock.`, kind: "ok" });
      setTimeout(() => { setToast(null); onDone(); }, 1500);
    } catch (e) {
      setToast({ msg: e instanceof Error ? e.message : "Request failed", kind: "err" });
    } finally {
      setCooking(false);
    }
  };

  return (
    <div style={{
      backgroundColor: "#f0fdf4", border: "1.5px solid #86efac",
      borderRadius: 10, padding: "14px 16px", marginTop: 12,
    }}>
      <p style={{ fontSize: 13, fontWeight: 700, color: "#15803d", margin: "0 0 10px" }}>
        Log Cooked Batch — {fmtId(ingredientId)}
      </p>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, flex: 1, minWidth: 180 }}>
          <input
            type="number" min="1" step="100"
            value={qty} onChange={e => setQty(e.target.value)}
            style={{
              flex: 1, padding: "8px 12px", borderRadius: 8,
              border: "1.5px solid #86efac", fontSize: 14, fontWeight: 600,
              outline: "none", color: "#111827",
            }}
          />
          <span style={{ fontSize: 13, color: "#6b7280", whiteSpace: "nowrap" }}>grams</span>
        </div>
        <button onClick={handleCook} disabled={cooking} style={{
          display: "flex", alignItems: "center", gap: 6,
          backgroundColor: cooking ? "#86efac" : "#16a34a",
          color: "#fff", border: "none", borderRadius: 8,
          padding: "9px 18px", fontWeight: 700, fontSize: 13,
          cursor: cooking ? "not-allowed" : "pointer", minHeight: 44, whiteSpace: "nowrap",
        }}>
          <Plus size={15} />
          {cooking ? "Saving…" : "Add to Stock"}
        </button>
        <button onClick={onDone} style={{
          backgroundColor: "transparent", border: "none",
          color: "#9ca3af", cursor: "pointer", fontSize: 14, padding: "9px 8px",
        }}>
          Cancel
        </button>
      </div>
      <p style={{ fontSize: 11, color: "#6b7280", margin: "8px 0 0" }}>
        Default batch size: {fmtG(defaultQty)}. Adjust if you cooked a different amount.
      </p>
      <ToastBubble toast={toast} />
    </div>
  );
};

// ── Sell Form ──────────────────────────────────────────────────────────────
// Staff logs a customer order — deducts stock via POS webhook → DecompoAgent.

const SellForm: React.FC<{ onDone: () => void }> = ({ onDone }) => {
  const [drink, setDrink] = useState(DRINKS[0].name);
  const [size, setSize] = useState<"S" | "M" | "L">("M");
  const [qty, setQty] = useState("1");
  const [extraPearls, setExtraPearls] = useState(false);
  const [selling, setSelling] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);

  const handleSell = async () => {
    const amount = parseInt(qty, 10);
    if (isNaN(amount) || amount < 1) {
      setToast({ msg: "Enter a valid quantity (1 or more).", kind: "err" });
      return;
    }
    setSelling(true);
    setToast(null);
    try {
      const res = await fetch(`${API}/api/v1/pos/webhook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transaction_id: `manual-${Date.now()}`,
          shop_id: SHOP,
          timestamp: new Date().toISOString(),
          items: [{
            name: drink,
            quantity: amount,
            size,
            ice_level: "normal ice",
            modifiers: extraPearls ? ["extra pearls"] : [],
          }],
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const summary = (data.deductions ?? [])
        .map((d: { ingredient_id: string; qty_grams_ml: number }) =>
          `${fmtId(d.ingredient_id)}: -${fmtG(d.qty_grams_ml)}`)
        .join("  |  ");
      setToast({ msg: `Sold ${amount}x ${drink} (${size}).  ${summary}`, kind: "ok" });
      setTimeout(() => { setToast(null); onDone(); }, 2000);
    } catch (e) {
      setToast({ msg: e instanceof Error ? e.message : "Request failed", kind: "err" });
    } finally {
      setSelling(false);
    }
  };

  return (
    <div style={{
      backgroundColor: "#fff7ed", border: "1.5px solid #fed7aa",
      borderRadius: 10, padding: "14px 16px", marginTop: 12,
    }}>
      <p style={{ fontSize: 13, fontWeight: 700, color: "#c2410c", margin: "0 0 12px" }}>
        Log Customer Order
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {/* Drink selector */}
        <div>
          <label style={{ fontSize: 11, fontWeight: 600, color: "#6b7280", display: "block", marginBottom: 4 }}>
            DRINK
          </label>
          <select value={drink} onChange={e => setDrink(e.target.value)} style={{
            width: "100%", padding: "8px 10px", borderRadius: 8,
            border: "1.5px solid #fed7aa", fontSize: 13, color: "#111827",
            backgroundColor: "#fff", cursor: "pointer", outline: "none",
          }}>
            {DRINKS.map(d => (
              <option key={d.name} value={d.name}>{d.name}</option>
            ))}
          </select>
        </div>

        {/* Size + Qty row */}
        <div style={{ display: "flex", gap: 10 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: "#6b7280", display: "block", marginBottom: 4 }}>
              SIZE
            </label>
            <div style={{ display: "flex", gap: 6 }}>
              {(["S", "M", "L"] as const).map(s => (
                <button key={s} onClick={() => setSize(s)} style={{
                  flex: 1, padding: "7px 0", borderRadius: 7,
                  border: `1.5px solid ${size === s ? "#f97316" : "#e5e7eb"}`,
                  backgroundColor: size === s ? "#fff7ed" : "#fff",
                  color: size === s ? "#c2410c" : "#6b7280",
                  fontWeight: size === s ? 700 : 500, fontSize: 13, cursor: "pointer",
                }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: "#6b7280", display: "block", marginBottom: 4 }}>
              QTY
            </label>
            <input
              type="number" min="1" value={qty} onChange={e => setQty(e.target.value)}
              style={{
                width: "100%", padding: "8px 10px", borderRadius: 8,
                border: "1.5px solid #fed7aa", fontSize: 14, fontWeight: 700,
                outline: "none", color: "#111827", boxSizing: "border-box",
              }}
            />
          </div>
        </div>

        {/* Extra pearls toggle */}
        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
          <input
            type="checkbox" checked={extraPearls}
            onChange={e => setExtraPearls(e.target.checked)}
            style={{ width: 16, height: 16, cursor: "pointer" }}
          />
          <span style={{ fontSize: 13, color: "#374151" }}>Extra pearls (+50% pearl deduction)</span>
        </label>

        {/* Submit row */}
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={handleSell} disabled={selling} style={{
            display: "flex", alignItems: "center", gap: 6,
            backgroundColor: selling ? "#fdba74" : "#ea580c",
            color: "#fff", border: "none", borderRadius: 8,
            padding: "10px 20px", fontWeight: 700, fontSize: 13,
            cursor: selling ? "not-allowed" : "pointer", minHeight: 44,
          }}>
            <ShoppingCart size={15} />
            {selling ? "Processing…" : "Log Sale"}
          </button>
          <button onClick={onDone} style={{
            backgroundColor: "transparent", border: "none",
            color: "#9ca3af", cursor: "pointer", fontSize: 13,
          }}>
            Cancel
          </button>
        </div>
      </div>

      <ToastBubble toast={toast} />
    </div>
  );
};

// ── Ingredient Card ────────────────────────────────────────────────────────

const IngredientCard: React.FC<{
  ingredient: InventoryIngredient;
  onRefresh: () => void;
}> = ({ ingredient, onRefresh }) => {
  const max = MAX_GRAMS[ingredient.ingredient_id] ?? 4000;
  const pct = Math.round((ingredient.total_remaining_grams / max) * 100);

  const [showCook,  setShowCook]  = useState(false);
  const [showSell,  setShowSell]  = useState(false);
  const [showCal,   setShowCal]   = useState(false);
  const [showBatch, setShowBatch] = useState(false);
  const [calVal,    setCalVal]    = useState("");
  const [calBusy,   setCalBusy]   = useState(false);
  const [calToast,  setCalToast]  = useState<Toast | null>(null);

  // Status color
  const statusColor = pct < 10 ? "#b52235" : pct < 30 ? "#d97706" : "#16a34a";
  const statusLabel = pct < 10 ? "Critical" : pct < 30 ? "Low" : "Healthy";

  const handleComplete = async (batchId: string, ingredientId: string) => {
    await fetch(`${API}/api/v1/inventory/brew/complete`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shop_id: SHOP, ingredient_id: ingredientId, batch_id: batchId }),
    });
    onRefresh();
  };

  const handleWaste = async (batchId: string, ingredientId: string, qty: number) => {
    await fetch(`${API}/api/v1/inventory/waste`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shop_id: SHOP, ingredient_id: ingredientId, batch_id: batchId, waste_qty_grams: qty }),
    });
    onRefresh();
  };

  const handleRecalibrate = async () => {
    const qty = parseFloat(calVal);
    if (isNaN(qty) || qty < 0) { setCalToast({ msg: "Enter a valid amount.", kind: "err" }); return; }
    setCalBusy(true);
    try {
      const res = await fetch(`${API}/api/v1/inventory/recalibrate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shop_id: SHOP, ingredient_id: ingredient.ingredient_id, actual_qty_grams: qty }),
      });
      if (!res.ok) throw new Error(await res.text());
      setCalToast({ msg: `Stock updated to ${fmtG(qty)}.`, kind: "ok" });
      setTimeout(() => { setCalToast(null); setShowCal(false); setCalVal(""); onRefresh(); }, 1500);
    } catch (e) {
      setCalToast({ msg: e instanceof Error ? e.message : "Failed", kind: "err" });
    } finally { setCalBusy(false); }
  };

  const afterAction = () => {
    setShowCook(false);
    setShowSell(false);
    onRefresh();
  };

  return (
    <div style={{
      backgroundColor: "#fff", borderRadius: 14,
      boxShadow: "0 2px 8px rgba(0,0,0,0.07)", border: "1px solid #f0f0f0",
      overflow: "hidden",
    }}>
      {/* Status bar at top */}
      <div style={{ height: 4, backgroundColor: statusColor, opacity: 0.7 }} />

      <div style={{ padding: 18 }}>
        {/* Header row */}
        <div style={{ display: "flex", gap: 14, alignItems: "flex-start", marginBottom: 16 }}>
          <CircularProgress value={pct} size={90} stroke={9}
            label={fmtG(ingredient.total_remaining_grams)} sublabel={`${pct}%`} />

          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 style={{ fontSize: 15, fontWeight: 800, color: "#111827", margin: "0 0 4px" }}>
              {fmtId(ingredient.ingredient_id)}
            </h3>

            {/* Status badge */}
            <span style={{
              display: "inline-block", backgroundColor: statusColor + "20",
              color: statusColor, borderRadius: 6, padding: "2px 8px",
              fontSize: 11, fontWeight: 700, marginBottom: 6,
            }}>
              {statusLabel}
            </span>

            <div style={{ fontSize: 12, color: "#6b7280", lineHeight: 1.6 }}>
              <div>{ingredient.active_batches.length} active batch{ingredient.active_batches.length !== 1 ? "es" : ""}</div>
              {ingredient.active_brewing_qty_grams > 0 && (
                <div style={{ color: "#0891b2", fontWeight: 600 }}>
                  Brewing: {fmtG(ingredient.active_brewing_qty_grams)}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
          <button
            onClick={() => { setShowCook(o => !o); setShowSell(false); setShowCal(false); }}
            style={{
              flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
              backgroundColor: showCook ? "#dcfce7" : "#f0fdf4",
              color: "#16a34a", border: "1.5px solid #86efac",
              borderRadius: 9, padding: "9px 0", fontWeight: 700, fontSize: 12,
              cursor: "pointer", minHeight: 40,
            }}>
            <Plus size={14} /> Cook / Brew
          </button>
          <button
            onClick={() => { setShowSell(o => !o); setShowCook(false); setShowCal(false); }}
            style={{
              flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
              backgroundColor: showSell ? "#fff7ed" : "#fff7ed",
              color: "#ea580c", border: "1.5px solid #fed7aa",
              borderRadius: 9, padding: "9px 0", fontWeight: 700, fontSize: 12,
              cursor: "pointer", minHeight: 40,
            }}>
            <ShoppingCart size={14} /> Sell
          </button>
          <button
            onClick={() => { setShowCal(o => !o); setShowCook(false); setShowSell(false); }}
            style={{
              display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
              backgroundColor: "#f0f9ff", color: "#0891b2",
              border: "1.5px solid #bae6fd",
              borderRadius: 9, padding: "9px 12px", fontWeight: 600, fontSize: 12,
              cursor: "pointer", minHeight: 40,
            }}>
            <Scale size={14} /> Adjust
          </button>
        </div>

        {/* Cook form */}
        {showCook && <CookForm ingredientId={ingredient.ingredient_id} onDone={afterAction} />}

        {/* Sell form */}
        {showSell && <SellForm onDone={afterAction} />}

        {/* Recalibrate (scale audit) form */}
        {showCal && (
          <div style={{
            backgroundColor: "#f0f9ff", border: "1.5px solid #bae6fd",
            borderRadius: 10, padding: "12px 14px", marginTop: 12,
          }}>
            <p style={{ fontSize: 12, fontWeight: 700, color: "#0369a1", margin: "0 0 8px" }}>
              Scale Audit — enter physical weight
            </p>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input
                type="number" min="0" placeholder="Grams on scale"
                value={calVal} onChange={e => setCalVal(e.target.value)}
                style={{
                  flex: 1, padding: "8px 10px", borderRadius: 8,
                  border: "1.5px solid #7dd3fc", fontSize: 13, outline: "none",
                }}
              />
              <span style={{ fontSize: 12, color: "#6b7280" }}>g</span>
              <button onClick={handleRecalibrate} disabled={calBusy} style={{
                backgroundColor: "#0891b2", color: "#fff", border: "none",
                borderRadius: 8, padding: "8px 16px", fontWeight: 700,
                fontSize: 12, cursor: "pointer",
              }}>
                {calBusy ? "…" : "Set"}
              </button>
              <button onClick={() => setShowCal(false)} style={{
                backgroundColor: "transparent", border: "none",
                color: "#9ca3af", cursor: "pointer", fontSize: 14,
              }}>
                x
              </button>
            </div>
            <ToastBubble toast={calToast} />
          </div>
        )}

        {/* FIFO batch stack — collapsible */}
        {ingredient.active_batches.length > 0 && (
          <div style={{ marginTop: 14 }}>
            <button onClick={() => setShowBatch(o => !o)} style={{
              display: "flex", alignItems: "center", gap: 6, width: "100%",
              backgroundColor: "transparent", border: "none", cursor: "pointer",
              padding: 0, marginBottom: showBatch ? 8 : 0,
            }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Batch Stack ({ingredient.active_batches.length})
              </span>
              {showBatch ? <ChevronUp size={13} color="#9ca3af" /> : <ChevronDown size={13} color="#9ca3af" />}
            </button>
            {showBatch && ingredient.active_batches.map(b => (
              <BatchRow
                key={b.batch_id} batch={b}
                onComplete={handleComplete}
                onWaste={handleWaste}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ── Main page ──────────────────────────────────────────────────────────────

export const InventoryPage: React.FC = () => {
  const { state, dispatch } = useDashboard();
  const [loading, setLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [showGlobalSell, setShowGlobalSell] = useState(false);

  const fetchInventory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/inventory/shop/${SHOP}`);
      if (!res.ok) return;
      const list: InventoryIngredient[] = await res.json();
      list.forEach(item => dispatch({ type: "UPSERT_INGREDIENT", payload: item }));
      setLastRefresh(new Date());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [dispatch]);

  useEffect(() => { fetchInventory(); }, [fetchInventory]);

  const ingredients = Object.values(state.ingredients);

  // Ensure all tracked ingredients appear even if empty
  const displayList: InventoryIngredient[] = TRACKED.map(id =>
    ingredients.find(i => i.ingredient_id === id) ?? {
      ingredient_id: id,
      total_remaining_grams: 0,
      active_brewing_qty_grams: 0,
      nearest_expiry: null,
      active_batches: [],
    }
  );

  return (
    <main style={{ flex: 1, overflowY: "auto", padding: 20, backgroundColor: "#f4f6f8" }}>

      {/* Page header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 800, color: "#111827", margin: 0 }}>
            Inventory Management
          </h1>
          <p style={{ fontSize: 13, color: "#9ca3af", margin: "4px 0 0" }}>
            Cook batches, log sales, manage stock levels
            {lastRefresh && ` — refreshed ${lastRefresh.toLocaleTimeString()}`}
          </p>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          {/* Quick sell button (global — any drink) */}
          <button onClick={() => setShowGlobalSell(o => !o)} style={{
            display: "flex", alignItems: "center", gap: 6,
            backgroundColor: showGlobalSell ? "#fff7ed" : "#fff",
            color: "#ea580c", border: "1.5px solid #fed7aa",
            borderRadius: 10, padding: "9px 16px", fontWeight: 700, fontSize: 13,
            cursor: "pointer", minHeight: 44,
          }}>
            <ShoppingCart size={15} /> Log Sale
          </button>

          <button onClick={fetchInventory} disabled={loading} style={{
            display: "flex", alignItems: "center", gap: 6,
            backgroundColor: "#1a6b5e", color: "#fff", border: "none",
            borderRadius: 10, padding: "9px 16px", fontWeight: 700, fontSize: 13,
            cursor: loading ? "not-allowed" : "pointer", minHeight: 44,
          }}>
            <RefreshCw size={14} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {/* Global sell form (shown when "Log Sale" is clicked from header) */}
      {showGlobalSell && (
        <div style={{ marginBottom: 20 }}>
          <SellForm onDone={() => { setShowGlobalSell(false); fetchInventory(); }} />
        </div>
      )}

      {/* Summary strip */}
      <div style={{
        display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap",
      }}>
        {[
          { label: "Total Active Stock", value: fmtG(displayList.reduce((s, i) => s + i.total_remaining_grams, 0)) },
          { label: "Ingredients", value: String(displayList.filter(i => i.total_remaining_grams > 0).length) + " / " + displayList.length },
          { label: "Currently Brewing", value: fmtG(displayList.reduce((s, i) => s + i.active_brewing_qty_grams, 0)) },
          { label: "Critical", value: String(displayList.filter(i => (i.total_remaining_grams / (MAX_GRAMS[i.ingredient_id] ?? 4000)) * 100 < 10).length) },
        ].map(({ label, value }) => (
          <div key={label} style={{
            flex: 1, minWidth: 130, backgroundColor: "#fff", borderRadius: 10,
            padding: "12px 16px", boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          }}>
            <p style={{ fontSize: 11, color: "#9ca3af", fontWeight: 600, margin: "0 0 3px", textTransform: "uppercase" }}>{label}</p>
            <p style={{ fontSize: 18, fontWeight: 800, color: "#111827", margin: 0 }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Ingredient grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
        gap: 16,
      }}>
        {displayList.map(ing => (
          <IngredientCard
            key={ing.ingredient_id}
            ingredient={ing}
            onRefresh={fetchInventory}
          />
        ))}
      </div>
    </main>
  );
};
