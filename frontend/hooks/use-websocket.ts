"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { getAccessToken } from "@/services/auth";
import type { QueueStatusRead } from "@/services/workflow";

export type WebSocketEvent = {
  event: string;
  timestamp: string;
  execution_id: string;
  workflow_id: string;
  data: Record<string, any>;
};

export function useWebsocket(onEventReceived?: (event: WebSocketEvent) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [queueMetrics, setQueueMetrics] = useState<QueueStatusRead | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectDelay = 10000; // Cap backoff delay at 10s

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;
    
    // Clean up existing socket before opening a new one
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const token = getAccessToken();
    if (!token) {
      console.warn("WebSocket connect aborted: No authentication access token available.");
      setIsConnected(false);
      setIsConnecting(false);
      return;
    }

    setIsConnecting(true);
    
    // Construct WebSocket URL from HTTP API base
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
    const wsBaseUrl = apiBase.replace(/^http/, "ws") + "/ws";
    const url = `${wsBaseUrl}?token=${encodeURIComponent(token)}`;

    try {
      const socket = new WebSocket(url);
      wsRef.current = socket;

      socket.onopen = () => {
        console.log("WebSocket connection established successfully.");
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0; // Reset reconnection counter
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as WebSocketEvent;
          
          // Capture and set real-time queue state broadcasts
          if (payload.event === "queue_updated") {
            setQueueMetrics(payload.data as QueueStatusRead);
          }
          
          // Forward event to callback subscriber
          if (onEventReceived) {
            onEventReceived(payload);
          }
        } catch (err) {
          console.error("Failed to parse incoming WebSocket frame:", err);
        }
      };

      socket.onclose = (event) => {
        setIsConnected(false);
        setIsConnecting(false);
        wsRef.current = null;
        
        // Don't reconnect on standard clean closures or explicit token closures
        if (event.code === 4001) {
          console.error("WebSocket closed: Authentication failed (Code 4001).");
          return;
        }

        console.log(`WebSocket connection closed (Code ${event.code}). Scheduling reconnect...`);
        scheduleReconnect();
      };

      socket.onerror = (error) => {
        console.error("WebSocket connection error occurred:", error);
        // Let onclose handle the reconnection logic
      };

    } catch (err) {
      console.error("Failed to initialize WebSocket client:", err);
      setIsConnecting(false);
      scheduleReconnect();
    }
  }, [onEventReceived]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), maxReconnectDelay);
    console.log(`Reconnecting to WebSocket server in ${(delay / 1000).toFixed(1)}s...`);
    
    reconnectAttemptsRef.current += 1;
    
    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  }, [connect]);

  // Handle auto-connection and teardown on mount/unmount
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    isConnecting,
    queueMetrics,
    reconnect: connect
  };
}
