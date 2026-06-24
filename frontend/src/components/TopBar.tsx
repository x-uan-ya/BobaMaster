import React from "react";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import type { WsConnectionStatus } from "../types";

interface Props {
  storeName?: string;
  connectionStatus: WsConnectionStatus;
}

const STATUS: Record<WsConnectionStatus, { label: string; bg: string; color: string; icon: React.ReactNode }> = {
  online:     { label: "Online",     bg: "#dcfce7", color: "#16a34a", icon: <Wifi size={13} /> },
  connecting: { label: "Connecting", bg: "#fef3c7", color: "#d97706", icon: <Loader2 size={13} className="animate-spin" /> },
  offline:    { label: "Offline",    bg: "#fde8eb", color: "#b52235", icon: <WifiOff size={13} /> },
};

export const TopBar: React.FC<Props> = ({ storeName = "Downtown Store", connectionStatus }) => {
  const s = STATUS[connectionStatus];

  return (
    <header
      role="banner"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: 56,
        padding: "0 20px",
        backgroundColor: "#ffffff",
        borderBottom: "1px solid #e5e7eb",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        flexShrink: 0,
        zIndex: 20,
      }}
    >
      {/* Left */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 16, fontWeight: 700, color: "#1a6b5e" }}>BobaMaster Operations Hub</span>
        <span style={{ fontSize: 13, color: "#9ca3af" }}>— {storeName}</span>
      </div>

      {/* Right — connection status chip */}
      <div
        role="status"
        aria-live="polite"
        aria-label={`Connection: ${s.label}`}
        style={{
          display: "inline-flex", alignItems: "center", gap: 5,
          padding: "4px 12px", borderRadius: 999,
          backgroundColor: s.bg, color: s.color,
          fontSize: 12, fontWeight: 600,
        }}
      >
        {s.icon}
        {s.label}
      </div>
    </header>
  );
};
