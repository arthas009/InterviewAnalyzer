import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

interface PrepModeProps {
  onSendMessage: (message: Record<string, unknown>) => void;
  onBack: () => void;
}

interface Evaluation {
  score?: number;
  feedback?: string;
  strengths?: string[];
  improvements?: string[];
  ideal_answer?: string;
}

export function PrepMode({ onSendMessage, onBack }: PrepModeProps) {
  const [topic, setTopic] = useState('general programming');
  const [difficulty, setDifficulty] = useState('medium');
  const [interviewType, setInterviewType] = useState('technical');
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [userAnswer, setUserAnswer] = useState('');
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState<'setup' | 'question' | 'answer' | 'evaluation'>('setup');
  const answerRef = useRef<HTMLTextAreaElement>(null);

  const generateQuestion = () => {
    setLoading(true);
    setEvaluation(null);
    setUserAnswer('');
    onSendMessage({
      type: 'prep_generate',
      topic,
      difficulty,
      interview_type: interviewType,
    });
  };

  const submitAnswer = () => {
    if (!userAnswer.trim()) return;
    setLoading(true);
    setPhase('evaluation');
    onSendMessage({
      type: 'prep_evaluate',
      question: currentQuestion,
      answer: userAnswer,
    });
  };

  // Listen for WebSocket messages via custom events
  useEffect(() => {
    const handlePrepQuestion = (e: CustomEvent) => {
      setCurrentQuestion(e.detail.question);
      setPhase('answer');
      setLoading(false);
    };

    const handlePrepEvaluation = (e: CustomEvent) => {
      try {
        let evalData = e.detail.evaluation;
        // Try to parse JSON from the evaluation string
        if (typeof evalData === 'string') {
          // Extract JSON from potential markdown code blocks
          const jsonMatch = evalData.match(/```json\s*([\s\S]*?)\s*```/) || evalData.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            evalData = JSON.parse(jsonMatch[1] || jsonMatch[0]);
          }
        }
        setEvaluation(evalData);
      } catch {
        setEvaluation({ feedback: e.detail.evaluation, score: 0 });
      }
      setLoading(false);
    };

    window.addEventListener('prep_question', handlePrepQuestion as EventListener);
    window.addEventListener('prep_evaluation', handlePrepEvaluation as EventListener);

    return () => {
      window.removeEventListener('prep_question', handlePrepQuestion as EventListener);
      window.removeEventListener('prep_evaluation', handlePrepEvaluation as EventListener);
    };
  }, []);

  return (
    <div className="prep-mode">
      <div className="prep-header">
        <button className="btn btn-back" onClick={onBack}>← Live Mode</button>
        <h2>Practice Mode</h2>
      </div>

      {phase === 'setup' && (
        <div className="prep-setup">
          <div className="empty-state">
            <div className="empty-icon">🎯</div>
            <h3>Interview Practice</h3>
            <p>Configure your practice session and start answering questions.</p>
          </div>

          <div className="prep-config">
            <div className="form-group">
              <label>Topic</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., React, Python, Data Structures"
              />
            </div>

            <div className="form-group">
              <label>Difficulty</label>
              <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>

            <div className="form-group">
              <label>Interview Type</label>
              <select value={interviewType} onChange={(e) => setInterviewType(e.target.value)}>
                <option value="technical">Technical</option>
                <option value="behavioral">Behavioral</option>
                <option value="system_design">System Design</option>
                <option value="coding">Coding</option>
              </select>
            </div>

            <button
              className="btn btn-start prep-start-btn"
              onClick={generateQuestion}
              disabled={loading}
            >
              {loading ? 'Generating...' : '🎯 Generate Question'}
            </button>
          </div>
        </div>
      )}

      {phase === 'answer' && (
        <div className="prep-answer-phase">
          <div className="prep-question-card">
            <div className="prep-question-header">
              <span className="prep-badge">{difficulty} • {interviewType}</span>
            </div>
            <div className="prep-question-text">
              <ReactMarkdown>{currentQuestion}</ReactMarkdown>
            </div>
          </div>

          <div className="prep-answer-area">
            <label>Your Answer</label>
            <textarea
              ref={answerRef}
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="Type your answer here... (or use the microphone to speak and paste the transcript)"
              rows={8}
            />
            <div className="prep-answer-actions">
              <button className="btn btn-start" onClick={submitAnswer} disabled={loading || !userAnswer.trim()}>
                {loading ? 'Evaluating...' : '✓ Submit Answer'}
              </button>
              <button className="btn btn-cancel" onClick={() => { setPhase('setup'); setCurrentQuestion(''); }}>
                Skip
              </button>
            </div>
          </div>
        </div>
      )}

      {phase === 'evaluation' && evaluation && (
        <div className="prep-evaluation-phase">
          <div className="prep-question-card">
            <div className="prep-question-text">
              <ReactMarkdown>{currentQuestion}</ReactMarkdown>
            </div>
          </div>

          <div className="prep-eval-card">
            <div className="prep-score">
              <span className="prep-score-number">{evaluation.score || '?'}</span>
              <span className="prep-score-label">/ 10</span>
            </div>

            {evaluation.feedback && (
              <div className="prep-eval-section">
                <h4>Feedback</h4>
                <p>{evaluation.feedback}</p>
              </div>
            )}

            {evaluation.strengths && evaluation.strengths.length > 0 && (
              <div className="prep-eval-section">
                <h4>✅ Strengths</h4>
                <ul>{evaluation.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}

            {evaluation.improvements && evaluation.improvements.length > 0 && (
              <div className="prep-eval-section">
                <h4>💡 Improvements</h4>
                <ul>{evaluation.improvements.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}

            {evaluation.ideal_answer && (
              <div className="prep-eval-section">
                <h4>📝 Ideal Answer</h4>
                <div className="markdown-content">
                  <ReactMarkdown>{evaluation.ideal_answer}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>

          <div className="prep-next-actions">
            <button className="btn btn-start" onClick={generateQuestion}>
              Next Question →
            </button>
            <button className="btn btn-cancel" onClick={() => setPhase('setup')}>
              Change Topic
            </button>
          </div>
        </div>
      )}

      {loading && phase === 'evaluation' && (
        <div className="prep-loading">
          <div className="typing-indicator">●●●</div>
          <p>Evaluating your answer...</p>
        </div>
      )}
    </div>
  );
}
