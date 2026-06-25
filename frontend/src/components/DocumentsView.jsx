import React from 'react';

export default function DocumentsView({ entityProgress }) {
  const documents = [
    { name: 'Articles of Organization (Filing draft)', state: 'Delaware / Wyoming', format: 'PDF', size: '240 KB', status: entityProgress >= 50 ? 'Generated' : 'Pending Wizard' },
    { name: 'IRS SS-4 Form (EIN application)', state: 'Federal (IRS)', format: 'PDF', size: '180 KB', status: entityProgress === 100 ? 'Generated' : 'Pending Wizard' },
    { name: 'Corporate Operating Agreement (Draft)', state: 'Delaware / Wyoming', format: 'DOCX', size: '1.2 MB', status: entityProgress === 100 ? 'Generated' : 'Pending Wizard' },
    { name: 'Registered Agent Consent Form', state: 'Delaware / Wyoming', format: 'PDF', size: '94 KB', status: entityProgress >= 50 ? 'Generated' : 'Pending Wizard' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* View Header */}
      <div>
        <h1 style={{ marginBottom: '8px' }}>Documents Vault</h1>
        <p>Access generated templates, state filing packages, and IRS applications.</p>
      </div>

      {/* Grid List (Linear/Notion style) */}
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '14px', margin: 0 }}>Synthesized Compliance Files</h2>
        </div>

        <table className="compliance-table">
          <thead>
            <tr>
              <th>Document File Name</th>
              <th>Jurisdiction</th>
              <th>Format</th>
              <th>File Size</th>
              <th>Standing</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                  📄 {doc.name}
                </td>
                <td>{doc.state}</td>
                <td style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)' }}>{doc.format}</td>
                <td>{doc.size}</td>
                <td>
                  <span className={`badge ${doc.status === 'Generated' ? 'badge-success' : 'badge-warning'}`}>
                    {doc.status}
                  </span>
                </td>
                <td>
                  <button
                    disabled={doc.status !== 'Generated'}
                    style={{
                      border: 'none',
                      background: 'none',
                      color: doc.status === 'Generated' ? 'var(--accent-blue)' : 'var(--text-muted)',
                      cursor: doc.status === 'Generated' ? 'pointer' : 'not-allowed',
                      fontSize: '12px',
                      fontWeight: '500',
                      padding: 0
                    }}
                    onClick={() => doc.status === 'Generated' && alert(`Downloading ${doc.name}...`)}
                  >
                    Download ↓
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
