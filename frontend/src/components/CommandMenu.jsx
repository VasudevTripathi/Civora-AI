import React, { useEffect, useRef } from 'react';

export default function CommandMenu({ isOpen, onClose, onViewChange }) {
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const commands = [
    { label: 'Go to Dashboard', icon: '📊', view: 'dashboard' },
    { label: 'Start Business Registration Wizard', icon: '📝', view: 'wizard' },
    { label: 'Consult AI Advisory Chatbot', icon: '💬', view: 'chat' },
    { label: 'View Compliance Deadlines Calendar', icon: '📅', view: 'calendar' },
    { label: 'Access Generated Documents Vault', icon: '📁', view: 'documents' }
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: 'rgba(0, 0, 0, 0.4)',
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'center',
      paddingTop: '120px',
      zIndex: 1000
    }} onClick={onClose}>
      <div style={{
        width: '540px',
        backgroundColor: '#ffffff',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        overflow: 'hidden'
      }} onClick={e => e.stopPropagation()}>
        {/* Command Search Input */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-color)',
          padding: '12px 16px',
          gap: '12px'
        }}>
          <span style={{ fontSize: '16px' }}>🔍</span>
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search..."
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              fontSize: '14px',
              color: 'var(--text-primary)',
              fontFamily: 'inherit'
            }}
          />
          <span style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            border: '1px solid var(--border-color)',
            padding: '2px 6px',
            borderRadius: 'var(--radius-sm)'
          }}>
            ESC
          </span>
        </div>

        {/* Command Options List */}
        <div style={{ padding: '8px 0', maxHeight: '300px', overflowY: 'auto' }}>
          <div style={{
            fontSize: '11px',
            fontWeight: '600',
            color: 'var(--text-muted)',
            padding: '8px 16px'
          }}>
            NAVIGATION COMMANDS
          </div>
          {commands.map((cmd, idx) => (
            <button
              key={idx}
              onClick={() => {
                onViewChange(cmd.view);
                onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                width: '100%',
                padding: '10px 16px',
                border: 'none',
                background: 'transparent',
                textAlign: 'left',
                cursor: 'pointer',
                fontSize: '13px',
                color: 'var(--text-secondary)'
              }}
              onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <span>{cmd.icon}</span>
              <span style={{ flex: 1 }}>{cmd.label}</span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Enter ↵</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
