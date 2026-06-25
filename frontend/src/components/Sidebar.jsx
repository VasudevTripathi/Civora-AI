import React from 'react';

export default function Sidebar({ activeView, onViewChange, entityProgress }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'wizard', label: 'Registration Wizard', icon: '📝', badge: entityProgress < 100 ? `${entityProgress}%` : null },
    { id: 'chat', label: 'AI Advisory Chat', icon: '💬' },
    { id: 'calendar', label: 'Compliance Calendar', icon: '📅' },
    { id: 'documents', label: 'Documents Hub', icon: '📁' }
  ];

  return (
    <aside className="sidebar" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Notion-style Workspace Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        cursor: 'pointer'
      }}>
        <div style={{
          width: '24px',
          height: '24px',
          backgroundColor: 'var(--accent-color)',
          borderRadius: 'var(--radius-sm)',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          fontWeight: '700'
        }}>
          C
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
            Civora Workspace
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            US-DE LLC Sandbox
          </div>
        </div>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>▼</span>
      </div>

      {/* Navigation Menu */}
      <nav style={{ padding: '16px 8px', flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {menuItems.map(item => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: '100%',
                padding: '8px 12px',
                border: 'none',
                background: isActive ? 'var(--bg-hover)' : 'transparent',
                borderRadius: 'var(--radius-sm)',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontSize: '13px',
                fontWeight: isActive ? '500' : '400',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'background 0.1s ease'
              }}
            >
              <span>{item.icon}</span>
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge && (
                <span style={{
                  fontSize: '10px',
                  backgroundColor: 'var(--accent-blue-light)',
                  color: 'var(--accent-blue)',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  fontWeight: '600'
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <div style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          backgroundColor: '#e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          fontWeight: '500'
        }}>
          VT
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '12px', fontWeight: '500' }}>Vasudev Tripathi</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Admin Role</div>
        </div>
      </div>
    </aside>
  );
}
