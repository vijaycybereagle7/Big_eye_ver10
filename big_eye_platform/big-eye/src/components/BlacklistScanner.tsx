import { useState } from 'react';
import { Shield, AlertTriangle } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';

export default function BlacklistScanner() {
  const [ip, setIp] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const scanBlacklist = async () => {
    if (!ip.trim()) {
      setError('Please enter an IP address');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    
    try {
      const { data, error: invokeError } = await invokeEdgeFunction('scan-blacklist', { ip: ip.trim() });

      if (invokeError) {
        throw new Error(invokeError.message || 'Failed to scan IP');
      }

      if (!data || !data.data) {
        throw new Error('Invalid response from server');
      }

      setResult(data.data);
    } catch (err: any) {
      console.error('Blacklist scan error:', err);
      setError(err.message || 'An error occurred while scanning');
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
        <h2 className="text-h2 font-semibold mb-2">Blacklist Scanner</h2>
        <p className="text-text-secondary">
          Check IP addresses against blacklist databases and reputation systems
        </p>
      </div>

      <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
        <label className="block text-sm font-medium text-text-secondary mb-2">
          IP Address
        </label>
        <div className="flex gap-4">
          <input
            type="text"
            value={ip}
            onChange={(e) => setIp(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && scanBlacklist()}
            placeholder="8.8.8.8"
            className="flex-grow bg-bg-near-black border border-border-subtle rounded-md px-4 py-3 text-text-primary font-mono focus:outline-none focus:ring-2 focus:ring-accent-primary"
          />
          <button
            onClick={scanBlacklist}
            disabled={loading}
            className="px-8 py-3 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Scanning...' : 'Scan IP'}
          </button>
        </div>
        {error && (
          <p className="mt-2 text-sm text-threat-critical">{error}</p>
        )}
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          {/* Threat Score Card */}
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Threat Score</h3>
                <p className={`text-6xl font-bold ${getThreatColor(result.overallThreatScore || 0)}`}>
                  {result.overallThreatScore ?? 0}
                </p>
                <p className="text-text-secondary mt-2 capitalize">
                  Risk: {result.riskLevel || 'unknown'}
                </p>
                {result.blacklisted && (
                  <p className="text-threat-critical mt-2 font-semibold">BLACKLISTED</p>
                )}
              </div>
              <Shield className={`w-24 h-24 ${getThreatColor(result.overallThreatScore || 0)}`} />
            </div>
          </div>

          {/* Basic Checks */}
          {result.basicChecks && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">Basic IP Analysis</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">IP Address:</span>
                  <span className="text-text-primary font-mono">{result.basicChecks.ip}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Type:</span>
                  <span className="text-text-primary">
                    {result.basicChecks.isPublic ? 'Public' : result.basicChecks.isPrivate ? 'Private' : 'Reserved'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Threat Score:</span>
                  <span className={getThreatColor(result.basicChecks.threatScore || 0)}>
                    {result.basicChecks.threatScore || 0}
                  </span>
                </div>
              </div>
              {result.basicChecks.note && (
                <p className="mt-4 text-sm text-text-tertiary">{result.basicChecks.note}</p>
              )}
            </div>
          )}

          {/* AbuseIPDB Report */}
          {result.abuseIPDB && result.abuseIPDB.available && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">AbuseIPDB Report</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-text-secondary">Country</p>
                  <p className="text-text-primary font-semibold">
                    {result.abuseIPDB.countryName || 'Unknown'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">ISP</p>
                  <p className="text-text-primary font-semibold">
                    {result.abuseIPDB.isp || 'Unknown'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Total Reports</p>
                  <p className="text-text-primary font-semibold">
                    {result.abuseIPDB.totalReports || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Abuse Confidence</p>
                  <p className={`font-semibold ${getThreatColor(result.abuseIPDB.abuseConfidenceScore || 0)}`}>
                    {result.abuseIPDB.abuseConfidenceScore || 0}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* AbuseIPDB Not Available */}
          {result.abuseIPDB && !result.abuseIPDB.available && (
            <div className="bg-bg-hover-surface p-6 rounded-lg border border-border-subtle">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-threat-warning flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-text-secondary mb-2">
                    {result.abuseIPDB.message || 'AbuseIPDB API not configured'}
                  </p>
                  {result.abuseIPDB.configureInstructions && (
                    <p className="text-xs text-text-tertiary">
                      {result.abuseIPDB.configureInstructions}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Recommendation */}
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4">Recommendation</h3>
            <p className="text-text-secondary">{result.recommendation || 'No recommendation available'}</p>
          </div>
        </div>
      )}
    </div>
  );
}
