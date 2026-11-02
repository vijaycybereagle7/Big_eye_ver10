import React, { useState } from 'react';
import { Database, Shield, Search, AlertTriangle, CheckCircle, XCircle, BarChart3, Zap } from 'lucide-react';
import { invokeEdgeFunction } from '../lib/analysis';

interface DatabaseAnalysisResult {
  [key: string]: any;
}

const DatabaseAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'email' | 'threat' | 'comprehensive'>('email');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<DatabaseAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Email Validation State
  const [email, setEmail] = useState('');
  const [verifySyntax, setVerifySyntax] = useState(true);
  const [verifyMxRecord, setVerifyMxRecord] = useState(true);
  const [checkDisposable, setCheckDisposable] = useState(true);

  // Threat Intelligence State
  const [threatQuery, setThreatQuery] = useState('');
  const [queryType, setQueryType] = useState<'ip' | 'domain' | 'url' | 'hash'>('domain');
  const [includeContext, setIncludeContext] = useState(true);
  const [includeRelated, setIncludeRelated] = useState(true);

  // Comprehensive Analysis State
  const [bulkEmails, setBulkEmails] = useState('');
  const [bulkDomains, setBulkDomains] = useState('');
  const [bulkIPs, setBulkIPs] = useState('');
  const [bulkUrls, setBulkUrls] = useState('');
  const [analysisType, setAnalysisType] = useState<'comprehensive' | 'email_security' | 'phishing_analysis' | 'threat_intelligence'>('comprehensive');

  const handleEmailValidation = async () => {
    if (!email.trim()) {
      setError('Please enter an email address');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { data, error } = await invokeEdgeFunction('database-email-validation', {
        email: email.trim(),
        verify_syntax: verifySyntax,
        verify_mx_record: verifyMxRecord,
        check_disposable: checkDisposable,
      });

      if (error) throw error;

      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Email validation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleThreatIntelligence = async () => {
    if (!threatQuery.trim()) {
      setError('Please enter a value to query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { data, error } = await invokeEdgeFunction('database-threat-intelligence', {
        query_type: queryType,
        value: threatQuery.trim(),
        include_context: includeContext,
        include_related: includeRelated,
        time_range_days: 30,
      });

      if (error) throw error;

      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Threat intelligence query failed');
    } finally {
      setLoading(false);
    }
  };

  const handleComprehensiveAnalysis = async () => {
    const emails = bulkEmails.split('\n').map(e => e.trim()).filter(e => e);
    const domains = bulkDomains.split('\n').map(d => d.trim()).filter(d => d);
    const ips = bulkIPs.split('\n').map(i => i.trim()).filter(i => i);
    const urls = bulkUrls.split('\n').map(u => u.trim()).filter(u => u);

    if (emails.length + domains.length + ips.length + urls.length === 0) {
      setError('Please enter at least one item to analyze');
      return;
    }

    if (emails.length + domains.length + ips.length + urls.length > 100) {
      setError('Maximum 100 items allowed per analysis');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { data, error } = await invokeEdgeFunction('database-comprehensive-analysis', {
        analysis_type: analysisType,
        emails,
        domains,
        ip_addresses: ips,
        urls,
        options: {},
      });

      if (error) throw error;

      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Comprehensive analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const renderEmailValidationResults = () => {
    if (!results?.data) return null;

    const data = results.data;
    const threats = data.threats || [];
    const recommendations = data.recommendations || [];

    return (
      <div className="space-y-6">
        {/* Validation Summary */}
        <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-text-primary">Email Validation Results</h3>
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
              data.is_valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {data.is_valid ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
              <span className="text-sm font-medium">
                {data.is_valid ? 'Valid' : 'Invalid'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="text-sm font-medium text-text-secondary">Email</label>
              <p className="text-text-primary font-mono">{data.email}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-text-secondary">Confidence Score</label>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${data.confidence_score > 0.7 ? 'bg-green-500' : data.confidence_score > 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${data.confidence_score * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm text-text-secondary">{(data.confidence_score * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Validation Details */}
          {data.validation_details && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
                  data.validation_details.syntax_valid ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                }`}>
                  {data.validation_details.syntax_valid ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                </div>
                <p className="text-xs text-text-secondary">Syntax</p>
              </div>
              <div className="text-center">
                <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
                  data.validation_details.domain_valid ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                }`}>
                  {data.validation_details.domain_valid ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                </div>
                <p className="text-xs text-text-secondary">Domain</p>
              </div>
              <div className="text-center">
                <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
                  data.validation_details.mx_record_valid ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                }`}>
                  {data.validation_details.mx_record_valid ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                </div>
                <p className="text-xs text-text-secondary">MX Record</p>
              </div>
              <div className="text-center">
                <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
                  data.validation_details.disposable ? 'bg-orange-100 text-orange-600' : 'bg-green-100 text-green-600'
                }`}>
                  {data.validation_details.disposable ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
                </div>
                <p className="text-xs text-text-secondary">Disposable</p>
              </div>
            </div>
          )}
        </div>

        {/* Threats */}
        {threats.length > 0 && (
          <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Detected Threats</h3>
            <div className="space-y-3">
              {threats.map((threat: any, index: number) => (
                <div key={index} className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-800 capitalize">{threat.type.replace('_', ' ')}</p>
                    <p className="text-sm text-red-600">{threat.description}</p>
                    <p className="text-xs text-red-500 mt-1">Source: {threat.source}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Recommendations</h3>
            <div className="space-y-2">
              {recommendations.map((rec: string, index: number) => (
                <div key={index} className="flex items-start gap-2">
                  <Zap className="w-4 h-4 text-yellow-500 mt-0.5" />
                  <p className="text-sm text-text-secondary">{rec}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderThreatIntelligenceResults = () => {
    if (!results?.data) return null;

    const data = results.data;
    const threats = data.threats || [];
    const related = data.related_indicators || [];

    return (
      <div className="space-y-6">
        {/* Threat Summary */}
        <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Threat Intelligence Summary</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{data.summary?.total_threats || 0}</div>
              <div className="text-sm text-text-secondary">Total Threats</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{data.summary?.high_severity || 0}</div>
              <div className="text-sm text-text-secondary">High Severity</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{data.summary?.medium_severity || 0}</div>
              <div className="text-sm text-text-secondary">Medium Severity</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{(data.confidence_score * 100).toFixed(1)}%</div>
              <div className="text-sm text-text-secondary">Confidence</div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-text-secondary">
            <span>Indicator: <span className="font-mono text-text-primary">{data.indicator}</span></span>
            <span>Type: <span className="font-medium text-text-primary">{data.indicator_type}</span></span>
          </div>
        </div>

        {/* Threats */}
        {threats.length > 0 && (
          <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Detected Threats</h3>
            <div className="space-y-4">
              {threats.map((threat: any, index: number) => (
                <div key={index} className="border border-border-subtle rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${
                        threat.severity === 'high' ? 'bg-red-500' :
                        threat.severity === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                      }`}></div>
                      <span className="font-medium text-text-primary capitalize">{threat.type.replace('_', ' ')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        threat.severity === 'high' ? 'bg-red-100 text-red-800' :
                        threat.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {threat.severity}
                      </span>
                      <span className="text-sm text-text-secondary">{threat.score}/100</span>
                    </div>
                  </div>
                  <p className="text-sm text-text-secondary mb-3">{threat.description}</p>
                  <div className="flex items-center gap-4 text-xs text-text-tertiary">
                    <span>Source: {threat.source}</span>
                    <span>Category: {threat.category}</span>
                    {threat.tags && threat.tags.length > 0 && (
                      <span>Tags: {threat.tags.join(', ')}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Related Indicators */}
        {related.length > 0 && (
          <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Related Indicators</h3>
            <div className="space-y-2">
              {related.map((indicator: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 bg-bg-hover-surface rounded-lg">
                  <div>
                    <span className="font-mono text-text-primary">{indicator.value}</span>
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                      {indicator.type}
                    </span>
                  </div>
                  <div className="text-sm text-text-secondary">
                    {(indicator.confidence * 100).toFixed(1)}% confidence
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Data Sources */}
        {data.data_sources && (
          <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Data Sources</h3>
            <div className="flex flex-wrap gap-2">
              {data.data_sources.map((source: string, index: number) => (
                <span key={index} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderComprehensiveAnalysisResults = () => {
    if (!results?.data) return null;

    const data = results.data;
    const summary = data.summary || {};
    const detailed = data.detailed_results || {};

    return (
      <div className="space-y-6">
        {/* Analysis Summary */}
        <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Analysis Summary</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{data.total_items || 0}</div>
              <div className="text-sm text-text-secondary">Total Items</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{summary.threats_found || 0}</div>
              <div className="text-sm text-text-secondary">Threats Found</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{summary.high_risk_items || 0}</div>
              <div className="text-sm text-text-secondary">High Risk</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{summary.medium_risk_items || 0}</div>
              <div className="text-sm text-text-secondary">Medium Risk</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{summary.clean_items || 0}</div>
              <div className="text-sm text-text-secondary">Clean</div>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm text-text-secondary">
            <span>Analysis Type: <span className="font-medium text-text-primary">{data.analysis_type}</span></span>
            <span>Duration: <span className="font-medium text-text-primary">{data.analysis_duration}ms</span></span>
          </div>
        </div>

        {/* Detailed Results by Type */}
        {Object.entries(detailed).map(([type, items]: [string, any]) => {
          if (!items || items.length === 0) return null;
          
          return (
            <div key={type} className="bg-bg-card border border-border-subtle rounded-lg p-6">
              <h4 className="text-lg font-semibold text-text-primary mb-4 capitalize">{type.replace('_', ' ')}</h4>
              <div className="space-y-3">
                {items.map((item: any, index: number) => (
                  <div key={index} className="border border-border-subtle rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-sm text-text-primary">{item.item}</span>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          item.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                          item.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                        }`}>
                          {item.risk_level} risk
                        </span>
                        <span className="text-sm text-text-secondary">
                          {(item.confidence_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    {item.threats && item.threats.length > 0 && (
                      <div className="space-y-1">
                        {item.threats.map((threat: any, threatIndex: number) => (
                          <div key={threatIndex} className="flex items-center gap-2 text-sm">
                            <AlertTriangle className="w-3 h-3 text-red-500" />
                            <span className="text-red-600 capitalize">{threat.type.replace('_', ' ')}</span>
                            <span className="text-text-secondary">- {threat.description}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {/* Recommendations */}
        {data.recommendations && data.recommendations.length > 0 && (
          <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Recommendations</h3>
            <div className="space-y-2">
              {data.recommendations.map((rec: string, index: number) => (
                <div key={index} className="flex items-start gap-2">
                  <Zap className="w-4 h-4 text-yellow-500 mt-0.5" />
                  <p className="text-sm text-text-secondary">{rec}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-center gap-3 mb-3">
          <Database className="w-8 h-8" />
          <h2 className="text-2xl font-bold">Big Eye Security Database</h2>
        </div>
        <p className="text-purple-100">
          Advanced cybersecurity analysis powered by comprehensive threat intelligence and validation systems.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-border-subtle">
        <div className="flex space-x-8">
          {[
            { id: 'email', label: 'Email Validation', icon: Shield },
            { id: 'threat', label: 'Threat Intelligence', icon: Search },
            { id: 'comprehensive', label: 'Comprehensive Analysis', icon: BarChart3 }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-accent-primary text-text-primary'
                  : 'border-transparent text-text-secondary hover:text-text-primary'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="bg-bg-card border border-border-subtle rounded-lg p-6">
        {activeTab === 'email' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-4">Email Validation</h3>
              <p className="text-text-secondary mb-6">
                Validate email addresses using the Big Eye Security Database with comprehensive checks including syntax, 
                domain validation, MX records, and disposable email detection.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full px-3 py-2 bg-bg-input border border-border-subtle rounded-md text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  />
                </div>

                <div className="space-y-3">
                  <label className="block text-sm font-medium text-text-secondary">Validation Options</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={verifySyntax}
                        onChange={(e) => setVerifySyntax(e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm text-text-secondary">Verify email syntax</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={verifyMxRecord}
                        onChange={(e) => setVerifyMxRecord(e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm text-text-secondary">Check MX records</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={checkDisposable}
                        onChange={(e) => setCheckDisposable(e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm text-text-secondary">Detect disposable emails</span>
                    </label>
                  </div>
                </div>

                <button
                  onClick={handleEmailValidation}
                  disabled={loading || !email.trim()}
                  className="w-full px-4 py-2 bg-accent-primary text-white rounded-md hover:bg-accent-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Validating...' : 'Validate Email'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'threat' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-4">Threat Intelligence Query</h3>
              <p className="text-text-secondary mb-6">
                Query comprehensive threat intelligence for IP addresses, domains, URLs, or file hashes using 
                multiple security databases and intelligence sources.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Query Type</label>
                  <select
                    value={queryType}
                    onChange={(e) => setQueryType(e.target.value as any)}
                    className="w-full px-3 py-2 bg-bg-input border border-border-subtle rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  >
                    <option value="ip">IP Address</option>
                    <option value="domain">Domain</option>
                    <option value="url">URL</option>
                    <option value="hash">File Hash</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Value to Query</label>
                  <input
                    type="text"
                    value={threatQuery}
                    onChange={(e) => setThreatQuery(e.target.value)}
                    placeholder={
                      queryType === 'ip' ? '192.168.1.1' :
                      queryType === 'domain' ? 'example.com' :
                      queryType === 'url' ? 'https://example.com' :
                      'd41d8cd98f00b204e9800998ecf8427e'
                    }
                    className="w-full px-3 py-2 bg-bg-input border border-border-subtle rounded-md text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  />
                </div>

                <div className="space-y-3">
                  <label className="block text-sm font-medium text-text-secondary">Query Options</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={includeContext}
                        onChange={(e) => setIncludeContext(e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm text-text-secondary">Include context information</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={includeRelated}
                        onChange={(e) => setIncludeRelated(e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm text-text-secondary">Include related indicators</span>
                    </label>
                  </div>
                </div>

                <button
                  onClick={handleThreatIntelligence}
                  disabled={loading || !threatQuery.trim()}
                  className="w-full px-4 py-2 bg-accent-primary text-white rounded-md hover:bg-accent-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Querying...' : 'Query Threat Intelligence'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'comprehensive' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-4">Comprehensive Analysis</h3>
              <p className="text-text-secondary mb-6">
                Perform bulk analysis of multiple items (emails, domains, IPs, URLs) using the Big Eye Security Database 
                for comprehensive threat detection and security assessment.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">Analysis Type</label>
                <select
                  value={analysisType}
                  onChange={(e) => setAnalysisType(e.target.value as any)}
                  className="w-full px-3 py-2 bg-bg-input border border-border-subtle rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                >
                  <option value="comprehensive">Comprehensive Analysis</option>
                  <option value="email_security">Email Security Focus</option>
                  <option value="phishing_analysis">Phishing Analysis</option>
                  <option value="threat_intelligence">Threat Intelligence Focus</option>
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Emails (one per line)</label>
                  <textarea
                    value={bulkEmails}
                    onChange={(e) => setBulkEmails(e.target.value)}
                    placeholder="user1@example.com&#10;user2@example.com"
                    rows={4}
                    className="w-full px-3 py-2 bg-bg-input border border-border-subtle rounded-md text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Domains (one per line)</label>
                  <textarea
                    value={bulkDomains}
                    onChange={(e) => setBulkDomains(e.target.value)}
                    placeholder="example1.com&#10;example2.com"
                    rows={4}
                    className="w-full px-3 py-2 bg-bg-input border border-border-subtle rounded-md text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">IP Addresses (one per line)</label>
                  <textarea
                    value={bulkIPs}
                    onChange={(e) => setBulkIPs(e.target.value)}
                    placeholder="192.168.1.1&#10;10.0.0.1"
                    rows={4}
                    className="w-full px-3 py-2 bg-bg-input border border-border-subtle rounded-md text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">URLs (one per line)</label>
                  <textarea
                    value={bulkUrls}
                    onChange={(e) => setBulkUrls(e.target.value)}
                    placeholder="https://example1.com&#10;https://example2.com"
                    rows={4}
                    className="w-full px-3 py-2 bg-bg-input border border-border-subtle rounded-md text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  />
                </div>
              </div>

              <div className="text-sm text-text-secondary">
                <p>Total items: {bulkEmails.split('\n').filter(e => e.trim()).length + 
                              bulkDomains.split('\n').filter(d => d.trim()).length + 
                              bulkIPs.split('\n').filter(i => i.trim()).length + 
                              bulkUrls.split('\n').filter(u => u.trim()).length} / 100 max</p>
              </div>

              <button
                onClick={handleComprehensiveAnalysis}
                disabled={loading}
                className="w-full px-4 py-2 bg-accent-primary text-white rounded-md hover:bg-accent-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Analyzing...' : 'Start Comprehensive Analysis'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-500" />
            <span className="font-medium text-red-800">Error</span>
          </div>
          <p className="text-red-600 mt-1">{error}</p>
        </div>
      )}

      {/* Results Display */}
      {results && !loading && (
        <div>
          {activeTab === 'email' && renderEmailValidationResults()}
          {activeTab === 'threat' && renderThreatIntelligenceResults()}
          {activeTab === 'comprehensive' && renderComprehensiveAnalysisResults()}
        </div>
      )}
    </div>
  );
};

export default DatabaseAnalysis;
