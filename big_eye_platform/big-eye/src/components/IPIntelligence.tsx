import { useState } from 'react';
import { MapPin, Server } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';
import { ReputationGauge } from './ReputationGauge';
import { ValidationBadges } from './ValidationBadges';

export default function IPIntelligence() {
  const [ip, setIp] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const checkIP = async () => {
    if (!ip.trim()) {
      alert('Please enter an IP address');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await invokeEdgeFunction('check-ip-reputation', { ip });

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
        <h2 className="text-h2 font-semibold mb-2">IP Intelligence Dashboard</h2>
        <p className="text-text-secondary">
          Comprehensive IP analysis including geolocation, ISP, and network information
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
            placeholder="8.8.8.8"
            className="flex-grow bg-bg-near-black border border-border-subtle rounded-md px-4 py-3 text-text-primary font-mono focus:outline-none focus:ring-2 focus:ring-accent-primary"
          />
          <button
            onClick={checkIP}
            disabled={loading}
            className="px-8 py-3 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Analyze IP'}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold mb-2">Threat Score</h3>
                <p className={`text-6xl font-bold ${
                  result.threatScore >= 75 ? 'text-threat-critical' : 
                  result.threatScore >= 50 ? 'text-threat-warning' : 
                  'text-threat-safe'
                }`}>
                  {result.threatScore}
                </p>
                <p className="text-text-secondary mt-2 capitalize">Risk: {result.riskLevel}</p>
                
                {result.validated_by && result.validated_by.length > 0 && (
                  <ValidationBadges validated_by={result.validated_by} details={result.validationDetails} />
                )}
              </div>
              <div className="flex items-center gap-6">
                {result.reputation_score !== undefined && (
                  <ReputationGauge score={result.reputation_score} size={100} label="IP Reputation" />
                )}
                <MapPin className={`w-24 h-24 ${
                  result.threatScore >= 75 ? 'text-threat-critical' : 
                  result.threatScore >= 50 ? 'text-threat-warning' : 
                  'text-threat-safe'
                }`} />
              </div>
            </div>
          </div>

          {result.geolocation && !result.geolocation.error && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">Geolocation</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-text-secondary">Country</p>
                  <p className="text-text-primary font-semibold">
                    {result.geolocation.country} ({result.geolocation.countryCode})
                  </p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Region</p>
                  <p className="text-text-primary font-semibold">{result.geolocation.region}</p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">City</p>
                  <p className="text-text-primary font-semibold">{result.geolocation.city}</p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Timezone</p>
                  <p className="text-text-primary font-semibold">{result.geolocation.timezone}</p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">ISP</p>
                  <p className="text-text-primary font-semibold">{result.geolocation.isp}</p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">ASN</p>
                  <p className="text-text-primary font-mono text-sm">{result.geolocation.asn}</p>
                </div>
              </div>
            </div>
          )}

          {result.whois && !result.whois.error && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Server className="w-5 h-5" />
                Network Information
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-text-secondary">Organization</p>
                  <p className="text-text-primary">{result.whois.organization}</p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Type</p>
                  <p className="text-text-primary capitalize">{result.whois.type}</p>
                </div>
                <div className="flex gap-4">
                  <div className={`px-3 py-1 rounded ${result.whois.isHosting ? 'bg-threat-warning/20 text-threat-warning' : 'bg-bg-hover-surface text-text-tertiary'}`}>
                    {result.whois.isHosting ? 'Hosting Provider' : 'Not Hosting'}
                  </div>
                  <div className={`px-3 py-1 rounded ${result.whois.isVPN ? 'bg-threat-warning/20 text-threat-warning' : 'bg-bg-hover-surface text-text-tertiary'}`}>
                    {result.whois.isVPN ? 'VPN/Proxy' : 'Not VPN'}
                  </div>
                  <div className={`px-3 py-1 rounded ${result.whois.isTor ? 'bg-threat-critical/20 text-threat-critical' : 'bg-bg-hover-surface text-text-tertiary'}`}>
                    {result.whois.isTor ? 'Tor Exit Node' : 'Not Tor'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {result.recommendations && result.recommendations.length > 0 && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">Analysis</h3>
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
