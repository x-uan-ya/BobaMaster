/**
 * BusinessInsightsPage — Manager Dashboard with Real Business Intelligence
 *
 * Displays:
 *  - Revenue forecast (today's pace)
 *  - Peak demand windows (when to prep)
 *  - Top-selling drinks (what's popular)
 *  - Inventory optimization tips (what to cook)
 *  - Staff efficiency metrics
 *  - Waste trends and recommendations
 */

import React, { useState, useEffect } from "react";
import { TrendingUp, BarChart3, AlertTriangle, Zap, Leaf, Users } from "lucide-react";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const SHOP = import.meta.env.VITE_SHOP_ID ?? "00000000-0000-0000-0000-000000000001";

interface BusinessInsight {
  shop_id: string;
  generated_at: string;
  peak_windows: PeakWindow[];
  today_revenue_estimate: number;
  waste_percentage: number;
  top_drinks: DrinkInsight[];
  inventory_optimizations: InventoryOptimization[];
  staff_efficiency_score: number;
  demo_mode: boolean;
}

interface PeakWindow {
  start_hour: number;
  end_hour: number;
  avg_cups_per_minute: number;
  confidence: number;
}

interface DrinkInsight {
  drink_name: string;
  cups_sold_today: number;
  revenue_estimate: number;
  popularity_rank: number;
  trend: "trending_up" | "stable" | "trending_down";
}

interface InventoryOptimization {
  ingredient_id: string;
  current_level_grams: number;
  recommended_level_grams: number;
  reason: string;
  savings_potential: number;
}

const fmtCur = (n: number) => `$${n.toFixed(2)}`;
const fmtPct = (n: number) => `${(n * 100).toFixed(1)}%`;
const fmtId = (id: string) => id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

// ── Stat Card ──────────────────────────────────────────────────────────────

const StatCard: React.FC<{
  label: string;
  value: string | number;
  subtext?: string;
  icon: React.ReactNode;
  color: "green" | "blue" | "orange" | "red" | "purple";
}> = ({ label, value, subtext, icon, color }) => {
  const colorMap = {
    green: { bg: "#f0fdf4", border: "#86efac", icon: "#16a34a", text: "#15803d" },
    blue: { bg: "#f0f9ff", border: "#7dd3fc", icon: "#0891b2", text: "#0369a1" },
    orange: { bg: "#fff7ed", border: "#fdba74", icon: "#ea580c", text: "#c2410c" },
    red: { bg: "#fde8eb", border: "#fca5a5", icon: "#b52235", text: "#9f1239" },
    purple: { bg: "#f3e8ff", border: "#d8b4fe", icon: "#7c3aed", text: "#6d28d9" },
  }[color];

  return (
    <div
      style={{
        backgroundColor: colorMap.bg,
        borderLeft: `4px solid ${colorMap.border}`,
        borderRadius: 12,
        padding: 16,
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 8,
          backgroundColor: colorMap.border,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: colorMap.icon,
        }}
      >
        {icon}
      </div>
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 11, fontWeight: 600, color: "#6b7280", margin: "0 0 2px" }}>
          {label}
        </p>
        <p style={{ fontSize: 22, fontWeight: 800, color: colorMap.text, margin: 0 }}>
          {value}
        </p>
        {subtext && <p style={{ fontSize: 10, color: "#9ca3af", margin: "2px 0 0" }}>{subtext}</p>}
      </div>
    </div>
  );
};

// ── Peak Windows Chart ─────────────────────────────────────────────────────

const PeakWindowsChart: React.FC<{ windows: PeakWindow[] }> = ({ windows }) => {
  if (windows.length === 0)
    return (
      <div style={{ textAlign: "center", padding: 20, color: "#9ca3af" }}>
        No peak windows identified yet
      </div>
    );

  return (
    <div style={{ display: "flex", gap: 20, overflowX: "auto", padding: "16px 0" }}>
      {windows.map((w, i) => {
        const height = (w.avg_cups_per_minute / 15) * 150;
        return (
          <div key={i} style={{ textAlign: "center", minWidth: 80 }}>
            <div
              style={{
                width: 60,
                height: Math.max(20, height),
                backgroundColor: "#0891b2",
                borderRadius: "4px 4px 0 0",
                margin: "0 auto",
                opacity: 0.5 + w.confidence * 0.5,
                transition: "all 0.3s",
              }}
            />
            <p style={{ fontSize: 11, fontWeight: 700, color: "#1f2937", margin: "6px 0 0" }}>
              {w.start_hour}:00 - {w.end_hour}:00
            </p>
            <p style={{ fontSize: 10, color: "#6b7280", margin: "2px 0 0" }}>
              {w.avg_cups_per_minute.toFixed(1)}/min
            </p>
          </div>
        );
      })}
    </div>
  );
};

