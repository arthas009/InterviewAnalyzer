import { useAppStore } from '../store/appStore';

export function TranscriptOverlay() {
  const { transcript, status } = useAppStore();

  if (status !== 'listening' || !transcript) {
    return null;
  }

  // Show last 200 characters of transcript
  const displayText = transcript.length > 200
    ? '...' + transcript.slice(-200)
    : transcript;

  return (
    <div className="transcript-overlay">
      <div className="transcript-header">
        <span className="transcript-label">Live Transcript</span>
        <span className="recording-dot" />
      </div>
      <div className="transcript-text">
        {displayText}
      </div>
    </div>
  );
}
