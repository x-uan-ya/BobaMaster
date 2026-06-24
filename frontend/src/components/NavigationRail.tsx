import React from "react";
import {
  LayoutDashboard, Package, TrendingUp, Lightbulb,
  Bell, BarChart2, Settings, ChevronLeft, ChevronRight,
} from "lucide-react";

export type NavPage =
  | "dashboard" | "inventory" | "forecast" | "insights"
  | "alerts" | "reports" | "settings";

const NAV_ITEMS = [
  { id: "dashboard" as NavPage, label: "Dashboard", icon: <LayoutDashboard size={20} /> },
  { id: "inventory" as NavPage, label: "Inventory",  icon: <Package size={20} /> },
  { id: "forecast"  as NavPage, label: "Forecast",   icon: <TrendingUp size={20} /> },
  { id: "insights"  as NavPage, label: "Insights",   icon: <Lightbulb size={20} /> },
  { id: "alerts"    as NavPage, label: "Alerts",     icon: <Bell size={20} /> },
  { id: "reports"   as NavPage, label: "Reports",    icon: <BarChart2 size={20} /> },
  { id: "settings"  as NavPage, label: "Settings",   icon: <Settings size={20} /> },
];

interface Props {
  activePage: NavPage;
  onNavigate: (page: NavPage) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const NavigationRail: React.FC<Props> = ({
  activePage, onNavigate, collapsed, onToggleCollapse,
}) => {
  const width = collapsed ? 64 : 220;

  return (
    <nav
      className={`
        flex flex-col h-full bg-white border-r-2 border-surface-variant
        transition-all duration-300 shadow-m3-2 z-10
        ${collapsed ? "w-20" : "w-64"}
      `}
      aria-label="Main navigation"
      style={{
        width,
        minWidth: width,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#ffffff",
        borderRight: "1px solid #e5e7eb",
        boxShadow: "2px 0 4px rgba(0,0,0,0.05)",
        transition: "width 0.2s ease",
        overflow: "hidden",
        zIndex: 10,
      }}
    >
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: collapsed ? "center" : "space-between",
        padding: "12px 10px",
        borderBottom: "1px solid #f0f0f0",
        minHeight: 56,
      }}>
        {!collapsed && (
          <span style={{ fontWeight: 700, color: "#1a6b5e", fontSize: 15, whiteSpace: "nowrap" }}>
            🧋 BobaFlow
          </span>
        )}
        <button
          onClick={onToggleCollapse}
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: 36, height: 36, borderRadius: 8, border: "none",
            background: "transparent", cursor: "pointer", color: "#6b7280",
            flexShrink: 0,
          }}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Nav items */}
      <ul style={{ flex: 1, padding: "8px 6px", margin: 0, listStyle: "none", overflowY: "auto" }}>
        {NAV_ITEMS.map((item) => {
          const active = activePage === item.id;
          return (
            <li key={item.id} style={{ marginBottom: 2 }}>
              <button
                onClick={() => onNavigate(item.id)}
                aria-current={active ? "page" : undefined}
                title={collapsed ? item.label : undefined}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 10px",
                  borderRadius: 10,
                  border: "none",
                  cursor: "pointer",
                  backgroundColor: active ? "#d0f0eb" : "transparent",
                  color: active ? "#1a6b5e" : "#4b5563",
                  fontWeight: active ? 700 : 500,
                  fontSize: 13,
                  textAlign: "left",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  transition: "background 0.15s",
                  minHeight: 44,
                }}
                onMouseEnter={(e) => {
                  if (!active) (e.currentTarget as HTMLButtonElement).style.backgroundColor = "#f3f4f6";
                }}
                onMouseLeave={(e) => {
                  if (!active) (e.currentTarget as HTMLButtonElement).style.backgroundColor = "transparent";
                }}
              >
                <span style={{ flexShrink: 0 }}>{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
