import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('clinicAgentSessionId') ?? '');
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    initializeSession();
  }, []);

  async function initializeSession() {
    const storedSessionId = localStorage.getItem('clinicAgentSessionId');
    setError('');
    setIsInitializing(true);

    try {
      if (storedSessionId) {
        const existingSession = await fetch(`${API_BASE_URL}/api/sessions/${storedSessionId}`);
        if (existingSession.ok) {
          const payload = await existingSession.json();
          if (payload.messages.length > 0) {
            setSessionId(payload.session_id);
            setMessages(toUiMessages(payload.messages));
            return;
          }
        }
      }
      await createNewSession();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsInitializing(false);
    }
  }

  async function createNewSession() {
    const response = await fetch(`${API_BASE_URL}/api/sessions`, { method: 'POST' });
    if (!response.ok) {
      throw new Error(`Session creation failed with status ${response.status}`);
    }

    const payload = await response.json();
    setSessionId(payload.session_id);
    setMessages(toUiMessages(payload.messages));
    localStorage.setItem('clinicAgentSessionId', payload.session_id);
  }

  async function sendMessage(event) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || isSending || isInitializing) return;

    setError('');
    setDraft('');
    setIsSending(true);
    setMessages((current) => [...current, { role: 'user', content: message, toolResults: [] }]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: sessionId || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const payload = await response.json();
      setSessionId(payload.session_id);
      localStorage.setItem('clinicAgentSessionId', payload.session_id);
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: payload.message,
          toolResults: payload.tool_results ?? [],
        },
      ]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSending(false);
    }
  }

  async function resetSession() {
    localStorage.removeItem('clinicAgentSessionId');
    setError('');
    setIsInitializing(true);
    try {
      await createNewSession();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsInitializing(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="compose-button">+</div>
        <div className="profile-card">
          <div className="avatar">CA</div>
          <div>
            <h1>ClinicAgent</h1>
            <p>Scheduling assistant</p>
          </div>
        </div>

        <div className="search">Search demo flows</div>

        <div className="thread active">
          <span className="status-dot" />
          <div>
            <strong>Appointment booking</strong>
            <p>Slots, validation, booking</p>
          </div>
        </div>
        <div className="thread">
          <span className="status-dot muted" />
          <div>
            <strong>Patient validation</strong>
            <p>Jamie Rivera / 1990-01-01</p>
          </div>
        </div>
        <div className="thread">
          <span className="status-dot muted" />
          <div>
            <strong>Debug mode</strong>
            <p>Tool calls shown inline</p>
          </div>
        </div>

        <button className="reset-button" onClick={resetSession}>
          New chat
        </button>
      </aside>

      <section className="chat-panel">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Live local demo</p>
            <h2>Clinic scheduling chat</h2>
          </div>
          <div className="session-pill">{sessionId ? `Session ${sessionId.slice(0, 8)}` : 'New session'}</div>
        </header>

        <div className="messages">
          {isInitializing && (
            <div className="bubble assistant typing">
              <span />
              <span />
              <span />
            </div>
          )}
          {messages.map((message, index) => (
            <MessageBubble key={`${message.role}-${index}`} message={message} />
          ))}
          {isSending && (
            <div className="bubble assistant typing">
              <span />
              <span />
              <span />
            </div>
          )}
        </div>

        {error && <div className="error-banner">{error}</div>}

        <form className="composer" onSubmit={sendMessage}>
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Try: Find checkup slots, then validate Jamie Rivera DOB 1990-01-01"
          />
          <button type="submit" disabled={isSending}>
            Send
          </button>
        </form>
      </section>
    </main>
  );
}

function toUiMessages(messages) {
  return messages.map((message) => ({
    role: message.role,
    content: message.content,
    toolResults: [],
  }));
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'from-user' : 'from-agent'}`}>
      <div className={`bubble ${isUser ? 'user' : 'assistant'}`}>
        <p>{message.content}</p>
        {message.toolResults.length > 0 && (
          <details className="tool-details">
            <summary>Tool activity ({message.toolResults.length})</summary>
            <pre>{JSON.stringify(message.toolResults, null, 2)}</pre>
          </details>
        )}
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
