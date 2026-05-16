import { create } from 'zustand';
import type { AppStatus, QAMessage, Settings, AudioDevice, SystemInfo } from '../types';

interface AppStore {
  // Connection state
  status: AppStatus;
  setStatus: (status: AppStatus) => void;

  // Messages
  messages: QAMessage[];
  addQuestion: (id: string, question: string) => void;
  appendAnswer: (id: string, chunk: string) => void;
  completeAnswer: (id: string, fullAnswer: string) => void;
  clearMessages: () => void;

  // Transcript
  transcript: string;
  setTranscript: (text: string) => void;
  appendTranscript: (text: string) => void;

  // Devices
  devices: AudioDevice[];
  defaultDevice: AudioDevice | null;
  setDevices: (devices: AudioDevice[], defaultDevice: AudioDevice | null) => void;

  // System info
  systemInfo: SystemInfo | null;
  setSystemInfo: (info: SystemInfo) => void;

  // Settings
  settings: Settings;
  updateSettings: (partial: Partial<Settings>) => void;

  // UI state
  settingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;
  alwaysOnTop: boolean;
  setAlwaysOnTop: (value: boolean) => void;
  opacity: number;
  setOpacity: (value: number) => void;

  // Errors
  error: string | null;
  setError: (error: string | null) => void;
}

const defaultSettings: Settings = {
  audio: { device_index: null, sample_rate: 16000, use_microphone: false },
  stt: {
    model_size: 'small',
    language: 'auto',
    device: 'auto',
    compute_type: 'auto',
    cpu_threads: 4,
    vad_sensitivity: 0.4,
  },
  llm: {
    provider: 'ollama',
    openai_api_key: null,
    openai_model: 'gpt-4o',
    claude_api_key: null,
    claude_model: 'claude-sonnet-4-20250514',
    ollama_base_url: 'http://localhost:11434',
    ollama_model: 'llama3',
    temperature: 0.3,
    max_tokens: 2048,
  },
  language: 'en',
};

export const useAppStore = create<AppStore>((set) => ({
  // Connection
  status: 'connecting',
  setStatus: (status) => set({ status }),

  // Messages
  messages: [],
  addQuestion: (id, question) =>
    set((s) => ({
      messages: [
        ...s.messages,
        { id, question, answer: '', answerComplete: false, timestamp: Date.now() },
      ],
    })),
  appendAnswer: (id, chunk) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, answer: m.answer + chunk } : m
      ),
    })),
  completeAnswer: (id, fullAnswer) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, answer: fullAnswer, answerComplete: true } : m
      ),
    })),
  clearMessages: () => set({ messages: [] }),

  // Transcript
  transcript: '',
  setTranscript: (text) => set({ transcript: text }),
  appendTranscript: (text) => set((s) => ({ transcript: s.transcript + ' ' + text })),

  // Devices
  devices: [],
  defaultDevice: null,
  setDevices: (devices, defaultDevice) => set({ devices, defaultDevice }),

  // System info
  systemInfo: null,
  setSystemInfo: (info) => set({ systemInfo: info }),

  // Settings
  settings: defaultSettings,
  updateSettings: (partial) =>
    set((s) => ({
      settings: { ...s.settings, ...partial },
    })),

  // UI
  settingsOpen: false,
  setSettingsOpen: (open) => set({ settingsOpen: open }),
  alwaysOnTop: false,
  setAlwaysOnTop: (value) => set({ alwaysOnTop: value }),
  opacity: 1.0,
  setOpacity: (value) => set({ opacity: value }),

  // Errors
  error: null,
  setError: (error) => set({ error }),
}));
