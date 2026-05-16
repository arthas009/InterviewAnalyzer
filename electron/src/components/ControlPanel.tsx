import type { AppStatus } from '../types';

interface ControlPanelProps {
  status: AppStatus;
  isConnected: boolean;
  onStart: () => void;
  onStartMic: () => void;
  onStop: () => void;
  onOpenSettings: () => void;
}

export function ControlPanel({ status, isConnected, onStart, onStartMic, onStop, onOpenSettings }: ControlPanelProps) {
  const isListening = status === 'listening';
  const isIdle = status === 'idle';

  const statusLabel = {
    idle: 'Ready',
    listening: 'Listening...',
    processing: 'Processing...',
    connecting: 'Connecting...',
  }[status];

  const statusColor = {
    idle: 'status-idle',
    listening: 'status-listening',
    processing: 'status-processing',
    connecting: 'status-connecting',
  }[status];

  return (
    <div className="control-panel">
      <div className="control-left">
        <div className={`status-indicator ${statusColor}`}>
          <span className="status-dot" />
          <span className="status-text">{statusLabel}</span>
        </div>
      </div>

      <div className="control-center">
        <h1 className="app-title">Interview Analyzer</h1>
      </div>

      <div className="control-right">
        {isIdle && isConnected && (
          <>
            <button className="btn btn-start" onClick={onStart}>
              ▶ Start
            </button>
            <button className="btn btn-start btn-mic" onClick={onStartMic}>
              🎤 Test Mic
            </button>
          </>
        )}
        {isListening && (
          <button className="btn btn-stop" onClick={onStop}>
            ■ Stop
          </button>
        )}
        <button className="btn btn-settings" onClick={onOpenSettings} title="Settings">
          ⚙
        </button>
      </div>
    </div>
  );
}
