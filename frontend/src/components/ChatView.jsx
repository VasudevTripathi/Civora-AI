import React, { useState } from 'react';

export default function ChatView() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello! I am your Civora AI compliance mentor. Ask me any question regarding LLC setups, Delaware vs Wyoming filing rules, or EIN registration steps.' }
  ]);
  const [inputVal, setInputVal] = useState('');

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    const userMsg = { role: 'user', text: inputVal };
    setMessages(prev => [...prev, userMsg]);
    setInputVal('');

    // Simulate AI response
    setTimeout(() => {
      let aiResponseText = 'To form an LLC in Delaware, you must file a Certificate of Formation with the Delaware Division of Corporations. The filing fee is $90. You are also required to appoint a Registered Agent located in Delaware.';
      
      if (inputVal.toLowerCase().includes('wyoming')) {
        aiResponseText = 'Wyoming LLC filings require Articles of Organization submitted to the Wyoming Secretary of State. The state fee is $100. Wyoming is popular because there is no state corporate or personal income tax, and it offers high privacy.';
      } else if (inputVal.toLowerCase().includes('ein')) {
        aiResponseText = 'An EIN (Employer Identification Number) is a free 9-digit number assigned by the IRS. You can apply online instantly via the official IRS portal or file Form SS-4 if you do not have a US Social Security Number.';
      }

      setMessages(prev => [...prev, { role: 'assistant', text: aiResponseText }]);
    }, 800);
  };

  return (
    <div style={{
      display: 'flex',
      height: 'calc(100vh - var(--header-height) - 48px)',
      margin: '-24px -40px', /* Flush fit */
      backgroundColor: '#ffffff'
    }}>
      {/* Left Pane: Conversations */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid var(--border-color)',
        height: '100%'
      }}>
        {/* Chat Messages */}
        <div style={{
          flex: 1,
          padding: '24px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                width: '100%'
              }}
            >
              <div style={{
                fontSize: '11px',
                fontWeight: '600',
                color: 'var(--text-muted)',
                marginBottom: '4px',
                padding: '0 4px'
              }}>
                {msg.role === 'user' ? 'YOU' : 'CIVORA ADVISOR'}
              </div>
              <div style={{
                backgroundColor: msg.role === 'user' ? 'var(--accent-blue-light)' : 'var(--bg-app)',
                color: msg.role === 'user' ? 'var(--accent-blue)' : 'var(--text-primary)',
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                fontSize: '13px',
                lineHeight: '1.5',
                maxWidth: '80%',
                border: '1px solid',
                borderColor: msg.role === 'user' ? 'transparent' : 'var(--border-color)'
              }}>
                {msg.text}
              </div>
            </div>
          ))}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={handleSend}
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            gap: '12px',
            backgroundColor: '#ffffff'
          }}
        >
          <input
            type="text"
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            placeholder="Ask about state fees, corporate structures, tax guidelines..."
            className="form-input"
            style={{ flex: 1, height: '38px' }}
          />
          <button type="submit" className="btn btn-primary" style={{ padding: '0 20px', height: '38px' }}>
            Ask
          </button>
        </form>
      </div>

      {/* Right Pane: Context & Citations (Notion/Linear panel style) */}
      <div style={{
        width: '320px',
        backgroundColor: 'var(--bg-app)',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        overflowY: 'auto'
      }}>
        <div>
          <h2 style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase', marginBottom: '12px' }}>
            Verifiable Context Sources
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Citations extracted from official Secretary of State guidelines matching current chat context:
          </p>
        </div>

        {/* Citation Cards */}
        <div style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--accent-blue)', marginBottom: '4px' }}>
            Delaware General Corp Law (DGCL)
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-primary)', fontWeight: '500', marginBottom: '6px' }}>
            Section 101 — Filing & Fees
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            "The Certificate of Formation must be delivered to the office of the Secretary of State along with the statutory filing fee ($90)."
          </div>
        </div>

        <div style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--accent-blue)', marginBottom: '4px' }}>
            Wyoming Statutes
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-primary)', fontWeight: '500', marginBottom: '6px' }}>
            W.S. 17-29-201 — LLC Creation
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            "One or more persons may act as organizer to form a limited liability company by signing and delivering articles of organization to the Secretary of State."
          </div>
        </div>
      </div>
    </div>
  );
}
