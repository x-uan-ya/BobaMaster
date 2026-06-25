/**
 * SettingsPage — Store configuration, agent thresholds, recipe viewer,
 * and system diagnostics.
 *
 * Sections
 * ────────
 *  1. Store Profile      — store name, shop ID, timezone (saved to localStorage)
 *  2. Agent Thresholds   — safety buffers and warn levels per ingredient
 *                          (saved to localStorage, read by AgentPanel on next run)
 *  3. Recipe Viewer      — reads recipes.json from the backend, shows BOM per drink
 *  4. System Status      — backend health, Redis mode, WebSocket connection
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  Save, RefreshCw, CheckCircle, AlertCircle,
  ChevronDown, ChevronUp, Loader2,
} from "lucide-react";
import { useDashboard } from "../store/dashboardStore";

const API  = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SHOP = import.meta.env.VITE_SHOP_ID  ?? "00000000-0000-0000-0000-000000000001";

const fmtId = (id: string) =>
  id.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

// ── Shared primitives ──────────────────────────────────────────────────────

type SaveState = "idle" | "saving" | "saved" | "error";

const SaveBtn: React.FC<{
  state: SaveState; onClick: () => void; label?: string;
}> = ({ state, onClick, label = "Save Changes" }) => {
  const map = {
    idle:   { bg: "#1a6b5e", label,                  icon: <Save size={14} /> },
    saving: { bg: "#6b7280", label: "Saving…",        icon: <Loader2 size={14} className="animate-spin" /> },
    saved:  { bg: "#16a34a", label: "Saved",          icon: <CheckCircle size={14} /> },
    error:  { bg: "#b52235", label: "Error — retry",  icon: <AlertCircle size={14} /> },
  }[state];

  return (
    <button onClick={onClick} disabled={state === "saving"} style={{
      display: "flex", alignItems: "center", gap: 6,
      backgroundColor: map.bg, color: "#fff", border: "none",
      borderRadius: 9, padding: "9px 18px", fontWeight: 700, fontSize: 13,
      cursor: state === "saving" ? "not-allowed" : "pointer", minHeight: 42,
    }}>
      {map.icon} {map.label}
    </button>
  );
};

const SectionCard: React.FC<{ title: string; subtitle?: string; children: React.ReactNode }> = ({
  title, subtitle, children,
}) => (
  <div style={{
    backgroundColor: "#fff", borderRadius: 14,
    boxShadow: "0 2px 8px rgba(0,0,0,0.07)", marginBottom: 20,
    overflow: "hidden",
  }}>
    <div style={{
      padding: "14px 20px", borderBottom: "1px solid #f0f0f0",
      backgroundColor: "#fafafa",
    }}>
      <h2 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: 0 }}>{title}</h2>
      {subtitle && <p style={{ fontSize: 12, color: "#9ca3af", margin: "3px 0 0" }}>{subtitle}</p>}
    </div>
    <div style={{ padding: "18px 20px" }}>{children}</div>
  </div>
);

const Field: React.FC<{
  label: string; hint?: string;
  children: React.ReactNode;
}> = ({ label, hint, children }) => (
  <div style={{ marginBottom: 16 }}>
    <label style={{
      display: "block", fontSize: 12, fontWeight: 700,
      color: "#374151", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.04em",
    }}>
      {label}
    </label>
    {children}
    {hint && <p style={{ fontSize: 11, color: "#9ca3af", marginTop: 4 }}>{hint}</p>}
  </div>
);

const textInput = (
  value: string,
  onChange: (v: string) => void,
  placeholder = "",
  disabled = false,
): React.ReactNode => (
  <input
    type="text" value={value} placeholder={placeholder}
    onChange={e => onChange(e.target.value)} disabled={disabled}
    style={{
      width: "100%", padding: "9px 12px", borderRadius: 8,
      border: "1.5px solid #d1d5db", fontSize: 13, color: "#111827",
      backgroundColor: disabled ? "#f9fafb" : "#fff",
      outline: "none", boxSizing: "border-box",
    }}
  />
);

// ── 1. Store Profile ───────────────────────────────────────────────────────

const LS_PROFILE = "bm_store_profile";

interface Profile {
  storeName: string;
  ownerName: string;
  timezone: string;
  openTime: string;
  closeTime: string;
}

const DEFAULT_PROFILE: Profile = {
  storeName: import.meta.env.VITE_STORE_NAME ?? "Downtown Store",
  ownerName: "",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  openTime: "10:00",
  closeTime: "22:00",
};

const StoreProfileSection: React.FC = () => {
  const [profile, setProfile] = useState<Profile>(() => {
    try {
      const saved = localStorage.getItem(LS_PROFILE);
      return saved ? { ...DEFAULT_PROFILE, ...JSON.parse(saved) } : DEFAULT_PROFILE;
    } catch { return DEFAULT_PROFILE; }
  });
  const [saveState, setSaveState] = useState<SaveState>("idle");

  const set = (k: keyof Profile) => (v: string) =>
    setProfile(p => ({ ...p, [k]: v }));

  const save = () => {
    setSaveState("saving");
    try {
      localStorage.setItem(LS_PROFILE, JSON.stringify(profile));
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 2500);
    } catch {
      setSaveState("error");
    }
  };

  return (
    <SectionCard
      title="Store Profile"
      subtitle="Basic information about your store displayed in the top bar and reports"
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Field label="Store Name" hint="Shown in the top navigation bar">
          {textInput(profile.storeName, set("storeName"), "e.g. Downtown Hub")}
        </Field>
        <Field label="Owner / Manager Name">
          {textInput(profile.ownerName, set("ownerName"), "e.g. Sarah Tan")}
        </Field>
        <Field label="Time Zone">
          {textInput(profile.timezone, set("timezone"), "e.g. Asia/Singapore")}
        </Field>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <Field label="Open Time">
            <input type="time" value={profile.openTime}
              onChange={e => set("openTime")(e.target.value)}
              style={{ width: "100%", padding: "9px 10px", borderRadius: 8,
                border: "1.5px solid #d1d5db", fontSize: 13, outline: "none" }} />
          </Field>
          <Field label="Close Time">
            <input type="time" value={profile.closeTime}
              onChange={e => set("closeTime")(e.target.value)}
              style={{ width: "100%", padding: "9px 10px", borderRadius: 8,
                border: "1.5px solid #d1d5db", fontSize: 13, outline: "none" }} />
          </Field>
        </div>
        <Field label="Shop ID (read-only)" hint="Set via VITE_SHOP_ID environment variable">
          {textInput(SHOP, () => {}, "", true)}
        </Field>
        <Field label="Backend URL (read-only)" hint="Set via VITE_API_URL environment variable">
          {textInput(API, () => {}, "", true)}
        </Field>
      </div>
      <div style={{ marginTop: 8 }}>
        <SaveBtn state={saveState} onClick={save} />
      </div>
    </SectionCard>
  );
};

// ── 2. Agent Thresholds ────────────────────────────────────────────────────

const LS_THRESHOLDS = "bm_agent_thresholds";

interface IngredientThreshold {
  ingredient_id: string;
  cook_time_minutes: number;
  batch_size_grams: number;
  safety_buffer_grams: number;
  warn_buffer_grams: number;
}

const DEFAULT_THRESHOLDS: IngredientThreshold[] = [
  { ingredient_id: "tapioca_pearls", cook_time_minutes: 50, batch_size_grams: 2000, safety_buffer_grams: 200,  warn_buffer_grams: 600  },
  { ingredient_id: "black_tea",      cook_time_minutes: 15, batch_size_grams: 4000, safety_buffer_grams: 300,  warn_buffer_grams: 800  },
  { ingredient_id: "jasmine_tea",    cook_time_minutes: 15, batch_size_grams: 4000, safety_buffer_grams: 300,  warn_buffer_grams: 800  },
  { ingredient_id: "oolong_tea",     cook_time_minutes: 15, batch_size_grams: 4000, safety_buffer_grams: 300,  warn_buffer_grams: 800  },
  { ingredient_id: "matcha_powder",  cook_time_minutes: 10, batch_size_grams: 500,  safety_buffer_grams: 50,   warn_buffer_grams: 150  },
];

const AgentThresholdsSection: React.FC = () => {
  const [thresholds, setThresholds] = useState<IngredientThreshold[]>(() => {
    try {
      const saved = localStorage.getItem(LS_THRESHOLDS);
      return saved ? JSON.parse(saved) : DEFAULT_THRESHOLDS;
    } catch { return DEFAULT_THRESHOLDS; }
  });
  const [saveState, setSaveState] = useState<SaveState>("idle");

  const update = (id: string, field: keyof IngredientThreshold, value: number) =>
    setThresholds(ts => ts.map(t => t.ingredient_id === id ? { ...t, [field]: value } : t));

  const save = () => {
    setSaveState("saving");
    localStorage.setItem(LS_THRESHOLDS, JSON.stringify(thresholds));
    setSaveState("saved");
    setTimeout(() => setSaveState("idle"), 2500);
  };

  const reset = () => {
    setThresholds(DEFAULT_THRESHOLDS);
    localStorage.removeItem(LS_THRESHOLDS);
  };

  const cols: { key: keyof IngredientThreshold; label: string; unit: string }[] = [
    { key: "cook_time_minutes",   label: "Cook Time",    unit: "min" },
    { key: "batch_size_grams",    label: "Batch Size",   unit: "g"   },
    { key: "safety_buffer_grams", label: "Safety Floor", unit: "g"   },
    { key: "warn_buffer_grams",   label: "Warn Level",   unit: "g"   },
  ];

  return (
    <SectionCard
      title="Agent Decision Thresholds"
      subtitle="Controls when OpsDeciderAgent triggers BREW_NOW vs WARN vs WAIT alerts"
    >
      {/* Column headers */}
      <div style={{
        display: "grid", gridTemplateColumns: "160px 1fr 1fr 1fr 1fr",
        gap: 10, marginBottom: 10,
      }}>
        <div />
        {cols.map(c => (
          <div key={c.key} style={{ fontSize: 11, fontWeight: 700, color: "#9ca3af",
            textTransform: "uppercase", letterSpacing: "0.04em", textAlign: "center" }}>
            {c.label}
            <span style={{ display: "block", fontSize: 10, color: "#d1d5db" }}>{c.unit}</span>
          </div>
        ))}
      </div>

      {/* Rows */}
      {thresholds.map(t => (
        <div key={t.ingredient_id} style={{
          display: "grid", gridTemplateColumns: "160px 1fr 1fr 1fr 1fr",
          gap: 10, marginBottom: 10, alignItems: "center",
          padding: "10px 12px", borderRadius: 10,
          backgroundColor: "#f9fafb", border: "1px solid #f0f0f0",
        }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: "#111827" }}>
            {fmtId(t.ingredient_id)}
          </span>
          {cols.map(c => (
            <input
              key={c.key} type="number" min={0}
              value={t[c.key] as number}
              onChange={e => update(t.ingredient_id, c.key, Number(e.target.value))}
              style={{
                width: "100%", padding: "7px 10px", borderRadius: 7,
                border: "1.5px solid #d1d5db", fontSize: 13, fontWeight: 600,
                textAlign: "center", outline: "none", boxSizing: "border-box",
              }}
            />
          ))}
        </div>
      ))}

      <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
        <SaveBtn state={saveState} onClick={save} />
        <button onClick={reset} style={{
          backgroundColor: "transparent", color: "#9ca3af", border: "1px solid #d1d5db",
          borderRadius: 9, padding: "9px 16px", fontWeight: 600, fontSize: 13, cursor: "pointer",
        }}>
          Reset to Defaults
        </button>
      </div>

      <div style={{
        marginTop: 14, backgroundColor: "#fffbeb", borderRadius: 8, padding: "10px 14px",
        border: "1px solid #fde68a", fontSize: 12, color: "#92400e",
      }}>
        <strong>Note:</strong> These values are stored in your browser. To apply them to a live
        deployment, update <code>DEFAULT_INGREDIENT_CONFIGS</code> in{" "}
        <code>backend/app/agents/ops_decider_agent.py</code>.
      </div>
    </SectionCard>
  );
};

