import React, { useReducer, useEffect, useState } from "react";
import { DashboardContext, dashboardReducer, initialState } from "./store/dashboardStore";
import { useWebSocket } from "./hooks/useWebSocket";
import { NavigationRail, type NavPage } from "./components/NavigationRail";
import { TopBar } from "./components/TopBar";
import { Dashboard } from "./components/Dashboard";
import type { InventoryUpdate, RecommendationAlert, WsMessage } from "./types";

const SHOP_ID    = import.meta.env.VITE_SHOP_ID    ?? "00000000-0000-0000-0000-000000000001";
const STORE_NAME = import.meta.env.VITE_STORE_NAME ?? "Downtown Store";

const PlaceholderPage: React.FC<{ title: string }> = ({ title }) => (
  <main className="flex flex-1 items-center justify-center p-8">
    <div className="card text-center max-w-sm w-full">
      <p className="text-4xl mb-3">🚧</p>
      <h2 className="text-lg font-semibold text-gray-800 mb-1">{title}</h2>
      <p className="text-sm text-gray-500">Coming in a future milestone.</p>
    </div>
  </main>
);

function WsMessageConsumer({ lastMessage }: { lastMessage: WsMessage | null }) {
  const { dispatch } = React.useContext(DashboardContext);
  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.event_type === "inventory_update") {
      (lastMessage as InventoryUpdate).ingredients.forEach((ing) =>
        dispatch({ type: "UPSERT_INGREDIENT", payload: ing })
      );
    } else if (lastMessage.event_type === "recommendation_alert") {
      dispatch({ type: "PUSH_ALERT", payload: lastMessage as RecommendationAlert });
    }
  }, [lastMessage, dispatch]);
  return null;
}

export default function App() {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);
  const [activePage, setActivePage] = useState<NavPage>("dashboard");
  const [navCollapsed, setNavCollapsed] = useState(false);
  const { status, lastMessage } = useWebSocket(SHOP_ID);

  useEffect(() => {
    dispatch({ type: "SET_CONNECTION_STATUS", payload: status });
  }, [status]);

  const renderPage = () => {
    switch (activePage) {
      case "dashboard": return <Dashboard />;
      case "inventory": return <PlaceholderPage title="Inventory Ledger" />;
      case "forecast":  return <PlaceholderPage title="Demand Forecast" />;
      case "insights":  return <PlaceholderPage title="Insights & Logs" />;
      case "alerts":    return <PlaceholderPage title="Alert History" />;
      case "reports":   return <PlaceholderPage title="Reports" />;
      case "settings":  return <PlaceholderPage title="Settings" />;
    }
  };

  return (
    <DashboardContext.Provider value={{ state, dispatch }}>
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
