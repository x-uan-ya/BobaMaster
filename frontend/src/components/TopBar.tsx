/**
 * TopBar — M3 Top App Bar.
 * Shows store name and WebSocket connection status chip.
 */

import React from "react";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import type { WsConnectionStatus } from "../types";

interface TopBarProps {
  storeName?: string;
  connectionStatus: WsConnectionStatus;
}

const STATUS_CONFIG: Record<
  WsConnectionStatus,
  { label: string; icon: React.ReactNode; classes: string }
> = {
  online: {
    label: "Online",
    icon: <Wifi size={14} />,
    classes: "bg-success-light text-success",
  },
  connecting: {
    label: "Connecting",
    icon: <Loader2 size={14} className="animate-spin" />,
    classes: "bg-warning-light text-warning",
  },
  offline: {
    label: "Offline",
    icon: <WifiOff size={14} />,
    classes: "bg-error-light text-error",
  },
};

export const TopBar: React.FC<TopBarProps> = ({
  storeName = "Downtown Store",
  connectionStatus,
}) => {
  const cfg = STATUS_CONFIG[connectionStatus];

  return (
    <header
      className="flex items-center justify-between
                 h-14 px-4 bg-white border-b border-gray-200
                 shadow-m3-1 z-20"
      role="banner"
    >
      {/* Left — logo text */}
      <div className="flex items-center gap-2">
        <span className="text-lg font-bold text-primary">🧋 BobaMaster</span>
        <span className="hidden sm:block text-on-surface-muted text-sm">
          — {storeName}
        </span>
      </div>

      {/* Right — WS status chip */}
      <div
        className={`status-chip ${cfg.classes}`}
        role="status"
        aria-live="polite"
        aria-label={`Connection status: ${cfg.label}`}
      >
        {cfg.icon}
        <span>{cfg.label}</span>
      </div>
    </header>
  );
};
