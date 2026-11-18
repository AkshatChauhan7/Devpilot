import { useEffect, useRef, useCallback, useState } from "react";
import { io, Socket } from "socket.io-client";
import { WebSocketMessage } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function useWebSocket(token: string | null) {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const listenersRef = useRef<Map<string, Set<(msg: WebSocketMessage) => void>>>(new Map());

  useEffect(() => {
    if (!token) return;

    socketRef.current = io(`${WS_URL}/ws`, {
      auth: { token },
      transports: ["websocket"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    const socket = socketRef.current;

    socket.on("connect", () => {
      setIsConnected(true);
    });

    socket.on("disconnect", () => {
      setIsConnected(false);
    });

    socket.on("message", (data: WebSocketMessage) => {
      setLastMessage(data);
      // Notify listeners
      const listeners = listenersRef.current.get(data.type);
      if (listeners) {
        listeners.forEach((callback) => callback(data));
      }
      // Also notify wildcard listeners
      const wildcardListeners = listenersRef.current.get("*");
      if (wildcardListeners) {
        wildcardListeners.forEach((callback) => callback(data));
      }
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [token]);

  const subscribe = useCallback((type: string, callback: (msg: WebSocketMessage) => void) => {
    if (!listenersRef.current.has(type)) {
      listenersRef.current.set(type, new Set());
    }
    listenersRef.current.get(type)!.add(callback);

    return () => {
      listenersRef.current.get(type)?.delete(callback);
    };
  }, []);

  const send = useCallback((data: object) => {
    socketRef.current?.emit("message", data);
  }, []);

  const ping = useCallback(() => {
    socketRef.current?.emit("message", { type: "ping" });
  }, []);

  return {
    isConnected,
    lastMessage,
    subscribe,
    send,
    ping,
  };
}

// Specific hooks for task and execution updates
export function useTaskUpdates(taskId: number, token: string | null) {
  const [updates, setUpdates] = useState<WebSocketMessage[]>([]);

  const { subscribe, isConnected } = useWebSocket(token);

  useEffect(() => {
    if (!taskId) return;

    const unsubscribe = subscribe("task_update", (msg) => {
      if (msg.task_id === taskId) {
        setUpdates((prev) => [...prev.slice(-49), msg]); // Keep last 50
      }
    });

    const unsubscribeState = subscribe("task_state", (msg) => {
      if (msg.task_id === taskId) {
        setUpdates((prev) => [...prev.slice(-49), msg]);
      }
    });

    return () => {
      unsubscribe();
      unsubscribeState();
    };
  }, [taskId, subscribe]);

  return { updates, isConnected };
}

export function useExecutionUpdates(executionId: number, token: string | null) {
  const [updates, setUpdates] = useState<WebSocketMessage[]>([]);

  const { subscribe, isConnected } = useWebSocket(token);

  useEffect(() => {
    if (!executionId) return;

    const unsubscribe = subscribe("execution_update", (msg) => {
      if (msg.execution_id === executionId) {
        setUpdates((prev) => [...prev.slice(-49), msg]);
      }
    });

    const unsubscribeState = subscribe("execution_state", (msg) => {
      if (msg.execution_id === executionId) {
        setUpdates((prev) => [...prev.slice(-49), msg]);
      }
    });

    return () => {
      unsubscribe();
      unsubscribeState();
    };
  }, [executionId, subscribe]);

  return { updates, isConnected };
}