// ── Top Drinks ─────────────────────────────────────────────────────────────

const TopDrinksTable: React.FC<{ drinks: DrinkInsight[] }> = ({ drinks }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
    {drinks.map((d, i) => (
      <div
        key={i}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "12px 14px",
          backgroundColor: "#f9fafb",
          borderRadius: 10,
          border: "1px solid #e5e7eb",
        }}
      >
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            backgroundColor: "#0891b2",
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 13,
            fontWeight: 700,
          }}
        >
          {d.popularity_rank}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: 13, fontWeight: 700, color: "#111827", margin: 0 }}>
            {d.drink_name}
          </p>
          <p style={{ fontSize: 11, color: "#6b7280", margin: "2px 0 0" }}>
            {d.cups_sold_today} cups · {fmtCur(d.revenue_estimate)}
          </p>
        </div>
        <div style={{ textAlign: "right" }}>
          <span
            style={{
              display: "inline-block",
              backgroundColor:
                d.trend === "trending_up"
                  ? "#dcfce7"
                  : d.trend === "trending_down"
                    ? "#fde8eb"
                    : "#f3f4f6",
              color:
                d.trend === "trending_up"
                  ? "#16a34a"
                  : d.trend === "trending_down"
                    ? "#b52235"
                    : "#6b7280",
              borderRadius: 6,
              padding: "2px 8px",
              fontSize: 11,
              fontWeight: 700,
            }}
          >
            {d.trend === "trending_up" ? "↑ Up" : d.trend === "trending_down" ? "↓ Down" : "→ Stable"}
          </span>
        </div>
      </div>
    ))}
  </div>
);

// ── Inventory Optimization Tips ────────────────────────────────────────────

const OptimizationTips: React.FC<{ tips: InventoryOptimization[] }> = ({ tips }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
    {tips.map((t, i) => {
      const change = t.recommended_level_grams - t.current_level_grams;
      const isIncrease = change > 0;

      return (
        <div
          key={i}
          style={{
            padding: 14,
            backgroundColor: isIncrease ? "#fff7ed" : "#f0fdf4",
            border: `1px solid ${isIncrease ? "#fed7aa" : "#86efac"}`,
            borderRadius: 10,
          }}
        >
          <div style={{ display: "flex", alignItems: "start", gap: 10, marginBottom: 8 }}>
            {isIncrease ? (
              <AlertTriangle size={18} style={{ color: "#ea580c", flexShrink: 0, marginTop: 2 }} />
            ) : (
              <Leaf size={18} style={{ color: "#16a34a", flexShrink: 0, marginTop: 2 }} />
            )}
            <div>
              <p style={{ fontSize: 12, fontWeight: 700, color: "#1f2937", margin: 0 }}>
                {fmtId(t.ingredient_id)}
              </p>
              <p style={{ fontSize: 11, color: "#6b7280", margin: "2px 0 0" }}>{t.reason}</p>
            </div>
          </div>
          <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#6b7280" }}>
            <span>
              Current: <strong style={{ color: "#111827" }}>{Math.round(t.current_level_grams)}g</strong>
            </span>
            <span>
              Recommended: <strong style={{ color: "#111827" }}>{Math.round(t.recommended_level_grams)}g</strong>
            </span>
            {t.savings_potential > 0 && (
              <span style={{ color: "#16a34a", fontWeight: 600 }}>
                Save: {Math.round(t.savings_potential)}g/day
              </span>
            )}
          </div>
        </div>
      );
    })}
  </div>
);

// ── Main Component ─────────────────────────────────────────────────────────

