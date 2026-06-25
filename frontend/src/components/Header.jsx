import React from 'react';

export default function Header({ activeView, entityProgress, onSearchClick }) {
  // Breadcrumb mapping
  const breadcrumbs = {
    dashboard: 'Workspace / Dashboard',
    wizard: 'Workspace / Registration Wizard',
    chat: 'Advisory / AI Assistant',
    calendar: 'Compliance / Calendar & Log',
    documents: 'Vault / Generated Documents'
  };

  const getStatusBadge = () => {
    if (entityProgress === 100) {
      return <span className="badge badge-success">● Active / Good Standing</span>;
    } else if (entityProgress > 0) {
      return <span className="badge badge-warning">● Registration In Progress ({entityProgress}%)</span>;
    } else {
      return <span className="badge badge-warning" style={{ backgroundColor: '#fee2e2', color: '#991b1b' }}>● Action Required: Setup Business</span>;
    }
  };

  return (
    <header style={{
      height: 'var(--header-height)',
      borderBottom: '1px solid var(--border-color)',
      backgroundColor: '#ffffff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      flexShrink: 0
    }}>
      {/* Left side: Breadcrumb path & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>
          {breadcrumbs[activeView]}
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {getStatusBadge()}
        </div>
      </div>

      {/* Right side: Global Search / Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          onClick={onSearchClick}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            backgroundColor: 'var(--bg-app)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            fontSize: '12px',
            color: 'var(--text-muted)'
          }}
        >
          <span>🔍</span>
          <span>Search or command...</span>
          <kbd style={{
            fontSize: '9px',
            padding: '2px 4px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: '3px',
            color: 'var(--text-muted)',
            fontWeight: '600',
            fontFamily: 'monospace'
          }}>
            ⌘K
          </kbd>
        </button>
      </div>
    </header>
  );
}
