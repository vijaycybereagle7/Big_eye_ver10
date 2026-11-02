import { useState } from 'react';
import { Mail, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';

export default function EmailLegitimacyChecker() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const checkEmail = async () => {
    if (!email.trim()) {
      alert('Please enter an email address');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await invokeEdgeFunction('check-email-legitimacy', { email });

      if (error) throw error;
      setResult(data.data);
    } catch (error: any) {
      console.error('Check error:', error);
      alert('Check failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h2 font-semibold mb-2">Email Legitimacy Checker</h2>
        <p className="text-text-secondary">
          Validate email syntax, deliverability, and detect disposable addresses
        </p>
      </div>

      <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
        <label className="block text-sm font-medium text-text-secondary mb-2">
          Email Address
        </label>
        <div className="flex gap-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            className="flex-grow bg-bg-near-black border border-border-subtle rounded-md px-4 py-3 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
          />
          <button
            onClick={checkEmail}
            disabled={loading}
            className="px-8 py-3 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            {loading ? 'Checking...' : 'Validate Email'}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Threat Score</h3>
                <p className={`text-6xl font-bold ${
                  result.threatScore >= 60 ? 'text-threat-critical' : 
                  result.threatScore >= 30 ? 'text-threat-warning' : 
                  'text-threat-safe'
                }`}>
                  {result.threatScore}
                </p>
                <p className="text-text-secondary mt-2 capitalize">Risk: {result.riskLevel}</p>
              </div>
              <Mail className={`w-24 h-24 ${
                result.threatScore >= 60 ? 'text-threat-critical' : 
                result.threatScore >= 30 ? 'text-threat-warning' : 
                'text-threat-safe'
              }`} />
            </div>
          </div>

          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4">Validation Checks</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                {result.syntaxValid ? (
                  <CheckCircle className="w-5 h-5 text-threat-safe" />
                ) : (
                  <XCircle className="w-5 h-5 text-threat-critical" />
                )}
                <span>Syntax Valid: {result.syntaxValid ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex items-center gap-3">
                {result.hasMXRecord ? (
                  <CheckCircle className="w-5 h-5 text-threat-safe" />
                ) : (
                  <XCircle className="w-5 h-5 text-threat-critical" />
                )}
                <span>MX Record: {result.hasMXRecord === null ? 'Not checked' : result.hasMXRecord ? 'Present' : 'Missing'}</span>
              </div>
              <div className="flex items-center gap-3">
                {!result.disposable ? (
                  <CheckCircle className="w-5 h-5 text-threat-safe" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-threat-critical" />
                )}
                <span>Disposable: {result.disposable ? 'Yes (Risky)' : 'No'}</span>
              </div>
              <div className="flex items-center gap-3">
                {result.deliverable ? (
                  <CheckCircle className="w-5 h-5 text-threat-safe" />
                ) : (
                  <XCircle className="w-5 h-5 text-threat-warning" />
                )}
                <span>Deliverable: {result.deliverable === null ? 'Not checked' : result.deliverable ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>

          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4">Recommendation</h3>
            <p className="text-text-secondary">{result.recommendation}</p>
          </div>

          {result.externalValidation && !result.externalValidation.available && (
            <div className="bg-bg-hover-surface p-6 rounded-lg border border-border-subtle">
              <p className="text-sm text-text-tertiary">
                {result.externalValidation.message}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
