import { useState } from 'react';
import { Mail, AlertTriangle, CheckCircle } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';

export default function TempEmailDetector() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const detectTempEmail = async () => {
    if (!email.trim()) {
      alert('Please enter an email address');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await invokeEdgeFunction('detect-temp-email', { email });

      if (error) throw error;
      setResult(data.data);
    } catch (error: any) {
      console.error('Detection error:', error);
      alert('Detection failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h2 font-semibold mb-2">Temporary Email Detector</h2>
        <p className="text-text-secondary">
          Identify disposable and temporary email addresses
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
            onClick={detectTempEmail}
            disabled={loading}
            className="px-8 py-3 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            {loading ? 'Checking...' : 'Check Email'}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Detection Result</h3>
                <div className="flex items-center gap-3 mt-4">
                  {result.isTemporary ? (
                    <AlertTriangle className="w-16 h-16 text-threat-critical" />
                  ) : (
                    <CheckCircle className="w-16 h-16 text-threat-safe" />
                  )}
                  <div>
                    <p className={`text-2xl font-bold ${result.isTemporary ? 'text-threat-critical' : 'text-threat-safe'}`}>
                      {result.isTemporary ? 'TEMPORARY EMAIL' : 'LEGITIMATE EMAIL'}
                    </p>
                    <p className="text-text-secondary mt-1 capitalize">Risk: {result.riskLevel}</p>
                  </div>
                </div>
              </div>
              <Mail className={`w-24 h-24 ${result.isTemporary ? 'text-threat-critical' : 'text-threat-safe'}`} />
            </div>
          </div>

          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4">Email Details</h3>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-text-secondary">Email</p>
                <p className="text-text-primary font-mono">{result.email}</p>
              </div>
              <div>
                <p className="text-sm text-text-secondary">Domain</p>
                <p className="text-text-primary font-mono">{result.domain}</p>
              </div>
              <div>
                <p className="text-sm text-text-secondary">Confidence</p>
                <p className="text-text-primary">{result.confidence}%</p>
              </div>
              <div className="flex gap-2 mt-4">
                <div className={`px-3 py-1 rounded text-sm ${result.isTemporary ? 'bg-threat-critical/20 text-threat-critical' : 'bg-threat-safe/20 text-threat-safe'}`}>
                  {result.isTemporary ? 'Disposable' : 'Not Disposable'}
                </div>
                {result.isFreemail && (
                  <div className="px-3 py-1 rounded text-sm bg-threat-warning/20 text-threat-warning">
                    Free Email Provider
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4">Recommendation</h3>
            <p className="text-text-secondary">{result.recommendation}</p>
          </div>

          {result.sources && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">Detection Sources</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {result.sources.localDatabase ? (
                    <CheckCircle className="w-4 h-4 text-threat-safe" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-border-moderate" />
                  )}
                  <span className="text-sm text-text-secondary">Local Database</span>
                </div>
                {result.sources.externalAPI && (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-threat-safe" />
                    <span className="text-sm text-text-secondary">External API ({result.sources.externalAPI.service})</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
