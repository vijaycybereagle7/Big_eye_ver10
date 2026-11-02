import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertOctagon,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileWarning,
  LockKeyhole,
  RefreshCw,
  ShieldCheck,
  Siren,
  Sparkles,
  Upload,
} from 'lucide-react';
import {
  downloadJson,
  getLocalScanHistory,
  getSyncSnapshot,
  persistScan,
  runEmailSecurityAnalysis,
  SecurityAnalysisResult,
  severityClass,
  SyncSnapshot,
} from '../lib/analysis';

const SAMPLE_EMAIL = `From: "Microsoft Security" <security-alert@micr0soft-support.example>
To: analyst@example.com
Subject: URGENT: Verify your account within 24 hours
Reply-To: helpdesk@secure-account.example
Authentication-Results: mx.example; spf=fail dkim=none dmarc=fail
Received: from unknown [198.51.100.42]; Mon, 02 Nov 2026 08:00:00 +0000
Content-Disposition: attachment; filename="invoice.pdf.exe"

Your account has been suspended. Verify your password now:
https://secure-login.example/verify-account?session=8f4a9c2e`;

function scoreColor(score: number) {
  if (score >= 80) return 'text-red-400';
  if (score >= 60) return 'text-orange-300';
  if (score >= 35) return 'text-amber-300';
  return 'text-emerald-300';
}

function statusIcon(status: string) {
  if (status === 'alert') return <Siren className="h-4 w-4 text-red-400" />;
  if (status === 'attention') return <AlertOctagon className="h-4 w-4 text-amber-300" />;
  if (status === 'not-run') return <Activity className="h-4 w-4 text-slate-500" />;
  return <CheckCircle2 className="h-4 w-4 text-emerald-300" />;
}

function statusLabel(status: string) {
  return status === 'not-run' ? 'Not run' : status.charAt(0).toUpperCase() + status.slice(1);
}