// ── 3. Recipe Viewer ───────────────────────────────────────────────────────

interface RecipeData {
  recipes: Record<string, Record<string, number>>;
  size_multipliers: Record<string, number>;
  ice_multipliers: Record<string, number>;
}

const RecipeViewerSection: React.FC = () => {
  const [data, setData] = useState<RecipeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      // Fetch from the static config served alongside the backend
      const res = await fetch(`${API}/api/v1/pos/recipes`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch {
      // Fall back to a fetch of the raw JSON file via backend static serving
      try {
        const res2 = await fetch(`${API}/static/recipes.json`);
        if (res2.ok) { setData(await res2.json()); return; }
      } catch { /* ignore */ }
      setError("Could not load recipes — backend may not expose this endpoint yet.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const recipes = data?.recipes ?? {};
  const filtered = Object.entries(recipes).filter(([name]) =>
    name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <SectionCard
      title="Recipe Matrix"
      subtitle="Bill of Materials for every drink — ingredient usage per M-size serving (grams/ml)"
    >
      <div style={{ display: "flex", gap: 10, marginBottom: 14, alignItems: "center" }}>
        <input
          type="text" placeholder="Search drinks…" value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            flex: 1, padding: "8px 12px", borderRadius: 8,
            border: "1.5px solid #d1d5db", fontSize: 13, outline: "none",
          }}
        />
        <button onClick={load} disabled={loading} style={{
          display: "flex", alignItems: "center", gap: 5,
          backgroundColor: "#1a6b5e", color: "#fff", border: "none",
          borderRadius: 8, padding: "8px 14px", fontWeight: 700, fontSize: 12,
          cursor: "pointer",
        }}>
          <RefreshCw size={13} /> {loading ? "Loading…" : "Reload"}
        </button>
      </div>

      {error && (
        <div style={{
          backgroundColor: "#fde8eb", color: "#b52235", borderRadius: 8,
          padding: "10px 14px", fontSize: 12, marginBottom: 12,
        }}>
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Size + ice multiplier badges */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
            {Object.entries(data.size_multipliers).map(([s, m]) => (
              <span key={s} style={{
                backgroundColor: "#f0fdf4", color: "#16a34a",
                border: "1px solid #86efac", borderRadius: 6,
                padding: "3px 10px", fontSize: 11, fontWeight: 700,
              }}>
                Size {s}: ×{m}
              </span>
            ))}
            {Object.entries(data.ice_multipliers).map(([s, m]) => (
              <span key={s} style={{
                backgroundColor: "#f0f9ff", color: "#0891b2",
                border: "1px solid #bae6fd", borderRadius: 6,
                padding: "3px 10px", fontSize: 11, fontWeight: 700,
              }}>
                {s}: ×{m}
              </span>
            ))}
          </div>

          <p style={{ fontSize: 12, color: "#9ca3af", marginBottom: 10 }}>
            {filtered.length} drink{filtered.length !== 1 ? "s" : ""} — click to expand BOM
          </p>

          {filtered.map(([name, bom]) => (
            <div key={name} style={{
              borderRadius: 10, border: "1px solid #e5e7eb",
              marginBottom: 6, overflow: "hidden",
            }}>
              <button
                onClick={() => setExpanded(expanded === name ? null : name)}
                style={{
                  width: "100%", display: "flex", alignItems: "center",
                  justifyContent: "space-between", padding: "10px 14px",
                  backgroundColor: expanded === name ? "#f0fdf4" : "#fff",
                  border: "none", cursor: "pointer", fontSize: 13,
                  fontWeight: 600, color: "#111827",
                }}
              >
                <span>{name}</span>
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 11, color: "#9ca3af" }}>
                    {Object.keys(bom).length} ingredient{Object.keys(bom).length !== 1 ? "s" : ""}
                  </span>
                  {expanded === name
                    ? <ChevronUp size={14} color="#9ca3af" />
                    : <ChevronDown size={14} color="#9ca3af" />
                  }
                </span>
              </button>

              {expanded === name && (
                <div style={{
                  padding: "10px 14px", backgroundColor: "#f9fafb",
                  borderTop: "1px solid #e5e7eb",
                  display: "flex", flexWrap: "wrap", gap: 8,
                }}>
                  {Object.entries(bom).map(([ing, qty]) => (
                    <div key={ing} style={{
                      backgroundColor: "#fff", border: "1px solid #e5e7eb",
                      borderRadius: 7, padding: "5px 10px",
                      fontSize: 12,
                    }}>
                      <span style={{ color: "#6b7280" }}>{fmtId(ing)}</span>
                      <span style={{ marginLeft: 6, fontWeight: 800, color: "#111827" }}>
                        {qty}g
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </>
      )}
    </SectionCard>
  );
};

// ── 4. System Status ───────────────────────────────────────────────────────

interface HealthData {
  status: string;
  service: string;
  redis_mode?: string;
  version?: string;
}

const SystemStatusSection: React.FC = () => {
  const { state } = useDashboard();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  const check = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/health`);
      if (res.ok) {
        setHealth(await res.json());
        setLastCheck(new Date());
      }
    } catch { setHealth(null); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { check(); }, [check]);


  const StatusRow: React.FC<{
    label: string; value: string; ok?: boolean; neutral?: boolean;
  }> = ({ label, value, ok, neutral }) => (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "9px 14px", borderRadius: 8, marginBottom: 6,
      backgroundColor: "#f9fafb", border: "1px solid #f0f0f0",
    }}>
      <span style={{ fontSize: 13, color: "#374151" }}>{label}</span>
      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          backgroundColor: neutral ? "#9ca3af" : ok ? "#16a34a" : "#b52235",
        }} />
        <span style={{ fontSize: 13, fontWeight: 700, color: "#111827" }}>{value}</span>
      </div>
    </div>
  );

  return (
    <SectionCard
      title="System Status"
      subtitle="Live diagnostics for backend services and agent connections"
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 12, color: "#9ca3af" }}>
          {lastCheck ? `Last checked: ${lastCheck.toLocaleTimeString()}` : "Not checked yet"}
        </span>
        <button onClick={check} disabled={loading} style={{
          display: "flex", alignItems: "center", gap: 5,
          backgroundColor: "#1a6b5e", color: "#fff", border: "none",
          borderRadius: 8, padding: "7px 14px", fontWeight: 700, fontSize: 12, cursor: "pointer",
        }}>
          <RefreshCw size={13} /> {loading ? "Checking…" : "Check Now"}
        </button>
      </div>

      <StatusRow
        label="Backend API"
        value={health ? `Online — ${health.service}` : "Offline / Unreachable"}
        ok={!!health}
      />
      <StatusRow
        label="WebSocket"
        value={state.connectionStatus.charAt(0).toUpperCase() + state.connectionStatus.slice(1)}
        ok={state.connectionStatus === "online"}
      />
      <StatusRow
        label="Redis / State Store"
        value={health?.redis_mode ?? "Unknown"}
        ok={health?.redis_mode === "redis"}
        neutral={health?.redis_mode === "in-memory"}
      />
      <StatusRow
        label="API Base URL"
        value={API}
        neutral
      />
      <StatusRow
        label="Shop ID"
        value={SHOP.slice(0, 18) + "…"}
        neutral
      />

      {health?.redis_mode === "in-memory" && (
        <div style={{
          marginTop: 10, backgroundColor: "#fffbeb", borderRadius: 8,
          padding: "10px 14px", border: "1px solid #fde68a",
          fontSize: 12, color: "#92400e",
        }}>
          <strong>In-memory mode:</strong> Redis is not running. Inventory state will reset
          when the backend restarts. Start Redis with:
          <code style={{
            display: "block", marginTop: 6, backgroundColor: "#fff7ed",
            padding: "5px 8px", borderRadius: 5, fontSize: 11,
          }}>
            cd docker && docker-compose up -d
          </code>
        </div>
      )}
    </SectionCard>
  );
};

// ── Main page ──────────────────────────────────────────────────────────────

export const SettingsPage: React.FC = () => (
  <main style={{ flex: 1, overflowY: "auto", padding: 20, backgroundColor: "#f4f6f8" }}>
    <div style={{ marginBottom: 24 }}>
      <h1 style={{ fontSize: 20, fontWeight: 800, color: "#111827", margin: 0 }}>
        Settings
      </h1>
      <p style={{ fontSize: 13, color: "#9ca3af", margin: "4px 0 0" }}>
        Store profile, agent parameters, recipe configuration, and system diagnostics
      </p>
    </div>

    <StoreProfileSection />
    <AgentThresholdsSection />
    <RecipeViewerSection />
    <SystemStatusSection />
  </main>
);
