import React, { useState } from 'react';
import { generateCompliancePlan } from '../api/compliance';

export default function WizardView({
  entityProgress,
  onProgressUpdate,
  onViewChange,
  compliancePlan,
  setCompliancePlan
}) {
  const [step, setStep] = useState(entityProgress === 100 ? 4 : entityProgress === 50 ? 2 : 1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
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

  const generatePlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const stateMapping = {
        'Delaware': 'DE',
        'Wyoming': 'WY',
        'Texas': 'TX'
      };

      const payload = {
        business_type: formData.entityType,
        state: stateMapping[formData.state] || formData.state,
        industry: 'General Business',
        employees: 5,
        annual_revenue: 200000.0,
        ownership_type: formData.entityType,
        is_foreign_owner: false,
        is_home_based: false,
        additional_attributes: {
          businessName: formData.businessName,
          shareCount: formData.shareCount,
          founderEmail: formData.founderEmail
        }
      };

      const plan = await generateCompliancePlan(payload);
      setCompliancePlan(plan);
      setStep(4);
      onProgressUpdate(100);
    } catch (err) {
      setError(err?.message || 'An error occurred while calling the Compliance Engine.');
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (step === 1) {
      setStep(2);
      onProgressUpdate(25);
    } else if (step === 2) {
      setStep(3);
      onProgressUpdate(50);
    } else if (step === 3) {
      generatePlan();
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(prev => prev - 1);
    }
  };

  const renderStep = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '48px 0' }}>
          <div className="spinner" style={{
            width: '40px',
            height: '40px',
            border: '4px solid var(--border-color)',
            borderTop: '4px solid var(--accent-blue)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px auto'
          }} />
          <h3 style={{ fontWeight: 500 }}>Generating Compliance Plan...</h3>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Consulting Rule engines and constructing topological workflow paths.
          </p>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      );
    }

    if (error) {
      return (
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          <span style={{ fontSize: '36px', display: 'block', marginBottom: '8px' }}>⚠️</span>
          <h3 style={{ marginBottom: '8px', fontWeight: 600, color: '#ef4444' }}>Generation Failed</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>{error}</p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button onClick={() => setError(null)} className="btn">
              Go Back
            </button>
            <button onClick={generatePlan} className="btn btn-primary">
              Retry Generation
            </button>
          </div>
        </div>
      );
    }

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
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <span style={{ fontSize: '48px' }}>🎉</span>
              <h2 style={{ margin: '16px 0 8px 0' }}>Filing Prepared Successfully!</h2>
              <p style={{ maxWidth: '400px', margin: '0 auto' }}>
                Your compliance plan and registration workflow have been synthesized.
              </p>
            </div>

            {compliancePlan && (
              <div style={{
                backgroundColor: 'var(--bg-app)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                padding: '16px',
                textAlign: 'left'
              }}>
                <h3 style={{ fontSize: '13px', fontWeight: '600', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '6px' }}>
                  SYNTHESIZED PLAN SUMMARY
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                  <div><strong>Company Name:</strong> {formData.businessName || 'Civora LLC'}</div>
                  <div><strong>Jurisdiction:</strong> {formData.state} (State code: {compliancePlan.profile.state})</div>
                  <div><strong>Entity Type:</strong> {formData.entityType}</div>
                  <div><strong>Standing Status:</strong> <span className="badge badge-success">{compliancePlan.eligibility_result.status}</span></div>
                  <div><strong>Generated Steps:</strong> {Object.keys(compliancePlan.workflow_result.steps).length} tasks matched</div>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                onClick={() => onViewChange('dashboard')}
                className="btn"
              >
                Go to Dashboard
              </button>
              <button
                onClick={() => onViewChange('documents')}
                className="btn btn-primary"
              >
                Go to Documents Hub
              </button>
            </div>
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
        {step < 4 && !loading && !error && (
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
        {step < 4 && !loading && !error && (
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
