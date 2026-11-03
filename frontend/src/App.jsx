import { useEffect, useRef, useState } from "react";
import {
  ArrowDown, ArrowRight, Bot, BookOpen, CalendarDays, ChevronDown,
  FileText, GraduationCap, Landmark, Link, Menu, MessageCircle,
  Minus, Send, ShieldCheck, Sparkles, User, X
} from "lucide-react";
import "./App.css";

const API_BASE_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const suggestions = [
  "How can I collect my DMC?",
  "How can I apply for a transcript?",
  "What is the process for a migration certificate?",
  "How can I contact the examination branch?"
];

function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const inputRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading, assistantOpen]);

  useEffect(() => {
    const controller = new AbortController();
    const checkApiStatus = () => {
      fetch(`${API_BASE_URL}/health`, { signal: controller.signal })
        .then((response) => {
          if (!response.ok) throw new Error(`Server error: ${response.status}`);
          return response.json();
        })
        .then((data) => setApiStatus(data.status === "ok" ? "online" : "degraded"))
        .catch((error) => {
          if (error.name !== "AbortError") setApiStatus("offline");
        });
    };
    checkApiStatus();
    const intervalId = setInterval(checkApiStatus, 15000);
    return () => {
      clearInterval(intervalId);
      controller.abort();
    };
  }, []);

  const sendMessage = async (text) => {
    const userQuestion = text.trim();
    if (!userQuestion || loading) return;
    setMessages((previous) => [...previous, { role: "user", content: userQuestion }]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userQuestion })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || data.error || `Server error: ${response.status}`);
      if (typeof data.answer !== "string" || !Array.isArray(data.sources)) {
        throw new Error("The AI server returned an invalid response.");
      }
      setMessages((previous) => [...previous, {
        role: "assistant", content: data.answer, sources: data.sources
      }]);
    } catch (error) {
      setMessages((previous) => [...previous, {
        role: "assistant",
        content: `I couldn’t reach the university assistant. ${error.message}`,
        sources: []
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage(question);
  };

  return (
    <div className="university-site">
      <div className="announcement-bar">
        <span>Admissions open for the 2026–27 session</span>
        <a href="#admissions">Explore programmes <ArrowRight size={13} /></a>
      </div>

      <header className="site-header">
        <a className="university-brand" href="#home" aria-label="Akal University home">
          <span className="brand-mark"><Landmark size={26} strokeWidth={1.7} /></span>
          <span className="brand-copy"><strong>AKAL UNIVERSITY</strong><small>Talwandi Sabo, Punjab</small></span>
        </a>
        <button className="site-menu-toggle" onClick={() => setMobileMenuOpen((open) => !open)} aria-label="Toggle navigation">
          {mobileMenuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
        <nav className={mobileMenuOpen ? "site-nav site-nav-open" : "site-nav"}>
          <a href="#about">About <ChevronDown size={13} /></a>
          <a href="#academics">Academics <ChevronDown size={13} /></a>
          <a href="#admissions">Admissions</a>
          <a href="#campus">Campus life</a>
          <a href="#contact">Contact</a>
          <a className="portal-button" href="#portal">Alumni portal <ArrowRight size={14} /></a>
        </nav>
      </header>

      <main id="home">
        <section className="hero-section">
          <div className="hero-content">
            <div className="hero-eyebrow"><span /> A university rooted in values</div>
            <h1>Learn with purpose.<br /><span>Lead with compassion.</span></h1>
            <p>Discover a future shaped by knowledge, character, and a commitment to serve. Find your place at Akal University.</p>
            <div className="hero-actions">
              <a className="primary-action" href="#admissions">Explore admissions <ArrowRight size={17} /></a>
              <a className="text-action" href="#academics">Discover academics <ArrowDown size={16} /></a>
            </div>
            <div className="hero-note"><ShieldCheck size={16} /> NAAC accredited · UGC recognized</div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="hero-photo" />
            <div className="hero-photo-caption"><span>Knowledge. Values. Service.</span><small>AKAL UNIVERSITY · PUNJAB</small></div>
            <div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" />
          </div>
          <div className="hero-index"><span>01</span><i /><span>03</span></div>
        </section>

        <section className="quick-links" id="academics">
          <a href="#programmes"><span className="quick-icon"><BookOpen size={20} /></span><span><small>Find your path</small><strong>Academic programmes</strong></span><ArrowRight size={17} /></a>
          <a href="#admissions"><span className="quick-icon"><GraduationCap size={21} /></span><span><small>Start your journey</small><strong>Admissions 2026–27</strong></span><ArrowRight size={17} /></a>
          <a href="#events"><span className="quick-icon"><CalendarDays size={19} /></span><span><small>Life at Akal</small><strong>Events & campus news</strong></span><ArrowRight size={17} /></a>
        </section>

        <section className="welcome-strip" id="about">
          <div><span className="section-kicker">WELCOME TO AKAL UNIVERSITY</span><h2>Education that shapes<br />a better tomorrow.</h2></div>
          <p>We bring together rigorous learning, a vibrant campus, and a deep sense of responsibility. Explore our community and the opportunities waiting for you.</p>
        </section>
        <footer className="site-footer" id="contact"><span>AKAL UNIVERSITY</span><span>Talwandi Sabo, Bathinda, Punjab</span></footer>
      </main>

      {!assistantOpen && (
        <button className="assistant-launcher" onClick={() => setAssistantOpen(true)} aria-label="Open Akal AI Assistant">
          <MessageCircle size={22} /><span>Ask Akal AI</span><i />
        </button>
      )}

      {assistantOpen && (
        <aside className="assistant-panel" aria-label="Akal University AI Assistant">
          <header className="assistant-header">
            <div className="assistant-brand-icon"><Sparkles size={20} /></div>
            <div className="assistant-heading"><strong>Akal AI Assistant</strong><span><i className={`status-dot ${apiStatus}`} />{apiStatus === "online" ? "Here to help" : apiStatus === "degraded" ? "Some sources unavailable" : apiStatus === "offline" ? "Connection unavailable" : "Connecting to university"}</span></div>
            <button className="assistant-header-button" onClick={() => setAssistantOpen(false)} aria-label="Minimize assistant"><Minus size={19} /></button>
            <button className="assistant-header-button close-assistant" onClick={() => setAssistantOpen(false)} aria-label="Close assistant"><X size={19} /></button>
          </header>

          <div className="assistant-thread">
            {messages.length === 0 ? (
              <div className="assistant-welcome">
                <div className="welcome-orb"><Sparkles size={23} /></div>
                <span className="assistant-kicker">YOUR UNIVERSITY GUIDE</span>
                <h2>How can I help<br />you today?</h2>
                <p>Ask me about admissions, academics, exams, campus life, and more.</p>
                <div className="suggestion-label">POPULAR QUESTIONS</div>
                <div className="assistant-suggestions">
                  {suggestions.map((item) => (
                    <button key={item} onClick={() => sendMessage(item)} disabled={loading}>
                      <span>{item}</span><ArrowRight size={15} />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="assistant-messages">
                {messages.map((message, index) => (
                  <div className={`chat-message ${message.role}`} key={`${index}-${message.role}`}>
                    {message.role === "assistant" && <span className="chat-avatar"><Bot size={15} /></span>}
                    <div className="chat-message-body">
                      {message.role === "assistant" && <span className="message-name">Akal AI</span>}
                      <div className="chat-bubble">{message.content}</div>
                      {message.role === "assistant" && message.sources?.length > 0 && (
                        <div className="chat-sources">
                          <span className="chat-sources-title"><Link size={12} /> Sources</span>
                          {message.sources.map((source) => <span className="chat-source-chip" key={source}><FileText size={12} />{source}</span>)}
                        </div>
                      )}
                    </div>
                    {message.role === "user" && <span className="chat-avatar user-avatar"><User size={15} /></span>}
                  </div>
                ))}
                {loading && <div className="chat-message assistant"><span className="chat-avatar"><Bot size={15} /></span><div className="chat-message-body"><span className="message-name">Akal AI</span><div className="chat-bubble typing"><i /><i /><i /><small>Looking that up…</small></div></div></div>}
                <div ref={bottomRef} />
              </div>
            )}
          </div>

          <div className="assistant-compose-area">
            <form className="assistant-compose" onSubmit={handleSubmit}>
              <input ref={inputRef} value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question…" maxLength={2000} disabled={loading} aria-label="Ask Akal AI a question" />
              <button type="submit" disabled={!question.trim() || loading} aria-label="Send question"><Send size={17} /></button>
            </form>
            <div className="assistant-disclaimer"><ShieldCheck size={12} /> Answers use university information. Please verify important details.</div>
          </div>
        </aside>
      )}
    </div>
  );
}

export default App;
