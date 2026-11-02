import { useState } from 'react';
import { invokeEdgeFunction } from '../lib/analysis';
import { AlertTriangle, CheckCircle, Shield, Clock, TrendingUp, Activity } from 'lucide-react';
import { ReputationGauge } from './ReputationGauge';
import { ValidationBadges } from './ValidationBadges';

export default function AllInOneAnalysis() {
  const [emailContent, setEmailContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const analyzeEmail = async () => {
    if (!emailContent.trim()) {
      setError('Please paste email content');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const { data, error: analyzeError } = await invokeEdgeFunction('comprehensive-email-analysis', { emailContent });

      if (analyzeError) throw analyzeError;

      setResult(data.data);
    } catch (err: any) {
      setError(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical': return 'text-red-500 bg-red-500/10 border-red-500';
      case 'high': return 'text-orange-500 bg-orange-500/10 border-orange-500';
      case 'medium': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500';
      case 'low': return 'text-blue-500 bg-blue-500/10 border-blue-500';
      case 'safe': return 'text-green-500 bg-green-500/10 border-green-500';
      default: return 'text-text-secondary bg-bg-card border-border-subtle';
    }
  };

  const getVerdictIcon = (verdict: string) => {
    if (verdict === 'LEGITIMATE') return <CheckCircle className="w-16 h-16 text-green-500" />;
    if (verdict === 'PHISHING' || verdict === 'HIGHLY SUSPICIOUS') return <AlertTriangle className="w-16 h-16 text-red-500" />;
    return <Shield className="w-16 h-16 text-yellow-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Activity className="w-8 h-8 text-accent-primary" />
            All in One Analysis
          </h2>
          <p className="text-text-secondary mt-1">Comprehensive email security analysis - paste complete email content</p>
        </div>
      </div>

      {/* Input Section */}
      <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
        <label className="block text-sm font-semibold text-text-primary mb-2">
          Email Content (Including Headers)
        </label>
        <textarea
          value={emailContent}
          onChange={(e) => setEmailContent(e.target.value)}
          placeholder={`Paste complete email content with headers here...\n\nExample:\nFrom: sender@example.com\nTo: you@example.com\nSubject: Important Account Update\nReceived: from mail.example.com [192.0.2.1]\n\nEmail body content here...`}
          className="w-full h-64 px-4 py-3 bg-bg-near-black text-text-primary border border-border-subtle rounded-md focus:outline-none focus:ring-2 focus:ring-accent-primary resize-none font-mono text-sm"
        />
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={analyzeEmail}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 bg-accent-primary text-white font-semibold rounded-md hover:bg-accent-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <Clock className="w-4 h-4 animate-spin" />
                Analyzing All Tools...
              </>
            ) : (
              <>
                <Shield className="w-4 h-4" />
                Run Complete Analysis
              </>
            )}
          </button>
          {loading && (
            <span className="text-sm text-text-secondary animate-pulse">
              Running 9 security checks in parallel...
            </span>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500 rounded-lg p-4">
          <p className="text-red-500 font-semibold">Error: {error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Overall Verdict Card */}
          <div className={`rounded-lg border-2 p-8 ${getRiskColor(result.comprehensiveVerdict.riskLevel)}`}>
            <div className="flex items-center gap-6">
              <div className="flex-shrink-0">
                {getVerdictIcon(result.comprehensiveVerdict.overallVerdict)}
              </div>
              <div className="flex-1">
                <h3 className="text-3xl font-bold mb-2">{result.comprehensiveVerdict.overallVerdict}</h3>
                <div className="flex items-center gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    <span className="text-lg font-semibold">Confidence: {result.comprehensiveVerdict.confidenceScore}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    <span className="text-sm">Risk Level: {result.comprehensiveVerdict.riskLevel.toUpperCase()}</span>
                  </div>
                </div>
                <p className="text-base font-medium">{result.comprehensiveVerdict.recommendation}</p>
                <div className="mt-3 text-sm opacity-80">
                  Analysis completed using {result.comprehensiveVerdict.toolsExecuted}/{result.comprehensiveVerdict.totalToolsAvailable} security tools
                </div>
                
                {result.validated_by && result.validated_by.length > 0 && (
                  <div className="mt-4">
                    <ValidationBadges validated_by={result.validated_by} details={result.validationDetails} />
                  </div>
                )}
              </div>
              {result.reputation_score !== undefined && (
                <div className="flex-shrink-0">
                  <ReputationGauge score={result.reputation_score} size={120} label="Overall Reputation" />
                </div>
              )}
            </div>
          </div>

          {/* Detailed Summary */}
          <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
            <h4 className="text-xl font-bold text-text-primary mb-4">Analysis Summary</h4>
            <div className="whitespace-pre-wrap text-text-secondary font-mono text-sm bg-bg-near-black p-4 rounded border border-border-subtle">
              {result.comprehensiveVerdict.summary}
            </div>
          </div>

          {/* Email Details */}
          <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
            <h4 className="text-xl font-bold text-text-primary mb-4">Parsed Email Information</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-text-tertiary">Sender Email:</span>
                <p className="text-text-primary font-semibold">{result.parsedEmail.senderEmail}</p>
              </div>
              <div>
                <span className="text-sm text-text-tertiary">Sender Domain:</span>
                <p className="text-text-primary font-semibold">{result.parsedEmail.senderDomain}</p>
              </div>
              {result.parsedEmail.senderName && (
                <div>
                  <span className="text-sm text-text-tertiary">Sender Name:</span>
                  <p className="text-text-primary font-semibold">{result.parsedEmail.senderName}</p>
                </div>
              )}
              {result.parsedEmail.subject && (
                <div>
                  <span className="text-sm text-text-tertiary">Subject:</span>
                  <p className="text-text-primary font-semibold">{result.parsedEmail.subject}</p>
                </div>
              )}
              <div>
                <span className="text-sm text-text-tertiary">Links Found:</span>
                <p className="text-text-primary font-semibold">{result.parsedEmail.linkCount}</p>
              </div>
            </div>
          </div>

          {/* Individual Analysis Details */}
          <div className="bg-bg-card rounded-lg border border-border-subtle p-6">
            <h4 className="text-xl font-bold text-text-primary mb-4">Individual Tool Results</h4>
            <div className="space-y-4">
              {Object.entries(result.individualAnalyses).map(([key, analysis]: [string, any]) => {
                if (analysis.error) {
                  return (
                    <div key={key} className="p-4 bg-bg-near-black rounded border border-border-subtle">
                      <h5 className="font-semibold text-text-secondary capitalize">{key.replace(/Analysis$/, '').replace(/([A-Z])/g, ' $1').trim()}</h5>
                      <p className="text-sm text-text-tertiary mt-1">Analysis unavailable: {analysis.message}</p>
                    </div>
                  );
                }

                return (
                  <details key={key} className="group">
                    <summary className="cursor-pointer p-4 bg-bg-near-black rounded border border-border-subtle hover:bg-bg-hover-surface transition-colors">
                      <span className="font-semibold text-text-primary capitalize">
                        {key.replace(/Analysis$/, '').replace(/([A-Z])/g, ' $1').trim()}
                      </span>
                      {analysis.threatScore !== undefined && (
                        <span className={`ml-3 text-sm ${analysis.threatScore >= 70 ? 'text-red-500' : analysis.threatScore >= 40 ? 'text-yellow-500' : 'text-green-500'}`}>
                          Threat Score: {analysis.threatScore}
                        </span>
                      )}
                      {analysis.phishingScore !== undefined && (
                        <span className={`ml-3 text-sm ${analysis.phishingScore >= 70 ? 'text-red-500' : analysis.phishingScore >= 40 ? 'text-yellow-500' : 'text-green-500'}`}>
                          Phishing Score: {analysis.phishingScore}
                        </span>
                      )}
                      {analysis.riskLevel && (
                        <span className={`ml-3 text-sm px-2 py-1 rounded ${getRiskColor(analysis.riskLevel)}`}>
                          {analysis.riskLevel.toUpperCase()}
                        </span>
                      )}
                    </summary>
                    <div className="mt-2 p-4 bg-bg-near-black/50 rounded border border-border-subtle text-sm">
                      <pre className="whitespace-pre-wrap text-text-secondary overflow-x-auto">
                        {JSON.stringify(analysis, null, 2)}
                      </pre>
                    </div>
                  </details>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
