import React, { useRef, useEffect, useState } from 'react';
import { Bot, User, Copy, Check, Sparkles } from 'lucide-react';

export default function ChatArea({ messages, onSelectStarter, isThinking }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isThinking]);

  const starterCards = [
    { title: "Open Web Apps", desc: "Type 'Open YouTube' or 'Play Music'", action: "Open YouTube Sir." },
    { title: "Coding & Math", desc: "Ask for code examples, algorithms, or debugs", action: "Write a python function for quicksort." },
    { title: "Creative & Advice", desc: "Draft emails, strategic advice, or ideas", action: "Introduce yourself in detail." }
  ];

  return (
    <main className="chat-viewport" ref={scrollRef}>
      {messages.length === 0 ? (
        <div className="empty-state">
          <div className="jarvis-avatar-large">
            <Bot size={42} style={{ color: 'var(--accent-green)' }} />
          </div>
          <h1 className="welcome-title">I am JARVIS</h1>
          <p className="welcome-subtitle">Your intelligent voice & AI companion. How may I assist you today, Sir?</p>

          <div className="starters-grid">
            {starterCards.map((card, idx) => (
              <div key={idx} className="starter-card" onClick={() => onSelectStarter(card.action)}>
                <div className="starter-title">{card.title}</div>
                <div className="starter-desc">{card.desc}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}
          {isThinking && (
            <div className="message-row bot">
              <div className="avatar bot">
                <Bot size={20} />
              </div>
              <div className="bubble-content" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} className="pulse-dot" />
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>JARVIS is thinking...</span>
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

function MessageBubble({ message }) {
  const isUser = message.sender === 'user';

  return (
    <div className={`message-row ${isUser ? 'user' : 'bot'}`}>
      <div className={`avatar ${isUser ? 'user' : 'bot'}`}>
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </div>
      <div className="bubble-content">
        <FormattedText content={message.text} />
      </div>
    </div>
  );
}

function FormattedText({ content }) {
  const [copiedIndex, setCopiedIndex] = useState(null);

  if (!content) return null;

  // Simple parser for code blocks delimited by ```
  const parts = content.split(/(```[\s\S]*?```)/g);

  const handleCopy = (codeText, idx) => {
    navigator.clipboard.writeText(codeText);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div>
      {parts.map((part, idx) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const lines = part.slice(3, -3).trim().split('\n');
          const language = lines[0].match(/^[a-zA-Z0-9_-]+$/) ? lines[0] : '';
          const codeContent = language ? lines.slice(1).join('\n') : lines.join('\n');

          return (
            <pre key={idx}>
              <button 
                className="copy-code-btn" 
                onClick={() => handleCopy(codeContent, idx)}
              >
                {copiedIndex === idx ? <Check size={14} color="#25d366" /> : <Copy size={14} />}
                <span>{copiedIndex === idx ? 'Copied' : 'Copy'}</span>
              </button>
              <code>{codeContent}</code>
            </pre>
          );
        }

        // Render standard paragraph text with basic line breaks
        return (
          <p key={idx} style={{ whiteSpace: 'pre-wrap', marginBottom: idx < parts.length - 1 ? '8px' : '0' }}>
            {part}
          </p>
        );
      })}
    </div>
  );
}
