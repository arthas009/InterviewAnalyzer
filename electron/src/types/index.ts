export interface AudioDevice {
  index: number;
  name: string;
  channels: number;
  sample_rate: number;
  is_loopback: boolean;
}

export interface WhisperModel {
  id: string;
  name: string;
  size_mb: number;
  speed: string;
  accuracy: string;
}

export interface QAMessage {
  id: string;
  question: string;
  answer: string;
  answerComplete: boolean;
  timestamp: number;
}

export interface Settings {
  audio: {
    device_index: number | null;
    sample_rate: number;
    use_microphone: boolean;
  };
  stt: {
    model_size: string;
    language: string;
    device: string;
    compute_type: string;
    cpu_threads: number;
    vad_sensitivity: number;
  };
  llm: {
    provider: 'openai' | 'claude' | 'ollama';
    openai_api_key: string | null;
    openai_model: string;
    claude_api_key: string | null;
    claude_model: string;
    ollama_base_url: string;
    ollama_model: string;
    temperature: number;
    max_tokens: number;
  };
  language: string;
}

export interface SystemInfo {
  gpu: boolean;
  gpu_name: string | null;
  cpu_threads: number;
}

export type AppStatus = 'idle' | 'listening' | 'processing' | 'connecting';

export interface WSMessage {
  type: string;
  [key: string]: unknown;
}
