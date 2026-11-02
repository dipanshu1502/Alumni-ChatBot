
import { useState, useRef, useEffect } from "react";
import {
  MessageSquare, Plus, Settings, GraduationCap,
  Send, Paperclip, Menu, X, Bot, User, Sparkles, FileText
} from "lucide-react";
import "./App.css";

const API_BASE_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");
const EMPTY_MESSAGES = [];

const suggestions = [
  "How can I collect my DMC?",
  "What is the admission process?",
  "Tell me about university scholarships.",
  "How can I contact the examination branch?"
];

function App() {
  const [chatHistory, setChatHistory] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const nextChatId = useRef(0);
  const activeChat = chatHistory.find((chat) => chat.id === activeChatId);
  const messages = activeChat ? activeChat.messages : EMPTY_MESSAGES;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const controller = new AbortController();
    const checkApiStatus = () => {
      fetch(`${API_BASE_URL}/`, { signal: controller.signal })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
          }
          setApiStatus("online");
        })
        .catch((error) => {
          if (error.name !== "AbortError") {
            setApiStatus("offline");
          }
        });
    };

    checkApiStatus();
    const intervalId = setInterval(checkApiStatus, 15000);

    return () => {
      clearInterval(intervalId);
      controller.abort();
    };
  }, []);

  const appendMessage = (chatId, message, title) => {
    setChatHistory((previous) => {
      const existingChat = previous.find((chat) => chat.id === chatId);
      if (existingChat) {
        return previous.map((chat) => (
          chat.id === chatId
            ? { ...chat, messages: [...chat.messages, message] }
            : chat
        ));
      }

      return [{ id: chatId, title, messages: [message] }, ...previous];
    });
  };

  const startNewChat = () => {
    setActiveChatId(null);
    setQuestion("");
    setSidebarOpen(false);
    inputRef.current?.focus();
  };

  const openChat = (chatId) => {
    setActiveChatId(chatId);
    setSidebarOpen(false);
  };

  const sendMessage = async (text) => {
    const userQuestion = text.trim();
    if (!userQuestion || loading) return;

    const chatId = activeChatId ?? ++nextChatId.current;
    const chatTitle = userQuestion;
    setActiveChatId(chatId);
    appendMessage(chatId, { role: "user", content: userQuestion }, chatTitle);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userQuestion })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || `Server error: ${response.status}`);
      }
      if (data.error) {
        throw new Error(data.error);
      }
      if (typeof data.answer !== "string" || !Array.isArray(data.sources)) {
        throw new Error("The AI server returned an invalid response.");
      }

      appendMessage(chatId, {
        role: "assistant",
        content: data.answer,
        sources: data.sources
      }, chatTitle);
    } catch (error) {
      appendMessage(chatId, {
        role: "assistant",
        content: `Unable to get an answer from the AI server. ${error.message}`,
        sources: []
      }, chatTitle);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(question);
  };

  return (
    <div className="app-shell">

      {sidebarOpen && (
        <div
          className="mobile-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-logo">
            <GraduationCap size={27} />
          </div>
          <div>
            <h2>Akal University</h2>
            <span>AI Knowledge Assistant</span>
          </div>
          <button className="mobile-close" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <button className="new-chat-btn" onClick={startNewChat}>
          <Plus size={19} />
          <span>New Chat</span>
        </button>

        <div className="sidebar-section">
          <span className="section-label">YOUR WORKSPACE</span>
          <div className="sidebar-link active">
            <MessageSquare size={18} />
            <span>AI Assistant</span>
          </div>
        </div>

        <div className="history-section">
          <span className="section-label">RECENT CHATS</span>

          {chatHistory.length === 0 ? (
            <p className="empty-history">Your conversations will appear here.</p>
          ) : (
            chatHistory.map((chat) => (
          <button
            className={`history-item ${chat.id === activeChatId ? "selected" : ""}`}
            key={chat.id}
            type="button"
            onClick={() => openChat(chat.id)}
            aria-current={chat.id === activeChatId ? "page" : undefined}
          >
            <MessageSquare size={16} />
            <span>{chat.title}</span>
          </button>
            ))
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <Sparkles size={18} />
            <div>
              <strong>AI Powered Search</strong>
              <span>Answers from university documents</span>
            </div>
          </div>
          <div className="profile-row">
            <div className="profile-avatar">AU</div>
            <div className="profile-info">
              <strong>Akal University</strong>
              <span>Knowledge Portal</span>
            </div>
            <Settings size={18} />
          </div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            <button className="menu-btn" onClick={() => setSidebarOpen(true)}>
              <Menu size={22} />
            </button>
            <div className="breadcrumb">
              <span>Workspace</span>
              <span className="breadcrumb-divider">/</span>
              <strong>AI Assistant</strong>
            </div>
          </div>

          <div className="topbar-right">
            <div className="status-indicator">
              <span className={`status-dot ${apiStatus}`} />
              {apiStatus === "checking" ? "Connecting" :
               apiStatus === "online" ? "API connected" : "API unavailable"}
            </div>
            <div className="topbar-avatar">AU</div>
          </div>
        </header>

        <section className="chat-area">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">
                <GraduationCap size={42} />
                <span className="welcome-sparkle"><Sparkles size={16} /></span>
              </div>

              <div className="welcome-badge">
                <span className="status-dot" />
                UNIVERSITY KNOWLEDGE ASSISTANT
              </div>

              <h1>
                How can I help you <span>today?</span>
              </h1>

              <p className="welcome-description">
                Ask anything about Akal University. Get clear answers
                from official university documents.
              </p>

              <div className="suggestion-heading">
                <Sparkles size={17} />
                <span>TRY ASKING</span>
              </div>

              <div className="suggestion-grid">
                {suggestions.map((item, index) => (
                  <button
                    className="suggestion-card"
                    key={index}
                    onClick={() => sendMessage(item)}
                  >
                    <span className="suggestion-icon">
                      {index === 0 ? <FileText size={19} /> :
                       index === 1 ? <GraduationCap size={19} /> :
                       index === 2 ? <Sparkles size={19} /> :
                       <MessageSquare size={19} />}
                    </span>
                    <span>{item}</span>
                    <span className="suggestion-arrow">↗</span>
                  </button>
                ))}
              </div>

              <div className="privacy-note">
                <span className="privacy-dot" />
                Responses are generated using available university documents.
              </div>
            </div>
          ) : (
            <div className="conversation">
              {messages.map((message, index) => (
                <div className={`message-row ${message.role}`} key={index}>
                  <div className={`message-avatar ${message.role}`}>
                    {message.role === "assistant"
                      ? <Bot size={20} />
                      : <User size={19} />}
                  </div>

                  <div className="message-content">
                    <div className="message-author">
                      {message.role === "assistant" ? "Akal AI Assistant" : "You"}
                    </div>
                    <div className="message-text">
                      {message.content}
                    </div>

                    {message.sources?.length > 0 && (
                      <div className="sources-block">
                        <div className="sources-title">
                          <FileText size={15} />
                          Sources used
                        </div>
                        <div className="source-list">
                          {message.sources.map((source) => (
                            <span className="source-chip" key={source}>
                              <FileText size={13} />
                              {source}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-row assistant">
                  <div className="message-avatar assistant">
                    <Bot size={20} />
                  </div>
                  <div className="message-content">
                    <div className="message-author">Akal AI Assistant</div>
                    <div className="typing-indicator">
                      <span /><span /><span />
                      <small>Searching university documents...</small>
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </section>

        <footer className="chat-footer">
          <form className="input-container" onSubmit={handleSubmit}>
            <button
              type="button"
              className="attach-btn"
              title="Attachments coming soon"
              disabled
            >
              <Paperclip size={19} />
            </button>

            <input
              ref={inputRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask anything about Akal University..."
              disabled={loading}
            />

            <button
              className="send-btn"
              type="submit"
              disabled={!question.trim() || loading}
              title="Send message"
            >
              <Send size={19} />
            </button>
          </form>

          <p className="footer-note">
            <Sparkles size={13} />
            AI can make mistakes. Please verify important information with the university.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
