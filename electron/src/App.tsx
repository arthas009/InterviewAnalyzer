import { useWebSocket } from './hooks/useWebSocket';
import { useAppStore } from './store/appStore';
import { ControlPanel } from './components/ControlPanel';
import { ChatScreen } from './components/ChatScreen';
import { SettingsModal } from './components/SettingsModal';
import { TranscriptOverlay } from './components/TranscriptOverlay';
import { ErrorToast } from './components/ErrorToast';

export default function App() {
  const { startListening, stopListening, updateSettings, isConnected } = useWebSocket();
  const { status, settingsOpen, setSettingsOpen } = useAppStore();

  const startWithMic = () => {
    const settings = useAppStore.getState().settings;
    const micSettings = { ...settings, audio: { ...settings.audio, use_microphone: true } };
    useAppStore.setState({ settings: micSettings });
    startListening();
  };

  return (
    <div className="app-container">
      <ErrorToast />
      <ControlPanel
        status={status}
        isConnected={isConnected}
        onStart={startListening}
        onStartMic={startWithMic}
        onStop={stopListening}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      <div className="main-content">
        <ChatScreen />
        <TranscriptOverlay />
      </div>

      {settingsOpen && (
        <SettingsModal
          onClose={() => setSettingsOpen(false)}
          onSave={(settings) => {
            updateSettings(settings);
            setSettingsOpen(false);
          }}
        />
      )}
    </div>
  );
}
