import React, { useState } from 'react';

export default function WizardView({ entityProgress, onProgressUpdate, onViewChange }) {
  const [step, setStep] = useState(entityProgress === 100 ? 4 : entityProgress === 50 ? 2 : 1);
  const [formData, setFormData] = useState({
    businessName: '',
    entityType: 'LLC',
    state: 'Delaware',
    shareCount: '10000000',
    founderEmail: 'vasudev@example.com'
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleNext = () => {
    if (step === 1) {
      setStep(2);
      onProgressUpdate(25);
    } else if (step === 2) {
      setStep(3);
      onProgressUpdate(50);
    } else if (step === 3) {
      setStep(4);
      onProgressUpdate(100);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(prev => prev - 1);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div>
            <h2 style={{ marginBottom: '16px' }}>Step 1: Entity Details</h2>
            <div className="form-group">
              <label className="form-label">Desired Business Name</label>
              <input
                type="text"
                name="businessName"
                value={formData.businessName}
                onChange={handleInputChange}
                className="form-input"
                placeholder="e.g. Acme Tech"
              />
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                We will check availability of this name with the state registry.
              </p>
            </div>
            <div className="form-group">
              <label className="form-label">Entity Type</label>
              <select
                name="entityType"
                value={formData.entityType}
                onChange={handleInputChange}
                className="form-input"
                style={{ height: '36px' }}
              >
                <option value="LLC">Limited Liability Company (LLC)</option>
                <option value="C-Corp">C-Corporation (Slightly more complex setup)</option>
              </select>
            </div>
          </div>
        );
      case 2:
        return (
          <div>
            <h2 style={{ marginBottom: '16px' }}>Step 2: State Jurisdiction</h2>
            <div className="form-group">
              <label className="form-label">Incorporation State</label>
              <select
                name="state"
                value={formData.state}
                onChange={handleInputChange}
                className="form-input"
                style={{ height: '36px' }}
              >
                <option value="Delaware">Delaware (Best for venture-backed startups)</option>
                <option value="Wyoming">Wyoming (Low cost, high privacy)</option>
                <option value="Texas">Texas (No state income tax, solid business courts)</option>
              </select>
            </div>
            {formData.entityType === 'C-Corp' && (
              <div className="form-group">
                <label className="form-label">Authorized Shares</label>
                <input
                  type="number"
                  name="shareCount"
                  value={formData.shareCount}
                  onChange={handleInputChange}
                  className="form-input"
                />
              </div>
            )}
          </div>
        );
      case 3:
        return (
          <div>
            <h2 style={{ marginBottom: '16px' }}>Step 3: Founders & Officers</h2>
            <div className="form-group">
              <label className="form-label">Primary Founder Email</label>
              <input
                type="email"
                name="founderEmail"
                value={formData.founderEmail}
                onChange={handleInputChange}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Physical Business Address</label>
              <input
                type="text"
                className="form-input"
                placeholder="123 Startup Way, Suite 100"
                disabled
              />
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                Note: Sandbox environment uses our standard Delaware/Wyoming Registered Agent addresses automatically.
              </p>
            </div>
          </div>
        );
      case 4:
        return (
          <div style={{ textAlign: 'center', padding: '32px 0' }}>
            <span style={{ fontSize: '48px' }}>🎉</span>
            <h2 style={{ margin: '16px 0 8px 0' }}>Filing Prepared Successfully!</h2>
            <p style={{ maxWidth: '400px', margin: '0 auto 24px auto' }}>
              Your entity paperwork has been synthesized. You can now download the ready-to-file documents from the Documents Vault.
            </p>
            <button
              onClick={() => onViewChange('documents')}
              className="btn btn-primary"
            >
              Go to Documents Vault
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto', padding: '16px 0' }}>
      {/* Wizard Headline */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ marginBottom: '8px' }}>Business Registration Wizard</h1>
        <p>Draft state-compliant incorporation filings through our guided interactive interface.</p>
      </div>

      {/* Stripe-style Form Panel */}
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-sm)',
        padding: '32px',
        marginBottom: '24px'
      }}>
        {/* Step Indicator Header */}
        {step < 4 && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '32px',
            fontSize: '12px',
            fontWeight: '600',
            color: 'var(--text-muted)'
          }}>
            <span>STEP {step} OF 3</span>
            <span>{Math.round(((step - 1) / 3) * 100)}% COMPLETE</span>
          </div>
        )}

        {renderStep()}

        {/* Action button bar */}
        {step < 4 && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '32px',
            paddingTop: '20px',
            borderTop: '1px solid var(--border-color)'
          }}>
            <button
              onClick={handleBack}
              disabled={step === 1}
              className="btn"
              style={{ visibility: step === 1 ? 'hidden' : 'visible' }}
            >
              Back
            </button>
            <button
              onClick={handleNext}
              className="btn btn-primary"
            >
              {step === 3 ? 'Generate Filing' : 'Continue'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
