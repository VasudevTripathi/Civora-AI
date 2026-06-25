import React from 'react';

export default function DashboardView({ entityProgress, onViewChange }) {
  const issues = [
    { id: 'CIV-01', title: 'File Articles of Organization', status: entityProgress === 100 ? 'Completed' : 'Todo', priority: 'High', date: 'Immediate' },
    { id: 'CIV-02', title: 'Appoint Registered Agent', status: entityProgress >= 50 ? 'Completed' : 'Todo', priority: 'High', date: 'Immediate' },
    { id: 'CIV-03', title: 'Obtain Federal Employer ID (EIN)', status: entityProgress === 100 ? 'Completed' : 'Todo', priority: 'Medium', date: 'Post-incorporation' },
    { id: 'CIV-04', title: 'Draft Corporate Operating Agreement', status: entityProgress === 100 ? 'Completed' : 'Todo', priority: 'Medium', date: 'Within 30 days' },
    { id: 'CIV-05', title: 'Submit Initial Franchise Tax Report', status: 'Todo', priority: 'Low', date: 'June 2027' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Welcome & Context Header */}
      <div>
        <h1 style={{ marginBottom: '8px' }}>Workspace Dashboard</h1>
        <p>Monitor your company's official corporate standing and upcoming regulatory deadlines.</p>
      </div>

      {/* KPI Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {/* Compliance standing card */}
        <div style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '8px' }}>
            REGULATORY STANDING
          </div>
          <div style={{ fontSize: '20px', fontWeight: '600', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            {entityProgress === 100 ? 'Good Standing' : 'Incomplete setup'}
            <span style={{ fontSize: '10px', color: entityProgress === 100 ? '#15803d' : '#b45309' }}>●</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '8px' }}>
            {entityProgress === 100 ? 'All core files approved by State Secretary.' : 'Requires immediate incorporation filings.'}
          </div>
        </div>

        {/* Wizard progress card */}
        <div style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '8px' }}>
            REGISTRATION WIZARD PROGRESS
          </div>
          <div style={{ fontSize: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>
            {entityProgress}%
          </div>
          <div style={{
            height: '4px',
            backgroundColor: 'var(--bg-hover)',
            borderRadius: '2px',
            marginTop: '12px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${entityProgress}%`,
              height: '100%',
              backgroundColor: 'var(--accent-blue)',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        {/* Documents generated card */}
        <div style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '8px' }}>
            GENERATED DOCUMENTS VAULT
          </div>
          <div style={{ fontSize: '20px', fontWeight: '600', color: 'var(--text-primary)' }}>
            {entityProgress === 100 ? '4 Files' : entityProgress > 0 ? '2 Files' : '0 Files'}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '8px' }}>
            Store and retrieve ready-to-file legal paperwork.
          </div>
        </div>
      </div>

      {/* Action Table (Linear style) */}
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden'
      }}>
        <div style={{
          padding: '16px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ fontSize: '14px', margin: 0 }}>Active Compliance Tasks</h2>
          {entityProgress < 100 && (
            <button
              onClick={() => onViewChange('wizard')}
              className="btn btn-primary"
              style={{ padding: '6px 12px', fontSize: '12px' }}
            >
              Resume Setup
            </button>
          )}
        </div>

        <table className="compliance-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Task</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Due Date</th>
            </tr>
          </thead>
          <tbody>
            {issues.map(issue => (
              <tr key={issue.id}>
                <td style={{ fontWeight: '500', color: 'var(--text-muted)', fontSize: '12px' }}>{issue.id}</td>
                <td style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{issue.title}</td>
                <td>
                  <span className={`badge ${issue.status === 'Completed' ? 'badge-success' : 'badge-warning'}`}>
                    {issue.status}
                  </span>
                </td>
                <td>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: '500',
                    color: issue.priority === 'High' ? '#ef4444' : issue.priority === 'Medium' ? '#f59e0b' : 'var(--text-secondary)'
                  }}>
                    {issue.priority}
                  </span>
                </td>
                <td>{issue.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
