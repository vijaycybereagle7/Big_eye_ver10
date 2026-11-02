import { useState } from 'react';
import { Globe, Server, Lock, AlertTriangle, CheckCircle } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';
import { ReputationGauge } from './ReputationGauge';
import { ValidationBadges } from './ValidationBadges';

export default function DomainChecker() {
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const checkDomain = async () => {
    if (!domain.trim()) {
      alert('Please enter a domain');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await invokeEdgeFunction('check-domain', { domain });

      if (error) throw error;
      setResult(data.data);
    } catch (error: any) {
      console.error('Check error:', error);
      alert('Check failed: ' + error.message);
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
        <h2 className="text-h2 font-semibold mb-2">Domain Checker</h2>
        <p className="text-text-secondary">
          Comprehensive domain analysis including DNS, SSL, and authentication records
        </p>
      </div>

      <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
        <label className="block text-sm font-medium text-text-secondary mb-2">
          Domain Name
        </label>
        <div className="flex gap-4">
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="example.com"
            className="flex-grow bg-bg-near-black border border-border-subtle rounded-md px-4 py-3 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
          />
          <button
            onClick={checkDomain}
            disabled={loading}
            className="px-8 py-3 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            {loading ? 'Checking...' : 'Check Domain'}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold mb-2">Overall Threat Score</h3>
                <p className={`text-6xl font-bold ${getThreatColor(result.overallThreatScore)}`}>
                  {result.overallThreatScore}
                </p>
                <p className="text-text-secondary mt-2 capitalize">Risk Level: {result.riskLevel}</p>
                
                {result.validated_by && result.validated_by.length > 0 && (
                  <ValidationBadges validated_by={result.validated_by} details={result.validationDetails} />
                )}
              </div>
              <div className="flex items-center gap-6">
                {result.reputation_score !== undefined && (
                  <ReputationGauge score={result.reputation_score} size={100} label="Domain Reputation" />
                )}
                <Globe className={`w-24 h-24 ${getThreatColor(result.overallThreatScore)}`} />
              </div>
            </div>
          </div>

          {result.dns && !result.dns.error && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">DNS Configuration</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  {result.dns.hasARecord ? (
                    <CheckCircle className="w-5 h-5 text-threat-safe" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-threat-critical" />
                  )}
                  <span>A Record: {result.dns.hasARecord ? 'Present' : 'Missing'}</span>
                </div>
                <div className="flex items-center gap-2">
                  {result.dns.hasMXRecord ? (
                    <CheckCircle className="w-5 h-5 text-threat-safe" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-threat-critical" />
                  )}
                  <span>MX Record: {result.dns.hasMXRecord ? 'Present' : 'Missing'}</span>
                </div>
                <div className="flex items-center gap-2">
                  {result.dns.hasSPF ? (
                    <CheckCircle className="w-5 h-5 text-threat-safe" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-threat-warning" />
                  )}
                  <span>SPF Record: {result.dns.hasSPF ? 'Present' : 'Missing'}</span>
                </div>
                <div className="flex items-center gap-2">
                  {result.dns.hasDMARC ? (
                    <CheckCircle className="w-5 h-5 text-threat-safe" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-threat-warning" />
                  )}
                  <span>DMARC Record: {result.dns.hasDMARC ? 'Present' : 'Missing'}</span>
                </div>
              </div>
            </div>
          )}

          {result.ssl && !result.ssl.error && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Lock className="w-5 h-5" />
                SSL/TLS Status
              </h3>
              <p className={`text-sm ${result.ssl.hasSSL ? 'text-threat-safe' : 'text-threat-critical'}`}>
                {result.ssl.message}
              </p>
            </div>
          )}

          {result.recommendations && result.recommendations.length > 0 && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
              <ul className="space-y-2">
                {result.recommendations.map((rec: string, idx: number) => (
                  <li key={idx} className="text-text-secondary text-sm flex items-start gap-2">
                    <span className="text-accent-primary mt-1">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
