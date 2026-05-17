import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  buildFlowSubmissionMessage,
  getFlow,
  getFlowSummary,
  getOrderedFlows,
} from './flows';
import heroImage from './assets/clinic-agent-1.avif';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';
const SESSION_STORAGE_KEY = 'clinicAgentSessionId';
const CHAT_ROUTE_HASH = '#/chat';

function App() {
  const [view, setView] = useState(getRouteView);
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(() => sessionStorage.getItem(SESSION_STORAGE_KEY) ?? '');
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const [isInitializing, setIsInitializing] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [hasLoadedChat, setHasLoadedChat] = useState(false);
  const [queuedFlowId, setQueuedFlowId] = useState(null);
  const [activeFlow, setActiveFlow] = useState(null);
  const [pendingConfirmation, setPendingConfirmation] = useState(null);
  const messagesEndRef = useRef(null);
  const flows = useMemo(() => getOrderedFlows(), []);

  useEffect(() => {
    function handleHashChange() {
      setView(getRouteView());
    }

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    window.location.hash = view === 'chat' ? CHAT_ROUTE_HASH : '';
  }, [view]);

  useEffect(() => {
    if (view === 'chat' && !hasLoadedChat) {
      initializeSession();
    }
  }, [view, hasLoadedChat]);

  useEffect(() => {
    if (view !== 'chat' || !queuedFlowId || !hasLoadedChat || activeFlow || pendingConfirmation) {
      return;
    }

    startFlow(queuedFlowId);
    setQueuedFlowId(null);
  }, [view, queuedFlowId, hasLoadedChat, activeFlow, pendingConfirmation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pendingConfirmation, activeFlow, error]);

  async function initializeSession() {
    const storedSessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
    localStorage.removeItem(SESSION_STORAGE_KEY);

    setError('');
    setIsInitializing(true);

    try {
      if (storedSessionId) {
        const existingSession = await fetch(`${API_BASE_URL}/api/sessions/${storedSessionId}`);
        if (existingSession.ok) {
          const payload = await existingSession.json();
          setSessionId(payload.session_id);
          setMessages(toUiMessages(payload.messages));
          setHasLoadedChat(true);
          return;
        }
      }

      await createNewSession();
      setHasLoadedChat(true);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
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
    sessionStorage.setItem(SESSION_STORAGE_KEY, payload.session_id);
  }

  function openChat(flowId = null) {
    setView('chat');
    if (flowId) {
      setQueuedFlowId(flowId);
    }
  }

  function returnToLanding() {
    setView('landing');
  }

  function startFlow(flowId) {
    const flow = getFlow(flowId);
    if (!flow) {
      return;
    }

    const historyStartIndex =
      activeFlow?.historyStartIndex ?? pendingConfirmation?.historyStartIndex ?? messages.length;

    setError('');
    setPendingConfirmation(null);
    setActiveFlow({
      flowId,
      stepIndex: 0,
      answers: {},
      historyStartIndex,
    });
    setMessages((current) => [
      ...current.slice(0, historyStartIndex),
      createMessage('assistant', `${flow.intro}\n\n${flow.steps[0].prompt}`),
    ]);
  }

  function handleFlowAnswer(userAnswer) {
    const flow = getFlow(activeFlow.flowId);
    const currentStep = flow.steps[activeFlow.stepIndex];
    const nextAnswers = {
      ...activeFlow.answers,
      [currentStep.key]: userAnswer,
    };
    const nextMessages = [createMessage('user', userAnswer)];

    if (activeFlow.stepIndex === flow.steps.length - 1) {
      setActiveFlow(null);
      setPendingConfirmation({
        flowId: flow.id,
        answers: nextAnswers,
        historyStartIndex: activeFlow.historyStartIndex,
      });
      nextMessages.push(createMessage('assistant', flow.confirmationIntro));
    } else {
      const nextStepIndex = activeFlow.stepIndex + 1;
      setActiveFlow({
        flowId: flow.id,
        stepIndex: nextStepIndex,
        answers: nextAnswers,
        historyStartIndex: activeFlow.historyStartIndex,
      });
      nextMessages.push(createMessage('assistant', flow.steps[nextStepIndex].prompt));
    }

    setMessages((current) => [...current, ...nextMessages]);
  }

  async function sendMessage(event) {
    event.preventDefault();

    const message = draft.trim();
    if (!message || isSending || isInitializing) {
      return;
    }

    setDraft('');

    if (pendingConfirmation) {
      setError('Confirm or revise the current workflow before sending a new message.');
      return;
    }

    if (activeFlow) {
      handleFlowAnswer(message);
      return;
    }

    await sendChatMessage(message);
  }

  async function handleComposerKeyDown(event) {
    if (event.key !== 'Enter' || event.shiftKey) {
      return;
    }

    event.preventDefault();
    await sendMessage(event);
  }

  async function sendChatMessage(userMessage, visibleMessage = userMessage) {
    setError('');
    setIsSending(true);
    setMessages((current) => [...current, createMessage('user', visibleMessage)]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const payload = await response.json();
      setSessionId(payload.session_id);
      sessionStorage.setItem(SESSION_STORAGE_KEY, payload.session_id);
      setMessages((current) => [
        ...current,
        createMessage('assistant', payload.message, payload.tool_results ?? []),
      ]);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsSending(false);
    }
  }

  async function confirmFlow() {
    if (!pendingConfirmation) {
      return;
    }

    const submission = buildFlowSubmissionMessage(
      pendingConfirmation.flowId,
      pendingConfirmation.answers,
    );

    setPendingConfirmation(null);
    await sendChatMessage(submission);
  }

  function reviseFlow() {
    if (!pendingConfirmation) {
      return;
    }

    const flow = getFlow(pendingConfirmation.flowId);
    setPendingConfirmation(null);
    setActiveFlow({
      flowId: flow.id,
      stepIndex: 0,
      answers: {},
      historyStartIndex: pendingConfirmation.historyStartIndex,
    });
    setMessages((current) => [
      ...current.slice(0, pendingConfirmation.historyStartIndex),
      createMessage('assistant', `${flow.intro}\n\n${flow.steps[0].prompt}`),
    ]);
  }

  function cancelFlow() {
    const historyStartIndex =
      activeFlow?.historyStartIndex ?? pendingConfirmation?.historyStartIndex ?? messages.length;

    setPendingConfirmation(null);
    setActiveFlow(null);
    setError('');
    setMessages((current) => [
      ...current.slice(0, historyStartIndex),
    ]);
  }

  async function resetSession() {
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
    localStorage.removeItem(SESSION_STORAGE_KEY);
    setSessionId('');
    setMessages([]);
    setError('');
    setActiveFlow(null);
    setPendingConfirmation(null);
    setIsInitializing(true);

    try {
      await createNewSession();
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsInitializing(false);
    }
  }

  const activeStep =
    activeFlow && getFlow(activeFlow.flowId).steps[activeFlow.stepIndex]
      ? getFlow(activeFlow.flowId).steps[activeFlow.stepIndex]
      : null;

  const composerPlaceholder = pendingConfirmation
    ? 'Use the confirmation actions above to continue.'
    : activeStep?.placeholder ?? 'Ask about booking, intake, availability, or clinic policies';

  return view === 'chat' ? (
    <ChatShell
      activeFlow={activeFlow}
      composerPlaceholder={composerPlaceholder}
      draft={draft}
      error={error}
      isInitializing={isInitializing}
      isSending={isSending}
      messages={messages}
      messagesEndRef={messagesEndRef}
      onChangeDraft={setDraft}
      onConfirmFlow={confirmFlow}
      onResetSession={resetSession}
      onReturnToLanding={returnToLanding}
      onReviseFlow={reviseFlow}
      onCancelFlow={cancelFlow}
      onStartFlow={startFlow}
      onSubmit={sendMessage}
      onSubmitFromKeyboard={handleComposerKeyDown}
      pendingConfirmation={pendingConfirmation}
      sessionId={sessionId}
    />
  ) : (
    <LandingPage onOpenAssistant={openChat} />
  );
}

function LandingPage({ onOpenAssistant }) {
  const flows = getOrderedFlows();

  return (
    <main className="landing-shell">
      <header className="landing-topbar">
        <nav className="landing-nav" aria-label="Landing navigation">
          <a href="#overview">Home</a>
          <a href="#capabilities">About</a>
          <a href="#capabilities">Services</a>
          <a href="#principles">FAQ</a>
          <button className="nav-cta" onClick={() => onOpenAssistant()}>
            Open assistant
          </button>
        </nav>
      </header>

      <section className="landing-hero-banner" id="overview">
        <img
          className="hero-background-image"
          src={heroImage}
          alt="Clinic staff standing together in a clinical setting."
        />
        <div className="hero-overlay">
          <div className="hero-copy hero-copy-banner">
            <div className="hero-brand-pill">
              <span className="hero-brand-mark">CA</span>
              <span>ClinicAgent</span>
            </div>
            <p className="section-kicker">We provide guided patient access</p>
            <h1>Health care scheduling support with a calmer first-contact experience.</h1>
            <p className="hero-text">
              ClinicAgent helps new and returning patients request appointments, move through
              intake, and get clinic answers through one structured assistant.
            </p>
            <div className="hero-actions">
              <button className="primary-button" onClick={() => onOpenAssistant('new-patient')}>
                Start consultation
              </button>
              <button
                className="secondary-button"
                onClick={() => onOpenAssistant('book-appointment')}
              >
                Book appointment
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section trust-strip">
        <ul className="trust-list">
          <li>Guided intake</li>
          <li>Appointment booking</li>
          <li>Clinic questions</li>
          <li>No login in v1</li>
        </ul>
      </section>

      <section className="landing-section" id="capabilities">
        <div className="section-heading">
          <p className="section-kicker">What the assistant handles</p>
          <h2>Focused workflows, kept short and clear.</h2>
        </div>
        <div className="capability-grid">
          {flows.map((flow) => (
            <article key={flow.id} className="capability-card">
              <h3>{flow.label}</h3>
              <p>{flow.shortLabel}</p>
              <button className="text-button" onClick={() => onOpenAssistant(flow.id)}>
                Open in chat
              </button>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section about-section" id="principles">
        <div className="about-copy">
          <p className="section-kicker">About ClinicAgent</p>
          <h2>A patient-facing assistant built for the first few minutes of clinic access.</h2>
          <p className="about-lead">
            ClinicAgent is designed for the part of the patient journey where most people need the
            most clarity: booking a first visit, starting intake, rescheduling, or asking simple
            clinic questions without getting dropped into a full portal.
          </p>

          <div className="about-steps">
            <article className="about-step">
              <span className="step-number">01</span>
              <div>
                <h3>Start with a guided request</h3>
                <p>The assistant moves through one clear question at a time instead of asking for everything at once.</p>
              </div>
            </article>
            <article className="about-step">
              <span className="step-number">02</span>
              <div>
                <h3>Review before anything is sent</h3>
                <p>Appointment and intake details are summarized for confirmation so the patient stays in control.</p>
              </div>
            </article>
            <article className="about-step">
              <span className="step-number">03</span>
              <div>
                <h3>Keep the boundary narrow</h3>
                <p>Public chat helps with scheduling and access, not full account access or sensitive records.</p>
              </div>
            </article>
          </div>
        </div>

        <aside className="about-panel">
          <div className="about-panel-card">
            <p className="sidebar-label">What it handles well</p>
            <ul className="about-list">
              <li>New patient intake basics</li>
              <li>Appointment booking requests</li>
              <li>Rescheduling and timing changes</li>
              <li>Clinic information and visit prep questions</li>
            </ul>
          </div>

          <div className="about-panel-card muted">
            <p className="sidebar-label">What stays out of public chat</p>
            <ul className="about-list">
              <li>Medical records access</li>
              <li>Insurance and billing workflows</li>
              <li>Medication and history capture</li>
              <li>Account-level patient portal actions</li>
            </ul>
          </div>
        </aside>
      </section>
    </main>
  );
}

function ChatShell({
  activeFlow,
  composerPlaceholder,
  draft,
  error,
  isInitializing,
  isSending,
  messages,
  messagesEndRef,
  onCancelFlow,
  onChangeDraft,
  onConfirmFlow,
  onResetSession,
  onReturnToLanding,
  onReviseFlow,
  onStartFlow,
  onSubmit,
  onSubmitFromKeyboard,
  pendingConfirmation,
  sessionId,
}) {
  return (
    <main className="chat-shell">
      <section className="chat-workspace single-chat-layout">
        <header className="workspace-header">
          <div className="chat-header-main">
            <button className="back-link" onClick={onReturnToLanding}>
              Back to overview
            </button>
            <div className="sidebar-brand chat-brand">
              <div className="brand-mark">CA</div>
              <div>
                <p className="section-kicker">Patient assistant</p>
                <h2>ClinicAgent chat</h2>
              </div>
            </div>
          </div>
          <div className="workspace-status">
            <span className="status-badge">{isSending ? 'Assistant responding' : 'Ready'}</span>
            <button className="secondary-button header-button" onClick={onResetSession}>
              New chat
            </button>
          </div>
        </header>

        <MessageList
          isInitializing={isInitializing}
          isSending={isSending}
          messages={messages}
          messagesEndRef={messagesEndRef}
        />

        {error ? <div className="error-banner">{error}</div> : null}

        <WorkflowInlineBar
          activeFlow={activeFlow}
          onCancelFlow={onCancelFlow}
          onConfirmFlow={onConfirmFlow}
          onReviseFlow={onReviseFlow}
          pendingConfirmation={pendingConfirmation}
          sessionId={sessionId}
        />

        <form className="composer" onSubmit={onSubmit}>
          <label className="composer-label" htmlFor="composer-input">
            Message
          </label>
          <textarea
            id="composer-input"
            rows="3"
            value={draft}
            disabled={pendingConfirmation !== null}
            onChange={(event) => onChangeDraft(event.target.value)}
            onKeyDown={onSubmitFromKeyboard}
            placeholder={composerPlaceholder}
          />
          <button className="primary-button" type="submit" disabled={isSending || pendingConfirmation !== null}>
            {activeFlow ? 'Continue' : 'Send'}
          </button>
        </form>
      </section>
    </main>
  );
}

function WorkflowInlineBar({
  activeFlow,
  onCancelFlow,
  onConfirmFlow,
  onReviseFlow,
  pendingConfirmation,
  sessionId,
}) {
  if (activeFlow) {
    const flow = getFlow(activeFlow.flowId);
    const stepCount = flow.steps.length;
    const currentStepNumber = activeFlow.stepIndex + 1;

    return (
      <section className="workflow-inline-bar">
        <div className="workflow-inline-copy">
          <strong>{flow.shortLabel}</strong>
          <span>
            Step {currentStepNumber} of {stepCount}
          </span>
        </div>
        <div className="workflow-inline-actions">
          <span className="progress-pill">
            Step {currentStepNumber} of {stepCount}
          </span>
          <button className="text-button" onClick={onCancelFlow}>
            Cancel workflow
          </button>
        </div>
      </section>
    );
  }

  if (pendingConfirmation) {
    const flow = getFlow(pendingConfirmation.flowId);
    const summary = getFlowSummary(pendingConfirmation.flowId, pendingConfirmation.answers)
      .slice(0, 2)
      .map((item) => `${item.label}: ${item.value}`)
      .join(' | ');

    return (
      <section className="workflow-inline-bar confirm">
        <div className="workflow-inline-copy">
          <strong>{flow.shortLabel}</strong>
          <span>{summary || 'Review the captured details before sending.'}</span>
        </div>
        <div className="workflow-inline-actions">
          <button className="primary-button" onClick={onConfirmFlow}>
            Confirm
          </button>
          <button className="secondary-button" onClick={onReviseFlow}>
            Revise
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="workflow-inline-bar idle">
      <div className="workflow-inline-copy">
        <strong>{sessionId ? `Session ${sessionId.slice(0, 8)}` : 'Starting session'}</strong>
        <span>Ask about appointments, intake, rescheduling, or clinic questions.</span>
      </div>
    </section>
  );
}

function MessageList({ isInitializing, isSending, messages, messagesEndRef }) {
  return (
    <section className="message-list">
      {isInitializing ? (
        <div className="message-row">
          <div className="message-bubble assistant typing-indicator">
            <span />
            <span />
            <span />
          </div>
        </div>
      ) : null}

      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isSending ? (
        <div className="message-row">
          <div className="message-bubble assistant typing-indicator">
            <span />
            <span />
            <span />
          </div>
        </div>
      ) : null}

      <div ref={messagesEndRef} />
    </section>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'from-user' : ''}`}>
      <article className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
        <span className="message-role">{isUser ? 'Patient request' : 'ClinicAgent'}</span>
        <p>{message.content}</p>
        {message.toolResults.length > 0 ? (
          <details className="tool-details">
            <summary>Tool activity ({message.toolResults.length})</summary>
            <pre>{JSON.stringify(message.toolResults, null, 2)}</pre>
          </details>
        ) : null}
      </article>
    </div>
  );
}

function createMessage(role, content, toolResults = []) {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    content,
    toolResults,
  };
}

function toUiMessages(messages) {
  return messages.map((message) => createMessage(message.role, message.content));
}

function getRouteView() {
  return window.location.hash === CHAT_ROUTE_HASH ? 'chat' : 'landing';
}

function getErrorMessage(error) {
  return error instanceof Error ? error.message : 'Unexpected request failure';
}

export default App;
