import { useState } from 'react';
import { Brain, AlertTriangle } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';
import { ReputationGauge } from './ReputationGauge';
import { ValidationBadges } from './ValidationBadges';

export default function PhishingProbability() {
  const [formData, setFormData] = useState({
    email: '',
    subject: '',
    senderName: '',
    body: '',
    domain: '',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const analyzePhishing = async () => {
    if (!formData.email && !formData.subject && !formData.body) {
      alert('Please provide at least one input field');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await invokeEdgeFunction('analyze-phishing-probability', formData);

      if (error) throw error;
      setResult(data.data);
    } catch (error: any) {
      console.error('Analysis error:', error);
      alert('Analysis failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-h2 font-semibold mb-2">AI-Powered Phishing Probability Engine</h2>
        <p className="text-text-secondary">
          Advanced AI analysis combining multiple signals for comprehensive phishing detection
        </p>
      </div>

      <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Sender Email
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="sender@example.com"
              className="w-full bg-bg-near-black border border-border-subtle rounded-md px-4 py-3 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Subject Line
            </label>
            <input
              type="text"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              placeholder="Email subject"
              className="w-full bg-bg-near-black border border-border-subtle rounded-md px-4 py-3 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Sender Name
            </label>
            <input
              type="text"
              value={formData.senderName}
              onChange={(e) => setFormData({ ...formData, senderName: e.target.value })}
              placeholder="John Doe"
              className="w-full bg-bg-near-black border border-border-subtle rounded-md px-4 py-3 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Email Body (Optional)
            </label>
            <textarea
              value={formData.body}
              onChange={(e) => setFormData({ ...formData, body: e.target.value })}
              placeholder="Email content..."
              rows={6}
              className="w-full bg-bg-near-black border border-border-subtle rounded-md p-4 text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary resize-none"
            />
          </div>
          <button
            onClick={analyzePhishing}
            disabled={loading}
            className="w-full px-8 py-3 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Analyze Phishing Probability'}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold mb-2">Phishing Probability</h3>
                <p className={`text-6xl font-bold ${
                  result.phishingScore >= 75 ? 'text-threat-critical' : 
                  result.phishingScore >= 50 ? 'text-threat-warning' : 
                  'text-threat-safe'
                }`}>
                  {result.phishingScore}%
                </p>
                <p className="text-text-secondary mt-2 capitalize">Risk: {result.riskLevel}</p>
                <p className="text-text-tertiary text-sm mt-1">Confidence: {result.confidence}%</p>
                
                {result.validated_by && result.validated_by.length > 0 && (
                  <ValidationBadges validated_by={result.validated_by} details={result.validationDetails} />
                )}
              </div>
              <div className="flex items-center gap-6">
                {result.reputation_score !== undefined && (
                  <ReputationGauge score={result.reputation_score} size={100} label="Reputation" />
                )}
                <Brain className={`w-24 h-24 ${
                  result.phishingScore >= 75 ? 'text-threat-critical' : 
                  result.phishingScore >= 50 ? 'text-threat-warning' : 
                  'text-threat-safe'
                }`} />
              </div>
            </div>
          </div>

          <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
            <h3 className="text-lg font-semibold mb-4">Recommendation</h3>
            <div className={`p-4 rounded-md ${
              result.phishingScore >= 75 ? 'bg-threat-critical/20 border border-threat-critical' : 
              result.phishingScore >= 50 ? 'bg-threat-warning/20 border border-threat-warning' : 
              'bg-threat-safe/20 border border-threat-safe'
            }`}>
              <p className="font-semibold">{result.recommendation}</p>
            </div>
          </div>

          {result.redFlags && result.redFlags.length > 0 && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-threat-warning" />
                Red Flags Detected
              </h3>
              <ul className="space-y-2">
                {result.redFlags.map((flag: string, idx: number) => (
                  <li key={idx} className="text-text-secondary text-sm flex items-start gap-2">
                    <span className="text-threat-warning mt-1">•</span>
                    <span>{flag}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.reasoning && result.reasoning.length > 0 && (
            <div className="bg-bg-dark-surface p-8 rounded-lg border border-border-subtle shadow-card">
              <h3 className="text-lg font-semibold mb-4">AI Reasoning</h3>
              <ul className="space-y-2">
                {result.reasoning.map((reason: string, idx: number) => (
                  <li key={idx} className="text-text-secondary text-sm flex items-start gap-2">
                    <span className="text-accent-primary mt-1">•</span>
                    <span>{reason}</span>
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
