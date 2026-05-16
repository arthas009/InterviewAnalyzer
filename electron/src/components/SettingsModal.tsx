import { useState } from 'react';
import { useAppStore } from '../store/appStore';
import type { Settings } from '../types';

interface SettingsModalProps {
  onClose: () => void;
  onSave: (settings: Partial<Settings>) => void;
}

export function SettingsModal({ onClose, onSave }: SettingsModalProps) {
  const { settings, devices, systemInfo, alwaysOnTop, setAlwaysOnTop, opacity, setOpacity } = useAppStore();
  const [local, setLocal] = useState<Settings>(JSON.parse(JSON.stringify(settings)));

  const handleSave = () => {
    useAppStore.getState().updateSettings(local);
    onSave(local);
  };

  const updateLLM = (key: string, value: unknown) => {
    setLocal((prev) => ({
      ...prev,
      llm: { ...prev.llm, [key]: value },
    }));
  };

  const updateSTT = (key: string, value: unknown) => {
    setLocal((prev) => ({
      ...prev,
      stt: { ...prev.stt, [key]: value },
    }));
  };

  const handleAlwaysOnTop = (checked: boolean) => {
    setAlwaysOnTop(checked);
    window.electronAPI.setAlwaysOnTop(checked);
  };

  const handleOpacity = (value: number) => {
    setOpacity(value);
    window.electronAPI.setOpacity(value);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* System Info */}
          {systemInfo && (
            <section className="settings-section">
              <h3>System</h3>
              <div className="info-row">
                <span>GPU:</span>
                <span>{systemInfo.gpu ? systemInfo.gpu_name : 'Not available (using CPU)'}</span>
              </div>
              <div className="info-row">
                <span>CPU Threads:</span>
                <span>{systemInfo.cpu_threads}</span>
              </div>
            </section>
          )}

          {/* LLM Settings */}
          <section className="settings-section">
            <h3>AI Model</h3>
            <div className="form-group">
              <label>Provider</label>
              <select
                value={local.llm.provider}
                onChange={(e) => updateLLM('provider', e.target.value)}
              >
                <option value="openai">OpenAI (GPT-4o)</option>
                <option value="claude">Anthropic (Claude)</option>
                <option value="ollama">Ollama (Local)</option>
              </select>
            </div>

            {local.llm.provider === 'openai' && (
              <>
                <div className="form-group">
                  <label>API Key</label>
                  <input
                    type="password"
                    value={local.llm.openai_api_key || ''}
                    onChange={(e) => updateLLM('openai_api_key', e.target.value)}
                    placeholder="sk-..."
                  />
                </div>
                <div className="form-group">
                  <label>Model</label>
                  <input
                    type="text"
                    value={local.llm.openai_model}
                    onChange={(e) => updateLLM('openai_model', e.target.value)}
                  />
                </div>
              </>
            )}

            {local.llm.provider === 'claude' && (
              <>
                <div className="form-group">
                  <label>API Key</label>
                  <input
                    type="password"
                    value={local.llm.claude_api_key || ''}
                    onChange={(e) => updateLLM('claude_api_key', e.target.value)}
                    placeholder="sk-ant-..."
                  />
                </div>
                <div className="form-group">
                  <label>Model</label>
                  <input
                    type="text"
                    value={local.llm.claude_model}
                    onChange={(e) => updateLLM('claude_model', e.target.value)}
                  />
                </div>
              </>
            )}

            {local.llm.provider === 'ollama' && (
              <>
                <div className="form-group">
                  <label>Base URL</label>
                  <input
                    type="text"
                    value={local.llm.ollama_base_url}
                    onChange={(e) => updateLLM('ollama_base_url', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Model</label>
                  <input
                    type="text"
                    value={local.llm.ollama_model}
                    onChange={(e) => updateLLM('ollama_model', e.target.value)}
                    placeholder="llama3"
                  />
                </div>
              </>
            )}

            <div className="form-group">
              <label>Temperature: {local.llm.temperature}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={local.llm.temperature}
                onChange={(e) => updateLLM('temperature', parseFloat(e.target.value))}
              />
            </div>
          </section>

          {/* STT Settings */}
          <section className="settings-section">
            <h3>Speech Recognition</h3>
            <div className="form-group">
              <label>Whisper Model</label>
              <select
                value={local.stt.model_size}
                onChange={(e) => updateSTT('model_size', e.target.value)}
              >
                <option value="tiny">Tiny (75MB, fastest)</option>
                <option value="base">Base (145MB, fast)</option>
                <option value="small">Small (488MB, balanced)</option>
                <option value="medium">Medium (1.5GB, accurate)</option>
                <option value="large-v3">Large V3 (3GB, best)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Language</label>
              <select
                value={local.stt.language}
                onChange={(e) => updateSTT('language', e.target.value)}
              >
                <option value="auto">Auto-detect</option>
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="tr">Turkish</option>
                <option value="zh">Chinese</option>
                <option value="ja">Japanese</option>
                <option value="ko">Korean</option>
                <option value="pt">Portuguese</option>
                <option value="ru">Russian</option>
              </select>
            </div>

            <div className="form-group">
              <label>CPU Threads: {local.stt.cpu_threads}</label>
              <input
                type="range"
                min="1"
                max={systemInfo?.cpu_threads || 8}
                step="1"
                value={local.stt.cpu_threads}
                onChange={(e) => updateSTT('cpu_threads', parseInt(e.target.value))}
              />
            </div>

            <div className="form-group">
              <label>VAD Sensitivity: {local.stt.vad_sensitivity}</label>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.1"
                value={local.stt.vad_sensitivity}
                onChange={(e) => updateSTT('vad_sensitivity', parseFloat(e.target.value))}
              />
            </div>
          </section>

          {/* Audio Settings */}
          <section className="settings-section">
            <h3>Audio Input</h3>
            <div className="form-group checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={local.audio.use_microphone || false}
                  onChange={(e) =>
                    setLocal((prev) => ({
                      ...prev,
                      audio: { ...prev.audio, use_microphone: e.target.checked },
                    }))
                  }
                />
                Use Microphone (instead of system audio)
              </label>
            </div>
            <div className="form-group">
              <label>Capture Device</label>
              <select
                value={local.audio.device_index ?? ''}
                onChange={(e) =>
                  setLocal((prev) => ({
                    ...prev,
                    audio: { ...prev.audio, device_index: e.target.value ? parseInt(e.target.value) : null },
                  }))
                }
              >
                <option value="">{local.audio.use_microphone ? 'Default Microphone' : 'Default Loopback'}</option>
                {devices.map((d) => (
                  <option key={d.index} value={d.index}>
                    {d.name} {d.is_loopback ? '(Loopback)' : ''}
                  </option>
                ))}
              </select>
            </div>
          </section>

          {/* Window Settings */}
          <section className="settings-section">
            <h3>Window</h3>
            <div className="form-group checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={alwaysOnTop}
                  onChange={(e) => handleAlwaysOnTop(e.target.checked)}
                />
                Always on top
              </label>
            </div>
            <div className="form-group">
              <label>Opacity: {Math.round(opacity * 100)}%</label>
              <input
                type="range"
                min="0.3"
                max="1"
                step="0.05"
                value={opacity}
                onChange={(e) => handleOpacity(parseFloat(e.target.value))}
              />
            </div>
          </section>
        </div>

        <div className="modal-footer">
          <button className="btn btn-cancel" onClick={onClose}>Cancel</button>
          <button className="btn btn-save" onClick={handleSave}>Save & Apply</button>
        </div>
      </div>
    </div>
  );
}