export const BusinessInsightsPage: React.FC = () => {
  const [insights, setInsights] = useState<BusinessInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [revenue, setRevenue] = useState<any>(null);

  const fetchInsights = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/v1/business/insights/${SHOP}`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setInsights(data);

      // Also fetch revenue forecast
      const revRes = await fetch(`${API}/api/v1/business/revenue-forecast/${SHOP}`);
      if (revRes.ok) {
        setRevenue(await revRes.json());
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load insights");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
    const interval = setInterval(fetchInsights, 5 * 60 * 1000); // Refresh every 5 min
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <main style={{ flex: 1, overflowY: "auto", padding: 20, backgroundColor: "#f4f6f8" }}>
        <div
          style={{
            backgroundColor: "#fde8eb",
            border: "1.5px solid #fca5a5",
            borderRadius: 12,
            padding: "14px 16px",
            color: "#b52235",
          }}
        >
          {error}
        </div>
      </main>
    );
  }

  if (!insights) {
    return (
      <main style={{ flex: 1, overflowY: "auto", padding: 20, backgroundColor: "#f4f6f8" }}>
        <div style={{ textAlign: "center", padding: "48px 24px" }}>
          <div style={{ fontSize: 28, marginBottom: 12 }}>⏳</div>
          <p style={{ fontSize: 15, fontWeight: 700, color: "#374151" }}>Loading insights...</p>
        </div>
      </main>
    );
  }

  return (
    <main style={{ flex: 1, overflowY: "auto", padding: 20, backgroundColor: "#f4f6f8" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, color: "#111827", margin: 0 }}>
          Business Intelligence
        </h1>
        <p style={{ fontSize: 13, color: "#9ca3af", margin: "4px 0 0" }}>
          Real-time insights for operational decisions
          {insights.demo_mode && " (Demo data)"}
        </p>
      </div>

      {/* Key Metrics Row 1 */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 24 }}>
        <StatCard
          label="Today's Revenue"
          value={fmtCur(insights.today_revenue_estimate)}
          subtext={revenue ? `Projected: ${fmtCur(revenue.projected_total_revenue)}` : undefined}
          icon={<TrendingUp size={20} />}
          color="green"
        />
        <StatCard
          label="Waste Level"
          value={fmtPct(insights.waste_percentage)}
          subtext="12.3% is typical; <10% is excellent"
          icon={<Leaf size={20} />}
          color="orange"
        />
        <StatCard
          label="Staff Efficiency"
          value={`${insights.staff_efficiency_score.toFixed(0)}%`}
          subtext="Based on recommendation acceptance"
          icon={<Users size={20} />}
          color="blue"
        />
        <StatCard
          label="Optimization Score"
          value={`${(insights.inventory_optimizations.filter((o) => o.savings_potential > 0).length * 25).toFixed(0)}%`}
          subtext={`${insights.inventory_optimizations.filter((o) => o.savings_potential > 0).length} actions recommended`}
          icon={<Zap size={20} />}
          color="purple"
        />
      </div>

      {/* Two-column layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
        {/* Peak Windows */}
        <div
          style={{
            backgroundColor: "#fff",
            borderRadius: 14,
            padding: 18,
            boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
          }}
        >
          <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: "0 0 14px" }}>
            Peak Demand Windows
          </h3>
          <PeakWindowsChart windows={insights.peak_windows} />
          <p style={{ fontSize: 11, color: "#6b7280", margin: "12px 0 0", lineHeight: 1.5 }}>
            {insights.peak_windows.length > 0
              ? `Prepare extra stock before ${insights.peak_windows[0].start_hour}:00 to avoid stockouts.`
              : "No peak patterns identified yet."}
          </p>
        </div>

        {/* Top Drinks */}
        <div
          style={{
            backgroundColor: "#fff",
            borderRadius: 14,
            padding: 18,
            boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
          }}
        >
          <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: "0 0 14px" }}>
            Top-Selling Drinks Today
          </h3>
          <TopDrinksTable drinks={insights.top_drinks} />
        </div>
      </div>

      {/* Inventory Optimization */}
      <div
        style={{
          backgroundColor: "#fff",
          borderRadius: 14,
          padding: 18,
          boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
          marginBottom: 24,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
          <BarChart3 size={18} style={{ color: "#0891b2" }} />
          <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111827", margin: 0 }}>
            Inventory Optimization Recommendations
          </h3>
        </div>
        <OptimizationTips tips={insights.inventory_optimizations} />
      </div>

      {/* Refresh Button */}
      <div style={{ textAlign: "center" }}>
        <button
          onClick={fetchInsights}
          disabled={loading}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            backgroundColor: "#1a6b5e",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "10px 20px",
            fontWeight: 700,
            fontSize: 13,
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.7 : 1,
          }}
        >
          <TrendingUp size={14} />
          {loading ? "Refreshing..." : "Refresh Insights"}
        </button>
      </div>
    </main>
  );
};
