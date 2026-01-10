'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export interface ProgressUpdate {
  type: string;
  progress: number;
  message: string;
  data?: Record<string, any>;
}

export type ProgressStatus =
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'processing'
  | 'review_pending'
  | 'completed'
  | 'error'
  | 'disconnected';

export interface UseProgressOptions {
  onComplete?: () => void;
  onError?: (error: string) => void;
  onReviewPending?: () => void;
}

export function useProgress(meetingId: string | null, options: UseProgressOptions = {}) {
  const [status, setStatus] = useState<ProgressStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [updates, setUpdates] = useState<ProgressUpdate[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;

  const connect = useCallback(() => {
    if (!meetingId || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL ||
      (typeof window !== 'undefined'
        ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
        : 'ws://localhost:8000');

    const fullUrl = `${wsUrl}/api/v1/ws/meetings/${meetingId}/progress`;

    setStatus('connecting');
    const ws = new WebSocket(fullUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data: ProgressUpdate = JSON.parse(event.data);

        // Skip ping messages
        if (data.type === 'ping') {
          ws.send('pong');
          return;
        }

        // Update state based on message type
        setUpdates(prev => [...prev, data]);

        if (data.progress !== undefined) {
          setProgress(data.progress);
        }

        if (data.message) {
          setMessage(data.message);
        }

        // Handle specific message types
        switch (data.type) {
          case 'connected':
            setStatus('connected');
            break;
          case 'stt_start':
          case 'stt_progress':
          case 'summarize_start':
          case 'actions_start':
          case 'critique_start':
            setStatus('processing');
            break;
          case 'review_pending':
            setStatus('review_pending');
            options.onReviewPending?.();
            break;
          case 'completed':
            setStatus('completed');
            options.onComplete?.();
            break;
          case 'error':
            setStatus('error');
            options.onError?.(data.data?.error || data.message);
            break;
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      wsRef.current = null;

      // Only reconnect if not intentionally closed
      if (status !== 'completed' && status !== 'error') {
        setStatus('disconnected');

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      }
    };
  }, [meetingId, status, options]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('idle');
  }, []);

  const reset = useCallback(() => {
    setProgress(0);
    setMessage('');
    setUpdates([]);
    setStatus('idle');
  }, []);

  // Auto-connect when meetingId is provided
  useEffect(() => {
    if (meetingId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [meetingId]);

  return {
    status,
    progress,
    message,
    updates,
    connect,
    disconnect,
    reset,
    isConnected: status === 'connected' || status === 'processing',
    isProcessing: status === 'processing',
  };
}

export default useProgress;
