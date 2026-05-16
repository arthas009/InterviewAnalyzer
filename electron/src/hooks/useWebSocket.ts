import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store/appStore';
import type { WSMessage } from '../types';

declare global {
  interface Window {
    electronAPI: {
      getBackendPort: () => Promise<number>;
      getDataDir: () => Promise<string>;
      setAlwaysOnTop: (value: boolean) => Promise<void>;
      setOpacity: (value: number) => Promise<void>;
      onToggleListening: (callback: () => void) => void;
    };
  }
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const portRef = useRef<number | null>(null);

  const {
    setStatus,
    addQuestion,
    appendAnswer,
    completeAnswer,
    appendTranscript,
    setTranscript,
    setDevices,
    setSystemInfo,
    setError,
    status,
  } = useAppStore();

  const connect = useCallback(async () => {
    try {
      if (!portRef.current) {
        portRef.current = await window.electronAPI.getBackendPort();
      }

      const ws = new WebSocket(`ws://127.0.0.1:${portRef.current}/ws`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setStatus('idle');
        // Request initial data
        send({ type: 'get_devices' });
        send({ type: 'get_system_info' });
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);
          handleMessage(msg);
        } catch (e) {
          console.error('Failed to parse WS message:', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setStatus('connecting');
        scheduleReconnect();
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        ws.close();
      };
    } catch (err) {
      console.error('Failed to connect:', err);
      scheduleReconnect();
    }
  }, [setStatus]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimer.current) return;
    reconnectTimer.current = setTimeout(() => {
      reconnectTimer.current = null;
      connect();
    }, 2000);
  }, [connect]);

  const handleMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'status':
        setStatus(msg.state as 'idle' | 'listening' | 'processing');
        break;

      case 'transcript':
        // For both partial and final, update the display for live updating
        setTranscript(msg.text as string);
        // For final transcripts, also add to permanent history
        if (!msg.is_partial) {
          appendTranscript(msg.text as string);
        }
        break;

      case 'question_detected':
        addQuestion(msg.question_id as string, msg.question as string);
        break;

      case 'answer_chunk':
        appendAnswer(msg.question_id as string, msg.chunk as string);
        break;

      case 'answer_complete':
        completeAnswer(msg.question_id as string, msg.full_answer as string);
        break;

      case 'devices':
        setDevices(
          msg.devices as [],
          msg.default as null
        );
        break;

      case 'system_info':
        setSystemInfo({
          gpu: msg.gpu as boolean,
          gpu_name: msg.gpu_name as string | null,
          cpu_threads: msg.cpu_threads as number,
        });
        break;

      case 'error':
        console.error('Backend error:', msg.message);
        setError(msg.message as string);
        break;

      case 'settings_updated':
        break;

      default:
        console.log('Unknown message type:', msg.type);
    }
  }, [setStatus, appendTranscript, addQuestion, appendAnswer, completeAnswer, setDevices, setSystemInfo, setError]);

  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const startListening = useCallback(() => {
    const settings = useAppStore.getState().settings;
    send({ type: 'start', settings });
  }, [send]);

  const stopListening = useCallback(() => {
    send({ type: 'stop' });
  }, [send]);

  const updateSettings = useCallback((settings: Record<string, unknown>) => {
    send({ type: 'update_settings', settings });
  }, [send]);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  // Listen for global shortcut
  useEffect(() => {
    window.electronAPI.onToggleListening(() => {
      const currentStatus = useAppStore.getState().status;
      if (currentStatus === 'listening') {
        stopListening();
      } else if (currentStatus === 'idle') {
        startListening();
      }
    });
  }, [startListening, stopListening]);

  return {
    send,
    startListening,
    stopListening,
    updateSettings,
    isConnected: status !== 'connecting',
  };
}
