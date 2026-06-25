/**
 * App — Root component.
 *
 * Wires together:
 *  • DashboardContext provider (global state)
 *  • useWebSocket hook (listens for backend events)
 *  • NavigationRail + TopBar layout shell
 *  • Page routing (state-driven, no router library needed at M8 scope)
 */

import React, { useReducer, useEffect, useState } from "react";
import { DashboardContext, dashboardReducer, initialState } from "./store/dashboardStore";
import { useWebSocket } from "./hooks/useWebSocket";
import { NavigationRail, type NavPage } from "./components/NavigationRail";
import { TopBar } from "./components/TopBar";
import { Dashboard } from "./components/Dashboard";
import { InventoryPage } from "./components/InventoryPage";
import { ForecastPage } from "./components/ForecastPage";
import { InsightsPage } from "./components/InsightsPage";
import { FeedbackPage } from "./components/FeedbackPage";
import type { InventoryUpdate, RecommendationAlert, WsMessage } from "./types";

// ── Shop configuration (env override possible) ────────────────────────────
const SHOP_ID = import.meta.env.VITE_SHOP_ID ?? "00000000-0000-0000-0000-000000000001";
const STORE_NAME = import.meta.env.VITE_STORE_NAME ?? "Downtown Store";
// Use relative URL in production, absolute URL for local development
const API_BASE_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.MODE === 'production' ? '' : 'http://localhost:8000');

// ── Placeholder pages (M9+ will fill these in) ────────────────────────────
const PlaceholderPage: React.FC<{ title: string }> = ({ title }) => (
  <main className="flex-1 flex items-center justify-center p-8">
    <div className="m3-card text-center max-w-sm w-full">
      <h2 className="text-lg font-semibold text-on-surface mb-1">{title}</h2>
      <p className="text-sm text-on-surface-muted">
        This page will be built in a future milestone.
      </p>
    </div>
  </main>
);

// ── WebSocket message consumer ─────────────────────────────────────────────
function WsMessageConsumer({
  lastMessage,
}: {
  lastMessage: WsMessage | null;
}) {
  const { dispatch } = React.useContext(DashboardContext);

  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.event_type === "inventory_update") {
      const update = lastMessage as InventoryUpdate;
      update.ingredients.forEach((ing) => {
        dispatch({ type: "UPSERT_INGREDIENT", payload: ing });
      });
    } else if (lastMessage.event_type === "recommendation_alert") {
      dispatch({
        type: "PUSH_ALERT",
        payload: lastMessage as RecommendationAlert,
      });
    }
  }, [lastMessage, dispatch]);

  return null;
}

// ── Root App ───────────────────────────────────────────────────────────────
export default function App() {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);
  const [activePage, setActivePage] = useState<NavPage>("dashboard");
  const [navCollapsed, setNavCollapsed] = useState(false);

  const { status, lastMessage } = useWebSocket(SHOP_ID);

  useEffect(() => {
    async function bootstrapInventory() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/inventory/shop/${SHOP_ID}`);
        if (!response.ok) return;
        const list = await response.json();
        if (!Array.isArray(list)) return;

        list.forEach((item: any) => {
          dispatch({ type: "UPSERT_INGREDIENT", payload: item });
        });
      } catch {
        // Ignore bootstrap failure; WebSocket may populate state later.
      }
    }

    bootstrapInventory();
  }, [dispatch]);

  // Sync WebSocket connection status into global store
  useEffect(() => {
    dispatch({ type: "SET_CONNECTION_STATUS", payload: status });
  }, [status]);

  const renderPage = () => {
    switch (activePage) {
      case "dashboard": return <Dashboard onNavigate={setActivePage} />;
      case "inventory": return <InventoryPage />;
      case "forecast":  return <ForecastPage />;
      case "insights":  return <InsightsPage />;
      case "alerts":    return <FeedbackPage />;
      case "reports":   return <FeedbackPage />;
      case "settings":  return <PlaceholderPage title="Settings" />;
    }
  };

  return (
    <DashboardContext.Provider value={{ state, dispatch }}>
      {/* Consume WS messages and route them to the store */}
      <WsMessageConsumer lastMessage={lastMessage} />

      {/* App shell */}
      <div className="flex h-screen overflow-hidden bg-surface font-sans">
        {/* Left navigation */}
        <NavigationRail
          activePage={activePage}
          onNavigate={setActivePage}
          collapsed={navCollapsed}
          onToggleCollapse={() => setNavCollapsed((c) => !c)}
        />

        {/* Main content area */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <TopBar
            storeName={STORE_NAME}
            connectionStatus={state.connectionStatus}
          />
          {renderPage()}
        </div>
      </div>
    </DashboardContext.Provider>
  );
}
