import { useState } from 'react';
import { Mail, AlertTriangle, CheckCircle, Shield } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';

export default function EmailHeaderAnalyzer() {
  const [headers, setHeaders] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const analyzeHeaders = async () => {
    if (!headers.trim()) {
      alert('Please enter email headers');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await invokeEdgeFunction('analyze-email-header', { headers });

      if (error) throw error;
      setResult(data.data);
    } catch (error: any) {
      console.error('Analysis error:', error);
      alert('Analysis failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getThreatColor = (score: number) => {
    if (score >= 75) return 'text-threat-critical';
    if (score >= 50) return 'text-threat-warning';
    return 'text-threat-safe';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h2 font-semibold mb-2">Email Header Analyzer</h2>
        <p className="text-text-secondary">
          Analyze email headers for authentication, routing anomalies, and spoofing indicators
        </p>
      </div>

      {/* Input Section */}
      <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
        <label className="block text-sm font-medium text-text-secondary mb-2">
          Paste Email Headers
        </label>
        <textarea
          value={headers}
          onChange={(e) => setHeaders(e.target.value)}
          placeholder="Paste full email headers here..."
          className="w-full h-64 bg-bg-near-black border border-border-subtle rounded-md p-4 text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary resize-none"
        />
        <button
          onClick={analyzeHeaders}
          disabled={loading}
          className="mt-4 px-8 py-3 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Analyzing...' : 'Analyze Headers'}
        </button>
      </div>

      {/* Results Section */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          {/* Threat Score Card */}
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Threat Score</h3>
                <p className={`text-6xl font-bold ${getThreatColor(result.threatScore)}`}>
                  {result.threatScore}
                </p>
                <p className="text-text-secondary mt-2">out of 100</p>
              </div>
              <Shield className={`w-24 h-24 ${getThreatColor(result.threatScore)}`} />
            </div>
          </div>

          {/* Authentication Results */}
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4">Authentication Results</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-bg-near-black rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  {result.spf.status === 'pass' ? (
                    <CheckCircle className="w-5 h-5 text-threat-safe" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-threat-warning" />
                  )}
                  <span className="font-semibold">SPF</span>
                </div>
                <p className="text-sm text-text-secondary capitalize">{result.spf.status}</p>
              </div>
              <div className="p-4 bg-bg-near-black rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  {result.dkim.status === 'pass' ? (
                    <CheckCircle className="w-5 h-5 text-threat-safe" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-threat-warning" />
                  )}
                  <span className="font-semibold">DKIM</span>
                </div>
                <p className="text-sm text-text-secondary capitalize">{result.dkim.status}</p>
              </div>
              <div className="p-4 bg-bg-near-black rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  {result.dmarc.status === 'pass' ? (
                    <CheckCircle className="w-5 h-5 text-threat-safe" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-threat-warning" />
                  )}
                  <span className="font-semibold">DMARC</span>
                </div>
                <p className="text-sm text-text-secondary capitalize">{result.dmarc.status}</p>
              </div>
            </div>
          </div>

          {/* Header Details */}
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4">Email Details</h3>
            <div className="space-y-3">
              <div>
                <span className="text-text-secondary text-sm">From:</span>
                <p className="text-text-primary font-mono text-sm mt-1">{result.from}</p>
              </div>
              <div>
                <span className="text-text-secondary text-sm">To:</span>
                <p className="text-text-primary font-mono text-sm mt-1">{result.to}</p>
              </div>
              <div>
                <span className="text-text-secondary text-sm">Subject:</span>
                <p className="text-text-primary font-mono text-sm mt-1">{result.subject}</p>
              </div>
              <div>
                <span className="text-text-secondary text-sm">Return-Path:</span>
                <p className="text-text-primary font-mono text-sm mt-1">{result.returnPath}</p>
              </div>
            </div>
          </div>

          {/* Anomalies */}
          {result.anomalies && result.anomalies.length > 0 && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-threat-warning" />
                Anomalies Detected
              </h3>
              <ul className="space-y-2">
                {result.anomalies.map((anomaly: string, idx: number) => (
                  <li key={idx} className="text-text-secondary text-sm flex items-start gap-2">
                    <span className="text-threat-warning mt-1">•</span>
                    <span>{anomaly}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Routing Timeline */}
          {result.receivedHops && result.receivedHops.length > 0 && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">Routing Timeline</h3>
              <div className="space-y-4">
                {result.receivedHops.map((hop: any, idx: number) => (
                  <div key={idx} className="flex gap-4 pb-4 border-b border-border-subtle last:border-0">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-white text-sm font-semibold">
                      {idx + 1}
                    </div>
                    <div className="flex-grow">
                      <p className="text-text-primary font-mono text-sm">{hop.server}</p>
                      {hop.ip && (
                        <p className="text-text-secondary text-sm mt-1">IP: {hop.ip}</p>
                      )}
                      <p className="text-text-tertiary text-xs mt-1">{hop.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
