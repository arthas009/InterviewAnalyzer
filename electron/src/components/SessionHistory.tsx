import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import type { SessionSummary, SessionDetail } from '../types';

interface SessionHistoryProps {
  backendPort: number;
  onClose: () => void;
}

export function SessionHistory({ backendPort, onClose }: SessionHistoryProps) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const baseUrl = `http://127.0.0.1:${backendPort}`;

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${baseUrl}/sessions`);
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewSession = async (id: string) => {
    try {
      const res = await fetch(`${baseUrl}/sessions/${encodeURIComponent(id)}`);
      const data = await res.json();
      setSelectedSession(data);
    } catch (err) {
      console.error('Failed to fetch session:', err);
    }
  };

  const deleteSession = async (id: string) => {
    try {
      await fetch(`${baseUrl}/sessions/${encodeURIComponent(id)}`, { method: 'DELETE' });
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (selectedSession?.id === id) setSelectedSession(null);
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const exportSession = async (id: string, format: 'md' | 'json') => {
    try {
      const res = await fetch(`${baseUrl}/sessions/${encodeURIComponent(id)}/export?format=${format}`);
      const text = await res.text();

      const blob = new Blob([text], { type: format === 'md' ? 'text/markdown' : 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `session-${id.slice(0, 8)}.${format === 'md' ? 'md' : 'json'}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export session:', err);
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) +
      ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (selectedSession) {
    return (
      <div className="session-history">
        <div className="session-detail-header">
          <button className="btn btn-back" onClick={() => setSelectedSession(null)}>← Back</button>
          <h2>Session — {formatDate(selectedSession.started_at)}</h2>
          <div className="session-detail-actions">
            <button className="btn btn-sm" onClick={() => exportSession(selectedSession.id, 'md')}>Export MD</button>
            <button className="btn btn-sm" onClick={() => exportSession(selectedSession.id, 'json')}>Export JSON</button>
          </div>
        </div>
        <div className="session-meta">
          <span>Provider: {selectedSession.provider}</span>
          <span>Questions: {selectedSession.qa_pairs.length}</span>
        </div>
        <div className="session-qa-list">
          {selectedSession.qa_pairs.map((qa, i) => (
            <div key={qa.id} className="message-pair">
              <div className="message question-bubble">
                <div className="message-header">
                  <span className="message-label">Q{i + 1}</span>
                  <span className="message-time">{formatDate(qa.timestamp)}</span>
                </div>
                <div className="message-content">{qa.question}</div>
              </div>
              <div className="message answer-bubble">
                <div className="message-header">
                  <span className="message-label">Answer</span>
                </div>
                <div className="message-content markdown-content">
                  <ReactMarkdown>{qa.answer}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="session-history">
      <div className="session-history-header">
        <h2>Session History</h2>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>

      {loading ? (
        <div className="empty-state"><p>Loading...</p></div>
      ) : sessions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>No sessions yet</h3>
          <p>Past interview sessions will appear here.</p>
        </div>
      ) : (
        <div className="session-list">
          {sessions.map((s) => (
            <div key={s.id} className="session-card" onClick={() => viewSession(s.id)}>
              <div className="session-card-header">
                <span className="session-date">{formatDate(s.started_at)}</span>
                <span className="session-provider">{s.provider}</span>
              </div>
              <div className="session-card-body">
                <span>{s.question_count} question{s.question_count !== 1 ? 's' : ''}</span>
                {s.ended_at && <span className="session-duration">
                  {Math.round((new Date(s.ended_at).getTime() - new Date(s.started_at).getTime()) / 60000)} min
                </span>}
              </div>
              <div className="session-card-actions" onClick={(e) => e.stopPropagation()}>
                <button className="btn btn-sm" onClick={() => exportSession(s.id, 'md')}>Export</button>
                <button className="btn btn-sm btn-danger" onClick={() => deleteSession(s.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
