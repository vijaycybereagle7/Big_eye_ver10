import { useState } from 'react';
import { Calendar, Globe, AlertTriangle } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';

export default function DomainAgeTracker() {
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const checkDomainAge = async () => {
    if (!domain.trim()) {
      alert('Please enter a domain');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await invokeEdgeFunction('get-domain-age', { domain });

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
        <h2 className="text-h2 font-semibold mb-2">Domain Age Tracker</h2>
        <p className="text-text-secondary">
          Analyze domain registration age and identify newly created suspicious domains
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
            onClick={checkDomainAge}
            disabled={loading}
            className="px-8 py-3 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            {loading ? 'Checking...' : 'Check Age'}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold mb-2">Domain Age</h3>
                <p className="text-5xl font-bold text-accent-primary">
                  {result.ageDescription || 'Unknown'}
                </p>
                <p className="text-text-secondary mt-2">
                  {result.ageInDays !== null ? `${result.ageInDays} days` : 'Age unavailable'}
                </p>
              </div>
              <Calendar className="w-24 h-24 text-accent-primary" />
            </div>
          </div>

          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Threat Score</h3>
              <p className={`text-4xl font-bold ${
                result.threatScore >= 75 ? 'text-threat-critical' : 
                result.threatScore >= 50 ? 'text-threat-warning' : 
                'text-threat-safe'
              }`}>
                {result.threatScore}
              </p>
            </div>
            <div className={`p-4 rounded-md ${
              result.riskLevel === 'critical' ? 'bg-threat-critical/20 border border-threat-critical' : 
              result.riskLevel === 'high' ? 'bg-threat-warning/20 border border-threat-warning' : 
              'bg-threat-safe/20 border border-threat-safe'
            }`}>
              <p className="font-semibold capitalize">{result.riskLevel} Risk</p>
              <p className="text-sm mt-1">{result.riskReason}</p>
            </div>
          </div>

          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Globe className="w-5 h-5" />
              Registration Details
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-text-secondary">Domain</p>
                <p className="text-text-primary font-mono">{result.domain}</p>
              </div>
              {result.createdDate && (
                <div>
                  <p className="text-sm text-text-secondary">Created Date</p>
                  <p className="text-text-primary">{new Date(result.createdDate).toLocaleDateString()}</p>
                </div>
              )}
              {result.expiresDate && (
                <div>
                  <p className="text-sm text-text-secondary">Expires Date</p>
                  <p className="text-text-primary">{new Date(result.expiresDate).toLocaleDateString()}</p>
                </div>
              )}
              {result.registrar && (
                <div>
                  <p className="text-sm text-text-secondary">Registrar</p>
                  <p className="text-text-primary">{result.registrar}</p>
                </div>
              )}
              {result.dataSource && (
                <div>
                  <p className="text-sm text-text-secondary">Data Source</p>
                  <p className="text-text-tertiary text-sm">{result.dataSource}</p>
                </div>
              )}
            </div>
          </div>

          {result.ageInDays !== null && result.ageInDays < 180 && (
            <div className="bg-threat-warning/10 p-6 rounded-lg border border-threat-warning">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-threat-warning flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-threat-warning mb-1">Warning: Recently Registered Domain</p>
                  <p className="text-sm text-text-secondary">
                    Domains less than 6 months old are often used for phishing campaigns. Exercise extreme caution when interacting with emails from this domain.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
