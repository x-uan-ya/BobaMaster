/**
 * NavigationRail — Left-side M3 Navigation Rail.
 * Collapses to icon-only on smaller viewports.
 */

import React from "react";
import {
  LayoutDashboard,
  Package,
  TrendingUp,
  Lightbulb,
  Bell,
  BarChart2,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export type NavPage =
  | "dashboard"
  | "inventory"
  | "forecast"
  | "insights"
  | "alerts"
  | "reports"
  | "settings";

interface NavItem {
  id: NavPage;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { id: "dashboard",  label: "Dashboard",  icon: <LayoutDashboard size={22} /> },
  { id: "inventory",  label: "Inventory",  icon: <Package size={22} /> },
  { id: "forecast",   label: "Forecast",   icon: <TrendingUp size={22} /> },
  { id: "insights",   label: "Insights",   icon: <Lightbulb size={22} /> },
  { id: "alerts",     label: "Alerts",     icon: <Bell size={22} /> },
  { id: "reports",    label: "Reports",    icon: <BarChart2 size={22} /> },
  { id: "settings",   label: "Settings",   icon: <Settings size={22} /> },
];

interface NavigationRailProps {
  activePage: NavPage;
  onNavigate: (page: NavPage) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const NavigationRail: React.FC<NavigationRailProps> = ({
  activePage,
  onNavigate,
  collapsed,
  onToggleCollapse,
}) => {
  return (
    <nav
      className={`
        flex flex-col h-full bg-white border-r border-gray-200
        transition-all duration-200 shadow-m3-1 z-10
        ${collapsed ? "w-16" : "w-56"}
      `}
      aria-label="Main navigation"
    >
      {/* Logo / collapse toggle */}
      <div className="flex items-center justify-between px-3 py-4 border-b border-gray-100">
        {!collapsed && (
          <span className="font-bold text-primary text-sm tracking-wide truncate">
            BobaFlow
          </span>
        )}
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-m3-md hover:bg-surface-variant text-on-surface-muted
                     transition-colors min-h-0 min-w-0"
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Nav items */}
      <ul className="flex-1 py-2 space-y-1" role="list">
        {NAV_ITEMS.map((item) => {
          const isActive = activePage === item.id;
          return (
            <li key={item.id}>
              <button
                onClick={() => onNavigate(item.id)}
                className={`
                  w-full flex items-center gap-3 px-3 py-3 rounded-m3-md mx-1
                  text-sm font-medium transition-colors duration-150 min-h-0
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary
                  ${isActive
                    ? "bg-primary-light text-primary-dark"
                    : "text-on-surface-muted hover:bg-surface-variant hover:text-on-surface"
                  }
                `}
                aria-current={isActive ? "page" : undefined}
                title={collapsed ? item.label : undefined}
              >
                <span className="shrink-0">{item.icon}</span>
                {!collapsed && (
                  <span className="truncate">{item.label}</span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
