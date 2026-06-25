import React from 'react';

export default function CalendarView() {
  const schedules = [
    { title: 'Delaware Annual Franchise Tax Report', authority: 'Delaware Division of Corporations', freq: 'Annual', date: 'March 1, 2027', penalty: '$200 + 1.5% interest/month', link: 'https://corp.delaware.gov' },
    { title: 'Wyoming Annual Report License Tax', authority: 'Wyoming Secretary of State', freq: 'Annual', date: 'First day of incorporation month', penalty: 'Dissolution after 60 days', link: 'https://wyobiz.wyo.gov' },
    { title: 'IRS Form 1120 (C-Corp Tax Return)', authority: 'Internal Revenue Service (IRS)', freq: 'Annual', date: 'April 15, 2027', penalty: '5% of unpaid tax per month', link: 'https://irs.gov' },
    { title: 'IRS Form 1065 (LLC Partnership Return)', authority: 'Internal Revenue Service (IRS)', freq: 'Annual', date: 'March 15, 2027', penalty: '$220 per partner per month', link: 'https://irs.gov' },
    { title: 'Texas Franchise Tax Public Information Report', authority: 'Texas Comptroller of Public Accounts', freq: 'Annual', date: 'May 15, 2027', penalty: '$50 flat fee + 10% penalty', link: 'https://comptroller.texas.gov' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* View Header */}
      <div>
        <h1 style={{ marginBottom: '8px' }}>Compliance Calendar</h1>
        <p>Proactively monitor statutory filing deadlines to keep your corporation active and avoid penalties.</p>
      </div>

      {/* Compliance Log Grid */}
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '14px', margin: 0 }}>Statutory Recurring Dates</h2>
        </div>

        <table className="compliance-table">
          <thead>
            <tr>
              <th>Regulatory Task</th>
              <th>Authority</th>
              <th>Frequency</th>
              <th>Deadline</th>
              <th>Late Filing Penalty</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {schedules.map((item, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{item.title}</td>
                <td>{item.authority}</td>
                <td>{item.freq}</td>
                <td>{item.date}</td>
                <td style={{ color: '#b45309', fontWeight: '500' }}>{item.penalty}</td>
                <td>
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      fontSize: '12px',
                      color: 'var(--accent-blue)',
                      textDecoration: 'none',
                      fontWeight: '500'
                    }}
                  >
                    Filing Portal ↗
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
