/**
 * useWebSocket — Persistent WebSocket hook with auto-reconnect.
 *
 * Features
 * ────────
 * • Exponential back-off reconnection (1s → 2s → 4s … max 30s).
 * • Tracks connection status: "connecting" | "online" | "offline".
 * • Exposes the last received message as a strongly-typed WsMessage.
 * • Cleans up on unmount to prevent memory leaks.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import type { WsMessage, WsConnectionStatus } from "../types";

const WS_BASE_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
const MAX_RETRY_DELAY_MS = 30_000;
const BASE_RETRY_DELAY_MS = 1_000;

export function useWebSocket(shopId: string) {
  const [status, setStatus] = useState<WsConnectionStatus>("connecting");
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const retryDelayRef = useRef(BASE_RETRY_DELAY_MS);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const url = `${WS_BASE_URL}/ws/shop/${shopId}`;
    setStatus("connecting");

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setStatus("online");
      retryDelayRef.current = BASE_RETRY_DELAY_MS; // reset back-off on success
    };

    ws.onmessage = (event: MessageEvent) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(event.data as string) as WsMessage;
        setLastMessage(data);
      } catch {
        // Ignore malformed messages (e.g. pong frames)
      }
    };

    ws.onerror = () => {
      // Will be followed by onclose — handle reconnect there
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setStatus("offline");
      wsRef.current = null;

      // Schedule reconnect with exponential back-off
      retryTimeoutRef.current = setTimeout(() => {
        retryDelayRef.current = Math.min(
          retryDelayRef.current * 2,
          MAX_RETRY_DELAY_MS
        );
        connect();
      }, retryDelayRef.current);
    };
  }, [shopId]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { status, lastMessage };
}
