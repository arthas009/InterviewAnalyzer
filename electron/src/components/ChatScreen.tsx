import { useEffect, useRef } from 'react';
import { useAppStore } from '../store/appStore';
import { MessageBubble } from './MessageBubble';

export function ChatScreen() {
  const { messages } = useAppStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="chat-screen chat-empty">
        <div className="empty-state">
          <div className="empty-icon">🎙️</div>
          <h2>Ready to analyze</h2>
          <p>Click <strong>Start</strong> to begin listening to your interview.</p>
          <p className="hint">
            The app will capture system audio, detect technical questions,
            and provide answers in real-time.
          </p>
          <p className="shortcut">Shortcut: <kbd>Ctrl+Shift+L</kbd></p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-screen" ref={scrollRef}>
      <div className="messages-container">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>
    </div>
  );
}
