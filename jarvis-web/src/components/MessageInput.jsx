import React, { useState, useEffect } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';
import { speechService } from '../services/speechService';

export default function MessageInput({ onSendMessage, disabled }) {
  const [text, setText] = useState('');
  const [isListening, setIsListening] = useState(false);

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSendMessage(text);
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleVoiceInput = () => {
    if (isListening) {
      speechService.stopListening();
      setIsListening(false);
    } else {
      setIsListening(true);
      speechService.startListening(
        (transcript) => {
          setText(transcript);
          setIsListening(false);
        },
        (error) => {
          console.warn('Speech error:', error);
          setIsListening(false);
        }
      );
    }
  };

  return (
    <div className="input-section">
      <div className="input-box-wrapper">
        <button 
          className={`mic-btn ${isListening ? 'listening' : ''}`} 
          onClick={toggleVoiceInput}
          title={isListening ? "Listening... Click to stop" : "Speak to Jarvis"}
        >
          {isListening ? <MicOff size={20} /> : <Mic size={20} />}
        </button>

        <textarea
          className="chat-input"
          placeholder={isListening ? "Listening to your voice..." : "Type your command or message..."}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />

        <button 
          className="send-btn" 
          onClick={handleSend} 
          disabled={!text.trim() || disabled}
          title="Send Command"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
