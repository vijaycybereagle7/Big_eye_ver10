import { useState } from 'react';
import { Link, Mail, AlertTriangle, CheckCircle, XCircle, Shield } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';
import { ReputationGauge } from './ReputationGauge';
import { ValidationBadges } from './ValidationBadges';

type AnalysisMode = 'direct' | 'email';

export default function LinkChecker() {
  const [mode, setMode] = useState<AnalysisMode>('direct');
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const analyzeDirectLink = async () => {
    if (!inputValue.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const { data, error } = await invokeEdgeFunction('check-link-reputation', { url: inputValue.trim() });

      if (error) throw error;

      setResult(data?.data || data);

      // Track analytics
      await invokeEdgeFunction('track-user-analytics', {
        toolName: 'Link Checker',
        analysisType: 'direct-link',
        success: true,
        additionalData: { url: inputValue.trim() },
      });
    } catch (error: any) {
      console.error('Link analysis error:', error);
      setResult({ error: error.message || 'Failed to analyze link' });
    } finally {
      setLoading(false);
    }
  };

  const analyzeEmailLinks = async () => {
    if (!inputValue.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const { data, error } = await invokeEdgeFunction('analyze-email-links', { emailContent: inputValue.trim() });

      if (error) throw error;

      setResult(data?.data || data);

      // Track analytics
      await invokeEdgeFunction('track-user-analytics', {
        toolName: 'Link Checker',
        analysisType: 'email-content',
        success: true,
        additionalData: { linksFound: data?.data?.linksFound || 0 },
      });
    } catch (error: any) {
      console.error('Email link analysis error:', error);
      setResult({ error: error.message || 'Failed to analyze email content' });
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = () => {
    if (mode === 'direct') {
      analyzeDirectLink();
    } else {
      analyzeEmailLinks();
    }
  };

  const getThreatColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'critical':
        return 'text-red-500';
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
        return 'text-blue-500';
      case 'safe':
        return 'text-green-500';
      default:
        return 'text-gray-500';
    }
  };

  const getThreatIcon = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'critical':
      case 'high':
        return <XCircle className="w-6 h-6 text-red-500" />;
      case 'medium':
        return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
      case 'low':
        return <Shield className="w-6 h-6 text-blue-500" />;
      case 'safe':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      default:
        return <Shield className="w-6 h-6 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-bg-surface rounded-lg border border-border-subtle p-6">
        <h2 className="text-xl font-semibold text-text-primary mb-4 flex items-center gap-2">
          <Link className="w-6 h-6 text-accent-primary" />
          Link Checker for Phishing/Scam
        </h2>
        <p className="text-text-secondary mb-6">
          Analyze URLs and email content to detect phishing links, scams, and malicious websites.
        </p>

        {/* Mode Selection */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setMode('direct')}
            className={`flex-1 px-4 py-3 rounded-lg border transition-colors ${
              mode === 'direct'
                ? 'border-accent-primary bg-accent-primary/10 text-accent-primary'
                : 'border-border-subtle text-text-secondary hover:bg-bg-hover-surface'
            }`}
          >
            <Link className="w-5 h-5 mx-auto mb-2" />
            <div className="text-sm font-semibold">Direct Link Analysis</div>
            <div className="text-xs mt-1">Paste a URL to analyze</div>
          </button>
          <button
            onClick={() => setMode('email')}
            className={`flex-1 px-4 py-3 rounded-lg border transition-colors ${
              mode === 'email'
                ? 'border-accent-primary bg-accent-primary/10 text-accent-primary'
                : 'border-border-subtle text-text-secondary hover:bg-bg-hover-surface'
            }`}
          >
            <Mail className="w-5 h-5 mx-auto mb-2" />
            <div className="text-sm font-semibold">Email Content Analysis</div>
            <div className="text-xs mt-1">Paste email content to scan all links</div>
          </button>
        </div>

        {/* Input Area */}
        <div className="space-y-4">
          {mode === 'direct' ? (
            <div>
              <label className="block text-sm font-semibold text-text-primary mb-2">
                Enter URL
              </label>
              <input
                type="url"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-4 py-2 bg-bg-near-black border border-border-subtle rounded-lg text-text-primary placeholder-text-tertiary focus:border-accent-primary focus:outline-none transition-colors"
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-semibold text-text-primary mb-2">
                Paste Email Content
              </label>
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Paste the complete email content here..."
                rows={8}
                className="w-full px-4 py-2 bg-bg-near-black border border-border-subtle rounded-lg text-text-primary placeholder-text-tertiary focus:border-accent-primary focus:outline-none transition-colors resize-none"
              />
            </div>
          )}

          <button
            onClick={handleAnalyze}
            disabled={loading || !inputValue.trim()}
            className="w-full px-6 py-3 bg-accent-primary text-white rounded-lg font-semibold hover:bg-accent-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Analyzing...' : mode === 'direct' ? 'Check Link' : 'Scan Email Links'}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-bg-surface rounded-lg border border-border-subtle p-6 space-y-6 animate-fade-in">
          {result.error ? (
            <div className="text-red-500 flex items-center gap-2">
              <XCircle className="w-5 h-5" />
              <span>{result.error}</span>
            </div>
          ) : mode === 'direct' ? (
            // Direct Link Results
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-border-subtle pb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-text-primary">Link Analysis Results</h3>
                  <p className="text-sm text-text-tertiary mt-1">{result.url}</p>
                  
                  {result.validated_by && result.validated_by.length > 0 && (
                    <ValidationBadges validated_by={result.validated_by} details={result.validationDetails} />
                  )}
                </div>
                <div className="flex items-center gap-4">
                  {result.reputation_score !== undefined && (
                    <ReputationGauge score={result.reputation_score} size={80} label="URL Reputation" />
                  )}
                  {getThreatIcon(result.threatLevel)}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-bg-near-black rounded-lg">
                  <div className="text-sm text-text-tertiary mb-1">Threat Level</div>
                  <div className={`text-xl font-bold ${getThreatColor(result.threatLevel)}`}>
                    {result.threatLevel}
                  </div>
                </div>
                <div className="p-4 bg-bg-near-black rounded-lg">
                  <div className="text-sm text-text-tertiary mb-1">Threat Score</div>
                  <div className="text-xl font-bold text-text-primary">{result.threatScore}/100</div>
                </div>
              </div>

              {result.recommendation && (
                <div className="p-4 bg-accent-primary/10 border border-accent-primary/20 rounded-lg">
                  <div className="text-sm font-semibold text-accent-primary mb-1">Recommendation</div>
                  <div className="text-text-primary">{result.recommendation}</div>
                </div>
              )}

              {result.warnings && result.warnings.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-text-primary">Warnings</h4>
                  {result.warnings.map((warning: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 text-orange-500">
                      <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{warning}</span>
                    </div>
                  ))}
                </div>
              )}

              {result.checks && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-text-primary">Security Checks</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(result.checks).map(([key, value]) => (
                      <div key={key} className="p-3 bg-bg-near-black rounded-lg">
                        <div className="text-xs text-text-tertiary capitalize mb-1">
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </div>
                        <div className="text-sm text-text-primary">{value as string}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            // Email Links Results
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-border-subtle pb-4">
                <div>
                  <h3 className="text-lg font-semibold text-text-primary">Email Link Analysis Results</h3>
                  <p className="text-sm text-text-tertiary mt-1">
                    {result.linksFound} link{result.linksFound !== 1 ? 's' : ''} found
                  </p>
                </div>
                {getThreatIcon(result.overallThreatLevel)}
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-bg-near-black rounded-lg">
                  <div className="text-sm text-text-tertiary mb-1">Overall Threat</div>
                  <div className={`text-xl font-bold ${getThreatColor(result.overallThreatLevel)}`}>
                    {result.overallThreatLevel}
                  </div>
                </div>
                <div className="p-4 bg-bg-near-black rounded-lg">
                  <div className="text-sm text-text-tertiary mb-1">Threat Score</div>
                  <div className="text-xl font-bold text-text-primary">{result.overallThreatScore}/100</div>
                </div>
                <div className="p-4 bg-bg-near-black rounded-lg">
                  <div className="text-sm text-text-tertiary mb-1">Suspicious Links</div>
                  <div className="text-xl font-bold text-orange-500">
                    {result.statistics?.totalSuspicious || 0}
                  </div>
                </div>
              </div>

              {result.overallRecommendation && (
                <div className="p-4 bg-accent-primary/10 border border-accent-primary/20 rounded-lg">
                  <div className="text-sm font-semibold text-accent-primary mb-1">Recommendation</div>
                  <div className="text-text-primary">{result.overallRecommendation}</div>
                </div>
              )}

              {result.links && result.links.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-text-primary">Analyzed Links</h4>
                  {result.links.map((link: any, idx: number) => (
                    <div key={idx} className="p-4 bg-bg-near-black rounded-lg border border-border-subtle">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-mono text-text-primary truncate">{link.url}</div>
                          <div className="text-xs text-text-tertiary mt-1">{link.domain}</div>
                        </div>
                        <div className={`text-sm font-semibold ml-4 ${getThreatColor(link.threatLevel)}`}>
                          {link.threatLevel}
                        </div>
                      </div>

                      {link.warnings && link.warnings.length > 0 && (
                        <div className="space-y-1 mb-3">
                          {link.warnings.map((warning: string, wIdx: number) => (
                            <div key={wIdx} className="flex items-start gap-2 text-orange-500 text-xs">
                              <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                              <span>{warning}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {link.suspiciousIndicators && link.suspiciousIndicators.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {link.suspiciousIndicators.map((indicator: string, iIdx: number) => (
                            <span
                              key={iIdx}
                              className="px-2 py-1 bg-yellow-500/10 text-yellow-500 text-xs rounded"
                            >
                              {indicator}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
