import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import type { QAMessage } from '../types';

interface MessageBubbleProps {
  message: QAMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);

  const time = new Date(message.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  const copyAnswer = async () => {
    try {
      await navigator.clipboard.writeText(message.answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="message-pair">
      {/* Question bubble */}
      <div className="message question-bubble">
        <div className="message-header">
          <span className="message-label">Question</span>
          <span className="message-time">{time}</span>
        </div>
        <div className="message-content">
          {message.question}
        </div>
      </div>

      {/* Answer bubble */}
      <div className="message answer-bubble">
        <div className="message-header">
          <span className="message-label">Answer</span>
          {!message.answerComplete && <span className="typing-indicator">●●●</span>}
          {message.answerComplete && (
            <button className="btn-copy" onClick={copyAnswer} title="Copy answer">
              {copied ? '✓' : '📋'}
            </button>
          )}
        </div>
        <div className="message-content markdown-content">
          <ReactMarkdown>{message.answer || '...'}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