export default function SecurityCommandCenter() {
  const [emailContent, setEmailContent] = useState('');
  const [analysis, setAnalysis] = useState<SecurityAnalysisResult | null>(null);
  const [snapshot, setSnapshot] = useState<SyncSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');

  const refreshSnapshot = async () => {
    setSyncing(true);
    try {
      setSnapshot(await getSyncSnapshot());
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    refreshSnapshot();
  }, []);

  const runAnalysis = async () => {
    if (!emailContent.trim()) {
      setError('Paste a complete message or load the safe training sample first.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await runEmailSecurityAnalysis(emailContent);
      const sync = await persistScan(result);
      setAnalysis({ ...result, sync });
      await refreshSnapshot();
    } catch (analysisError: any) {
      setError(analysisError.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const findingCounts = useMemo(() => {
    const findings = analysis?.findings || [];
    return {
      critical: findings.filter((finding) => finding.severity === 'critical').length,
      high: findings.filter((finding) => finding.severity === 'high').length,
      medium: findings.filter((finding) => finding.severity === 'medium').length,
    };
  }, [analysis]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-accent-primary">
            <Sparkles className="h-4 w-4" />
            Big Eye Enterprise / v8 command center
          </div>
          <h2 className="mt-2 text-3xl font-bold text-text-primary">Security Operations Command Center</h2>
          <p className="mt-2 max-w-3xl text-text-secondary">
            One decision surface for phishing, malware delivery, identity deception, email authentication, and platform posture.
            Static analysis is safe to run in preview; live reputation and DNS enrichment activate through Supabase.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${analysis?.source === 'supabase' ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300' : 'border-blue-400/30 bg-blue-400/10 text-blue-300'}`}>
            {analysis?.source === 'supabase' ? 'LIVE EDGE ANALYSIS' : 'SAFE OFFLINE PREVIEW'}
          </span>
          <button onClick={refreshSnapshot} disabled={syncing} className="inline-flex items-center gap-2 rounded-md border border-border-subtle px-3 py-2 text-sm text-text-secondary transition hover:bg-bg-hover-surface disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            Refresh sync
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: 'Threat score', value: analysis ? `${analysis.comprehensiveVerdict.overallScore}/100` : '—', icon: ShieldCheck, color: analysis ? scoreColor(analysis.comprehensiveVerdict.overallScore) : 'text-text-tertiary' },
          { label: 'Verdict', value: analysis?.comprehensiveVerdict.overallVerdict || 'Awaiting scan', icon: ClipboardCheck, color: analysis ? scoreColor(analysis.comprehensiveVerdict.overallScore) : 'text-text-tertiary' },
          { label: 'Critical / high findings', value: `${findingCounts.critical} / ${findingCounts.high}`, icon: Siren, color: findingCounts.critical || findingCounts.high ? 'text-red-400' : 'text-emerald-300' },
          { label: 'Ledger sync', value: analysis?.sync?.status || snapshot?.mode || 'checking', icon: Activity, color: analysis?.sync?.status === 'synced' ? 'text-emerald-300' : 'text-text-secondary' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="rounded-lg border border-border-subtle bg-bg-dark-surface p-5 shadow-card">
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-secondary">{label}</span>
              <Icon className={`h-5 w-5 ${color}`} />
            </div>
            <p className={`mt-4 text-2xl font-bold capitalize ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      <section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="flex items-center gap-2 text-lg font-semibold text-text-primary"><Upload className="h-5 w-5 text-accent-primary" />Analyze a message</h3>
            <p className="mt-1 text-sm text-text-secondary">Include headers and body. Big Eye never executes attachments or follows links.</p>
          </div>
          <button onClick={() => setEmailContent(SAMPLE_EMAIL)} className="rounded-md border border-accent-primary/40 px-3 py-2 text-sm font-semibold text-accent-primary transition hover:bg-accent-primary/10">
            Load red-team sample
          </button>
        </div>
        <textarea
          value={emailContent}
          onChange={(event) => setEmailContent(event.target.value)}
          placeholder="Paste RFC 5322 email content here…"
          className="mt-5 min-h-[220px] w-full resize-y rounded-md border border-border-subtle bg-bg-near-black p-4 font-mono text-sm text-text-primary outline-none transition focus:border-accent-primary"
        />
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button onClick={runAnalysis} disabled={loading} className="inline-flex items-center gap-2 rounded-md bg-accent-primary px-5 py-2.5 font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50">
            {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
            {loading ? 'Running six engines…' : 'Run enterprise analysis'}
          </button>
          {emailContent && <button onClick={() => setEmailContent('')} className="rounded-md px-3 py-2 text-sm text-text-tertiary transition hover:bg-bg-hover-surface hover:text-text-primary">Clear</button>}
          {error && <span className="text-sm text-red-400">{error}</span>}
        </div>
      </section>

      {analysis && (
        <div className="space-y-6 animate-fade-in">
          <section className={`rounded-lg border p-6 ${severityClass(analysis.comprehensiveVerdict.riskLevel)}`}>
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <FileWarning className="h-8 w-8" />
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] opacity-70">Decision</p>
                    <h3 className="text-3xl font-bold">{analysis.comprehensiveVerdict.overallVerdict}</h3>
                  </div>
                </div>
                <p className="mt-4 max-w-3xl font-medium">{analysis.comprehensiveVerdict.recommendation}</p>
                <p className="mt-2 text-sm opacity-80">{analysis.comprehensiveVerdict.summary}</p>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div><p className="text-3xl font-bold">{analysis.comprehensiveVerdict.overallScore}</p><p className="text-xs opacity-70">score</p></div>
                <div><p className="text-3xl font-bold">{analysis.comprehensiveVerdict.confidenceScore}%</p><p className="text-xs opacity-70">confidence</p></div>
                <div><p className="text-3xl font-bold">{analysis.findings.length}</p><p className="text-xs opacity-70">findings</p></div>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-2 text-xs">
              <span className="rounded-full border border-current/20 px-2.5 py-1">{analysis.parsedEmail.senderEmail || 'sender not parsed'}</span>
              <span className="rounded-full border border-current/20 px-2.5 py-1">{analysis.parsedEmail.linkCount} link(s)</span>
              <span className="rounded-full border border-current/20 px-2.5 py-1">{analysis.parsedEmail.attachments.length} attachment(s)</span>
              <span className="rounded-full border border-current/20 px-2.5 py-1">hash {analysis.contentHash.slice(0, 16)}…</span>
            </div>
          </section>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card">
              <div className="flex items-center justify-between"><h3 className="text-lg font-semibold text-text-primary">Engine health</h3><span className="text-xs text-text-tertiary">{analysis.comprehensiveVerdict.toolsExecuted}/{analysis.comprehensiveVerdict.totalToolsAvailable} active</span></div>
              <div className="mt-4 space-y-3">
                {analysis.engineStatus.map((engine) => (
                  <div key={engine.id} className="rounded-md border border-border-subtle bg-bg-near-black p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">{statusIcon(engine.status)}<span className="text-sm font-semibold text-text-primary">{engine.label}</span></div>
                      <span className="text-xs text-text-secondary">{statusLabel(engine.status)}</span>
                    </div>
                    <div className="mt-2 flex items-center gap-3"><div className="h-1.5 flex-1 overflow-hidden rounded-full bg-bg-hover-surface"><div className={`h-full ${engine.score >= 60 ? 'bg-red-400' : engine.score >= 25 ? 'bg-amber-300' : 'bg-emerald-300'}`} style={{ width: `${Math.max(engine.score, 3)}%` }} /></div><span className="w-9 text-right text-xs text-text-tertiary">{engine.score}</span></div>
                    <p className="mt-1 text-xs text-text-tertiary">{engine.detail}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card">
              <div className="flex items-center justify-between"><h3 className="text-lg font-semibold text-text-primary">Prioritized findings</h3><span className="text-xs text-text-tertiary">Evidence-led</span></div>
              {analysis.findings.length ? <div className="mt-4 space-y-3">{analysis.findings.map((finding) => <div key={finding.id} className={`rounded-md border p-4 ${severityClass(finding.severity)}`}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{finding.title}</p><p className="mt-1 text-xs opacity-80">{finding.evidence}</p></div><span className="text-[10px] font-bold uppercase tracking-widest">{finding.severity}</span></div><p className="mt-3 text-xs opacity-90">Action: {finding.recommendation}</p></div>)}</div> : <div className="mt-4 rounded-md border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">No findings crossed the review threshold.</div>}
            </section>
          </div>

          <section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card">
            <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="text-lg font-semibold text-text-primary">Recommended response playbook</h3><button onClick={() => downloadJson(`big-eye-${analysis.scanId}.json`, analysis)} className="inline-flex items-center gap-2 rounded-md border border-border-subtle px-3 py-2 text-sm text-text-secondary transition hover:bg-bg-hover-surface"><Download className="h-4 w-4" />Export JSON</button></div>
            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">{analysis.remediation.map((step, index) => <div key={step} className="flex gap-3 rounded-md border border-border-subtle bg-bg-near-black p-4"><span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-accent-primary/20 text-xs font-bold text-accent-primary">{index + 1}</span><p className="text-sm text-text-secondary">{step}</p></div>)}</div>
            <div className="mt-4 flex items-center gap-2 text-xs text-text-tertiary"><LockKeyhole className="h-4 w-4" />Privacy guard: raw message content is not sent to the ledger; only a SHA-256 hash and normalized result are stored.</div>
          </section>
        </div>
      )}

      <section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card">
        <div className="flex items-center justify-between"><div><h3 className="text-lg font-semibold text-text-primary">Recent scan ledger</h3><p className="mt-1 text-sm text-text-secondary">Local history is always available; authenticated Supabase history appears beside it after migration.</p></div><span className="text-xs text-text-tertiary">{getLocalScanHistory().length} local record(s)</span></div>
        {snapshot?.localScans?.length ? <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm"><thead className="border-b border-border-subtle text-xs uppercase tracking-wider text-text-tertiary"><tr><th className="pb-3">Time</th><th className="pb-3">Verdict</th><th className="pb-3">Score</th><th className="pb-3">Domain</th><th className="pb-3">Findings</th></tr></thead><tbody>{snapshot.localScans.slice(0, 8).map((scan) => <tr key={scan.id} className="border-b border-border-subtle/60"><td className="py-3 text-text-tertiary">{new Date(scan.createdAt).toLocaleString()}</td><td className={`py-3 font-semibold ${scoreColor(scan.score)}`}>{scan.verdict}</td><td className="py-3 text-text-secondary">{scan.score}</td><td className="py-3 font-mono text-text-secondary">{scan.senderDomain || '—'}</td><td className="py-3 text-text-secondary">{scan.findingCount}</td></tr>)}</tbody></table></div> : <div className="mt-4 rounded-md border border-dashed border-border-subtle p-8 text-center text-sm text-text-tertiary">Run an analysis to create your first evidence record.</div>}
      </section>
    </div>
  );
}
