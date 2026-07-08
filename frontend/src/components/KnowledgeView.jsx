import React, { useState, useEffect } from 'react';
import { getBusinesses, getLicenses, getAuthorities } from '../api/knowledge';

export default function KnowledgeView() {
  const [activeTab, setActiveTab] = useState('businesses');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [businesses, setBusinesses] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [authorities, setAuthorities] = useState([]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [bizData, licData, authData] = await Promise.all([
        getBusinesses(),
        getLicenses(),
        getAuthorities()
      ]);
      setBusinesses(bizData);
      setLicenses(licData);
      setAuthorities(authData);
    } catch (err) {
      setError(err?.message || 'Failed to fetch knowledge directory from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const renderSkeleton = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '16px' }}>
      {[1, 2, 3, 4].map(i => (
        <div key={i} style={{
          height: '40px',
          backgroundColor: '#e2e8f0',
          borderRadius: 'var(--radius-sm)',
          animation: 'pulse 1.5s infinite ease-in-out',
          opacity: 0.6
        }} />
      ))}
      <style>{`
        @keyframes pulse {
          0% { opacity: 0.3; }
          50% { opacity: 0.6; }
          100% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );

  const renderError = () => (
    <div style={{
      padding: '32px',
      textAlign: 'center',
      border: '1px dashed #ef4444',
      borderRadius: 'var(--radius-md)',
      backgroundColor: '#fef2f2',
      color: '#991b1b',
      margin: '20px 0'
    }}>
      <span style={{ fontSize: '32px', display: 'block', marginBottom: '8px' }}>⚠️</span>
      <h3 style={{ marginBottom: '8px', fontWeight: 600 }}>Connection Error</h3>
      <p style={{ color: '#991b1b', opacity: 0.8, fontSize: '13px', marginBottom: '16px' }}>{error}</p>
      <button onClick={loadData} className="btn" style={{
        borderColor: '#fca5a5',
        backgroundColor: '#ffffff',
        color: '#991b1b'
      }}>
        Retry Connection
      </button>
    </div>
  );

  const renderContent = () => {
    if (activeTab === 'businesses') {
      return (
        <table className="compliance-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Jurisdiction</th>
              <th>Authority</th>
              <th>Version</th>
              <th>Effective Date</th>
            </tr>
          </thead>
          <tbody>
            {businesses.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No businesses found.</td>
              </tr>
            ) : (
              businesses.map(biz => (
                <tr key={biz.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{biz.id}</td>
                  <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{biz.title}</td>
                  <td><span className="badge badge-success" style={{ backgroundColor: 'var(--accent-blue-light)', color: 'var(--accent-blue)' }}>{biz.jurisdiction}</span></td>
                  <td>{biz.authority}</td>
                  <td>v{biz.version}</td>
                  <td>{biz.effective_date}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      );
    }

    if (activeTab === 'licenses') {
      return (
        <table className="compliance-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>License Name</th>
              <th>Jurisdiction</th>
              <th>Authority</th>
              <th>Version</th>
              <th>Tags</th>
            </tr>
          </thead>
          <tbody>
            {licenses.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No licenses found.</td>
              </tr>
            ) : (
              licenses.map(lic => (
                <tr key={lic.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{lic.id}</td>
                  <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{lic.title}</td>
                  <td><span className="badge badge-success" style={{ backgroundColor: 'var(--accent-blue-light)', color: 'var(--accent-blue)' }}>{lic.jurisdiction}</span></td>
                  <td>{lic.authority}</td>
                  <td>v{lic.version}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {lic.tags?.map((t, idx) => (
                        <span key={idx} style={{
                          fontSize: '10px',
                          backgroundColor: 'var(--bg-hover)',
                          color: 'var(--text-secondary)',
                          padding: '2px 6px',
                          borderRadius: '4px'
                        }}>{t}</span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      );
    }

    // Authorities Tab
    return (
      <table className="compliance-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Authority Name</th>
            <th>Jurisdiction</th>
            <th>Department / Ministry</th>
            <th>Effective Date</th>
          </tr>
        </thead>
        <tbody>
          {authorities.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No authorities found.</td>
            </tr>
          ) : (
            authorities.map(auth => (
              <tr key={auth.id}>
                <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{auth.id}</td>
                <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{auth.title}</td>
                <td><span className="badge badge-success" style={{ backgroundColor: 'var(--accent-blue-light)', color: 'var(--accent-blue)' }}>{auth.jurisdiction}</span></td>
                <td>{auth.metadata?.ministry_or_department || auth.authority || 'N/A'}</td>
                <td>{auth.effective_date}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Title */}
      <div>
        <h1 style={{ marginBottom: '8px' }}>Knowledge Directory</h1>
        <p>Explore canonical compliance rules, administrative authorities, and license categories loaded in the operating system.</p>
      </div>

      {/* Notion-style Tabs Navigation */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-color)',
        gap: '24px',
        paddingBottom: '2px'
      }}>
        {['businesses', 'licenses', 'authorities'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: 'none',
              border: 'none',
              padding: '8px 4px',
              fontSize: '13px',
              fontWeight: activeTab === tab ? '600' : '400',
              color: activeTab === tab ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === tab ? '2px solid var(--accent-color)' : '2px solid transparent',
              cursor: 'pointer',
              textTransform: 'capitalize',
              transition: 'all 0.15s ease'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Panel container */}
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden'
      }}>
        {loading ? renderSkeleton() : error ? renderError() : renderContent()}
      </div>
    </div>
  );
}
