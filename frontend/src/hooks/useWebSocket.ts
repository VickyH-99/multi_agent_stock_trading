/**
 * WebSocket hook for real-time stock updates.
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import type { Quote, WsMessage } from '@/types/api';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

interface UseWebSocketOptions {
  symbols: string[];
  onQuoteUpdate?: (symbol: string, quote: Quote) => void;
  onMarketPulse?: (status: string) => void;
  refreshInterval?: number;
  enabled?: boolean;
}

interface WebSocketState {
  connected: boolean;
  error: string | null;
  reconnectCount: number;
}

export function useStockWebSocket({
  symbols,
  onQuoteUpdate,
  onMarketPulse,
  refreshInterval = 10,
  enabled = true,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    error: null,
    reconnectCount: 0,
  });
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const symbolsRef = useRef<string[]>(symbols);

  useEffect(() => {
    symbolsRef.current = symbols;
  }, [symbols]);

  useEffect(() => {
    reconnectCountRef.current = state.reconnectCount;
  }, [state.reconnectCount]);

  const connect = useCallback(() => {
    if (!enabled || typeof window === 'undefined') return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectCountRef.current = 0;
        setState(s => ({ ...s, connected: true, error: null, reconnectCount: 0 }));
        // Subscribe to symbols
        if (symbolsRef.current.length > 0) {
          ws.send(JSON.stringify({
            action: 'subscribe',
            symbols: symbolsRef.current,
          }));
        }
        // Set refresh interval
        ws.send(JSON.stringify({
          action: 'set_interval',
          interval: refreshInterval,
        }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WsMessage;
          if (msg.type === 'quote' && onQuoteUpdate) {
            onQuoteUpdate(msg.symbol, msg.data);
          } else if (msg.type === 'market_pulse' && onMarketPulse) {
            onMarketPulse(msg.status);
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onerror = () => {
        setState(s => ({ ...s, error: 'WebSocket connection error' }));
      };

      ws.onclose = () => {
        setState(s => ({ ...s, connected: false }));
        // Reconnect with backoff
        if (enabled) {
          const nextCount = reconnectCountRef.current + 1;
          const delay = Math.min(30000, 2000 * nextCount);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectCountRef.current = nextCount;
            setState(s => ({ ...s, reconnectCount: nextCount }));
            connect();
          }, delay);
        }
      };
    } catch {
      setState(s => ({ ...s, error: 'Failed to create WebSocket' }));
    }
  }, [enabled, refreshInterval, onQuoteUpdate, onMarketPulse]);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => {
      reconnectTimeoutRef.current && clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  // Update subscriptions when symbols change
  useEffect(() => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN && symbols.length > 0) {
      ws.send(JSON.stringify({ action: 'subscribe', symbols }));
    }
  }, [symbols]);

  const setInterval = useCallback((interval: number) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'set_interval', interval }));
    }
  }, []);

  return { ...state, setInterval };
}
