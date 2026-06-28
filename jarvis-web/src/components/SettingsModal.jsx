import React, { useState, useEffect } from 'react';
import { X, Key, Info } from 'lucide-react';

export default function SettingsModal({ isOpen, onClose }) {
  const [apiKey, setApiKey] = useState('');
  const [savedStatus, setSavedStatus] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const storedKey = localStorage.getItem('GEMINI_API_KEY') || '';
      setApiKey(storedKey);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem('GEMINI_API_KEY', apiKey.trim());
    setSavedStatus(true);
    setTimeout(() => {
      setSavedStatus(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={20} style={{ color: 'var(--accent-green)' }} />
            <span>Jarvis System Settings</span>
          </div>
          <button className="icon-btn" onClick={onClose} style={{ border: 'none' }}>
            <X size={18} />
          </button>
        </div>

        <div className="form-group">
          <label className="form-label">Google Gemini API Key</label>
          <input
            type="password"
            className="form-input"
            placeholder="AIzaSy..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '6px' }}>
            Stored locally in your browser. Used for Gemini AI queries when deployed on Vercel/Render.
          </span>
        </div>

        <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '10px', marginBottom: '20px', display: 'flex', gap: '10px' }}>
          <Info size={18} style={{ color: 'var(--accent-cyan)', flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <strong>Deployment Note:</strong> You can also define <code>GEMINI_API_KEY</code> directly in your Vercel or Render Environment Variables dashboard!
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button 
            className="new-chat-btn" 
            onClick={handleSave} 
            style={{ width: 'auto', padding: '10px 24px' }}
          >
            {savedStatus ? 'Saved ✓' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
