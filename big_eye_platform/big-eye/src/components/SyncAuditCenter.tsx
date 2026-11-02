import { useEffect, useState } from 'react';
import { Activity, Database, Eye, FileDown, ListPlus, RefreshCw, ShieldCheck, TriangleAlert } from 'lucide-react';
import { addWatchlistIndicator, downloadJson, getSyncSnapshot, severityClass, SyncSnapshot } from '../lib/analysis';

type Panel = 'overview' | 'watchlist' | 'quotas';

export default function SyncAuditCenter() {
  const [panel, setPanel] = useState<Panel>('overview');
  const [snapshot, setSnapshot] = useState<SyncSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [indicator, setIndicator] = useState({ indicator_type: 'domain', indicator_value: '', label: '', severity: 'medium', notes: '' });
  const [message, setMessage] = useState('');

  const refresh = async () => {
    setLoading(true);
    try {
      setSnapshot(await getSyncSnapshot());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const addIndicator = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!indicator.indicator_value.trim()) return;
    await addWatchlistIndicator({ ...indicator, indicator_value: indicator.indicator_value.trim() });
    setIndicator({ ...indicator, indicator_value: '', label: '', notes: '' });
    setMessage('Indicator added to the watchlist.');
    await refresh();
  };

  const modeText = snapshot?.mode === 'synced' ? 'Supabase synchronized' : snapshot?.mode === 'not-authenticated' ? 'Sign-in required for cloud sync' : snapshot?.mode === 'degraded' ? 'Cloud sync degraded' : 'Offline preview';
  const modeClass = snapshot?.mode === 'synced' ? 'text-emerald-300 border-emerald-400/30 bg-emerald-400/10' : snapshot?.mode === 'offline' ? 'text-blue-300 border-blue-400/30 bg-blue-400/10' : 'text-amber-300 border-amber-300/30 bg-amber-300/10';

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300"><Database className="h-4 w-4" /> Governance / audit / sync</div>
          <h2 className="mt-2 text-3xl font-bold text-text-primary">Sync & Audit Center</h2>
          <p className="mt-2 max-w-3xl text-text-secondary">See what is synchronized, which incidents are open, where provider quotas stand, and which indicators deserve continuous monitoring.</p>
        </div>
        <div className="flex items-center gap-2"><span className={`rounded-full border px-3 py-1 text-xs font-semibold ${modeClass}`}>{loading ? 'Checking…' : modeText}</span><button onClick={refresh} disabled={loading} className="rounded-md border border-border-subtle p-2 text-text-secondary hover:bg-bg-hover-surface disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button></div>
      </div>

      {snapshot?.errors.length ? <div className="flex items-start gap-3 rounded-md border border-amber-300/30 bg-amber-300/10 p-4 text-sm text-amber-200"><TriangleAlert className="mt-0.5 h-5 w-5 flex-none" /><div><p className="font-semibold">Some sync streams are unavailable</p><ul className="mt-1 list-disc pl-5 text-xs opacity-80">{snapshot.errors.map((error) => <li key={error}>{error}</li>)}</ul></div></div> : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[['Cloud scans', snapshot?.scans.length || 0, ShieldCheck], ['Open incidents', snapshot?.incidents.filter((incident) => incident.status === 'open').length || 0, TriangleAlert], ['Watchlist indicators', snapshot?.watchlist.length || 0, Eye], ['Provider quota rows', snapshot?.apiUsage.length || 0, Activity]].map(([label, value, Icon]: any) => <div key={label} className="rounded-lg border border-border-subtle bg-bg-dark-surface p-5 shadow-card"><div className="flex items-center justify-between text-sm text-text-secondary"><span>{label}</span><Icon className="h-5 w-5 text-accent-primary" /></div><p className="mt-3 text-2xl font-bold text-text-primary">{value}</p></div>)}
      </div>

      <nav className="flex overflow-x-auto rounded-lg border border-border-subtle bg-bg-dark-surface p-1">
        {[['overview', 'Ledger overview'], ['watchlist', 'Threat watchlist'], ['quotas', 'Provider quotas']].map(([id, label]) => <button key={id} onClick={() => setPanel(id as Panel)} className={`whitespace-nowrap rounded-md px-4 py-2 text-sm font-semibold transition ${panel === id ? 'bg-accent-primary text-white' : 'text-text-secondary hover:bg-bg-hover-surface'}`}>{label}</button>)}
      </nav>

      {panel === 'overview' && <div className="grid grid-cols-1 gap-6 xl:grid-cols-2"><section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card"><div className="flex items-center justify-between"><div><h3 className="text-lg font-semibold text-text-primary">Cloud scan ledger</h3><p className="mt-1 text-sm text-text-secondary">Normalized records in <code>security_scans</code>.</p></div><button onClick={() => downloadJson('big-eye-cloud-scans.json', snapshot?.scans || [])} className="rounded-md border border-border-subtle p-2 text-text-secondary hover:bg-bg-hover-surface"><FileDown className="h-4 w-4" /></button></div>{snapshot?.scans.length ? <div className="mt-4 space-y-2">{snapshot.scans.slice(0, 10).map((scan) => <div key={scan.id} className="flex items-center justify-between gap-3 rounded-md border border-border-subtle bg-bg-near-black p-3"><div className="min-w-0"><p className="truncate text-sm font-semibold text-text-primary">{scan.sender_domain || 'Unknown sender domain'}</p><p className="text-xs text-text-tertiary">{new Date(scan.created_at).toLocaleString()} · {scan.finding_count || 0} findings</p></div><div className="text-right"><p className="font-bold text-text-primary">{scan.overall_score}</p><p className={`text-[10px] font-bold uppercase ${severityClass(scan.risk_level).split(' ')[0]}`}>{scan.verdict}</p></div></div>)}</div> : <Empty text="No cloud scans yet. Run a command-center analysis after signing in." />}</section><section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card"><h3 className="text-lg font-semibold text-text-primary">Incident queue</h3><p className="mt-1 text-sm text-text-secondary">High-risk findings are synchronized to <code>security_incidents</code>.</p>{snapshot?.incidents.length ? <div className="mt-4 space-y-2">{snapshot.incidents.slice(0, 10).map((incident) => <div key={incident.id} className={`rounded-md border p-3 ${severityClass(incident.severity)}`}><div className="flex items-center justify-between gap-3"><p className="truncate text-sm font-semibold">{incident.title}</p><span className="text-[10px] font-bold uppercase">{incident.status}</span></div><p className="mt-1 text-xs opacity-70">{new Date(incident.created_at).toLocaleString()}</p></div>)}</div> : <Empty text="No open incidents. The queue will populate for high and critical verdicts." />}</section></div>}

      {panel === 'watchlist' && <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(340px,0.8fr)]"><section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card"><h3 className="text-lg font-semibold text-text-primary">Active indicators</h3><p className="mt-1 text-sm text-text-secondary">Use this for repeat senders, domains, URLs, IPs, or file hashes.</p>{snapshot?.watchlist.length ? <div className="mt-4 space-y-2">{snapshot.watchlist.map((item) => <div key={item.id} className="flex items-center justify-between gap-3 rounded-md border border-border-subtle bg-bg-near-black p-3"><div className="min-w-0"><div className="flex items-center gap-2"><span className="rounded bg-accent-primary/15 px-2 py-1 text-[10px] font-bold uppercase text-accent-primary">{item.indicator_type}</span><span className="truncate text-sm font-mono text-text-primary">{item.indicator_value}</span></div><p className="mt-1 text-xs text-text-tertiary">{item.label || 'Unlabeled indicator'}</p></div><span className={`rounded border px-2 py-1 text-[10px] font-bold uppercase ${severityClass(item.severity)}`}>{item.severity}</span></div>)}</div> : <Empty text="No active watchlist indicators." />}</section><form onSubmit={addIndicator} className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card"><h3 className="flex items-center gap-2 text-lg font-semibold text-text-primary"><ListPlus className="h-5 w-5 text-accent-primary" />Add indicator</h3><div className="mt-4 space-y-3"><select value={indicator.indicator_type} onChange={(event) => setIndicator({ ...indicator, indicator_type: event.target.value })} className="w-full rounded-md border border-border-subtle bg-bg-near-black px-3 py-2 text-sm text-text-primary"><option value="domain">Domain</option><option value="email">Email</option><option value="ip">IP address</option><option value="url">URL</option><option value="sha256">SHA-256</option></select><input required value={indicator.indicator_value} onChange={(event) => setIndicator({ ...indicator, indicator_value: event.target.value })} placeholder="indicator value" className="w-full rounded-md border border-border-subtle bg-bg-near-black px-3 py-2 text-sm text-text-primary" /><input value={indicator.label} onChange={(event) => setIndicator({ ...indicator, label: event.target.value })} placeholder="label / campaign name" className="w-full rounded-md border border-border-subtle bg-bg-near-black px-3 py-2 text-sm text-text-primary" /><select value={indicator.severity} onChange={(event) => setIndicator({ ...indicator, severity: event.target.value })} className="w-full rounded-md border border-border-subtle bg-bg-near-black px-3 py-2 text-sm text-text-primary"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select><textarea value={indicator.notes} onChange={(event) => setIndicator({ ...indicator, notes: event.target.value })} placeholder="notes (optional)" rows={3} className="w-full rounded-md border border-border-subtle bg-bg-near-black px-3 py-2 text-sm text-text-primary" /><button type="submit" className="w-full rounded-md bg-accent-primary px-4 py-2.5 text-sm font-semibold text-white hover:bg-accent-hover">Add to watchlist</button>{message && <p className="text-sm text-emerald-300">{message}</p>}</div></form></div>}

      {panel === 'quotas' && <section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card"><h3 className="text-lg font-semibold text-text-primary">External provider usage</h3><p className="mt-1 text-sm text-text-secondary">Quota rows come from <code>api_usage_tracking</code>; the offline preview intentionally makes no provider calls.</p>{snapshot?.apiUsage.length ? <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[600px] text-left text-sm"><thead className="border-b border-border-subtle text-xs uppercase text-text-tertiary"><tr><th className="pb-3">Provider</th><th className="pb-3">Date</th><th className="pb-3">Usage</th><th className="pb-3">Limit</th><th className="pb-3">Period</th></tr></thead><tbody>{snapshot.apiUsage.map((usage) => <tr key={`${usage.api_name}-${usage.date}`} className="border-b border-border-subtle/60"><td className="py-3 text-text-primary">{usage.api_name}</td><td className="py-3 text-text-secondary">{usage.date}</td><td className="py-3 text-text-secondary">{usage.request_count}</td><td className="py-3 text-text-secondary">{usage.limit_total}</td><td className="py-3 text-text-tertiary">{usage.reset_period}</td></tr>)}</tbody></table></div> : <Empty text="No provider quota data is available yet." />}</section>}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <div className="mt-4 rounded-md border border-dashed border-border-subtle p-8 text-center text-sm text-text-tertiary">{text}</div>;
}
