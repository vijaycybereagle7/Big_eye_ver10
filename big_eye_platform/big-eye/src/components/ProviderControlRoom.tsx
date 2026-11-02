import { useEffect, useMemo, useState } from 'react';
import { Activity, CheckCircle2, Download, KeyRound, Layers3, RefreshCw, Search, ShieldAlert, SlidersHorizontal } from 'lucide-react';
import { downloadJson, invokeEdgeFunction } from '../lib/analysis';
import { providerCategoryLabel, ProviderCategory, PROVIDER_CATALOG, ProviderRuntime } from '../lib/providerCatalog';

type Panel = 'overview' | ProviderCategory | 'governance';

function statusClasses(provider: ProviderRuntime) {
  if (provider.health === 'ready' || provider.health === 'public-endpoint') return 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300';
  return 'border-amber-300/30 bg-amber-300/10 text-amber-200';
}

export default function ProviderControlRoom() {
  const [providers, setProviders] = useState<ProviderRuntime[]>([]);
  const [panel, setPanel] = useState<Panel>('overview');
  const [query, setQuery] = useState('');
  const [configuredOnly, setConfiguredOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);
  const [catalogNote, setCatalogNote] = useState('');

  const loadCatalog = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await invokeEdgeFunction('get-provider-catalog');
      if (response.error) throw response.error;
      const payload = response.data?.data || response.data;
      const runtimeProviders = (payload?.providers || []) as ProviderRuntime[];
      const runtime = new Map<string, ProviderRuntime>(runtimeProviders.map((provider) => [provider.id, provider]));
      setProviders(PROVIDER_CATALOG.map((definition) => ({
        ...definition,
        ...(runtime.get(definition.id) || {}),
        configured: runtime.get(definition.id)?.configured ?? definition.auth === 'public',
        secretNames: runtime.get(definition.id)?.secretNames || definition.envKeys,
        health: runtime.get(definition.id)?.health || (definition.auth === 'public' ? 'public-endpoint' : 'not-checked'),
        message: runtime.get(definition.id)?.message || 'Provider state has not been checked.',
      })));
      setGeneratedAt(payload?.generatedAt || new Date().toISOString());
      setCatalogNote(payload?.note || '');
    } catch (catalogError: any) {
      setError(catalogError.message || 'Provider catalog could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadCatalog(); }, []);

  const counts = useMemo(() => ({
    total: providers.length,
    configured: providers.filter((provider) => provider.configured).length,
    wired: providers.filter((provider) => provider.wiring === 'wired').length,
    needsReview: providers.filter((provider) => !provider.configured && provider.auth !== 'public').length,
  }), [providers]);

  const visibleProviders = useMemo(() => providers.filter((provider) => {
    const matchesPanel = panel === 'overview' || panel === 'governance' || provider.category === panel;
    const haystack = `${provider.name} ${provider.id} ${provider.coverage.join(' ')}`.toLowerCase();
    return matchesPanel && (!query.trim() || haystack.includes(query.toLowerCase())) && (!configuredOnly || provider.configured);
  }), [configuredOnly, panel, providers, query]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-violet-300"><Layers3 className="h-4 w-4" /> Integrations / provider governance</div>
          <h2 className="mt-2 text-3xl font-bold text-text-primary">API Control Room</h2>
          <p className="mt-2 max-w-3xl text-text-secondary">One governed catalog for threat intelligence, email, URL, domain, network, and mailbox providers. Keys are resolved only in Supabase Edge Functions; this UI never receives secret values.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2"><span className="rounded-full border border-violet-300/30 bg-violet-300/10 px-3 py-1 text-xs font-semibold text-violet-200">{counts.total} provider contracts</span><button onClick={loadCatalog} disabled={loading} className="inline-flex items-center gap-2 rounded-md border border-border-subtle px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover-surface disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />Refresh state</button><button onClick={() => downloadJson('big-eye-provider-catalog.json', providers)} className="inline-flex items-center gap-2 rounded-md border border-border-subtle px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover-surface"><Download className="h-4 w-4" />Export</button></div>
      </div>

      {error && <div className="rounded-md border border-red-400/30 bg-red-400/10 p-4 text-sm text-red-200">{error}</div>}
      {catalogNote && <div className="flex items-start gap-2 rounded-md border border-blue-400/20 bg-blue-400/10 p-4 text-xs text-blue-200"><ShieldAlert className="mt-0.5 h-4 w-4 flex-none" />{catalogNote}</div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">{[['Cataloged', counts.total, Layers3], ['Configured / public', counts.configured, CheckCircle2], ['Wired adapters', counts.wired, Activity], ['Needs configuration', counts.needsReview, KeyRound]].map(([label, value, Icon]: any) => <div key={label} className="rounded-lg border border-border-subtle bg-bg-dark-surface p-5 shadow-card"><div className="flex items-center justify-between text-sm text-text-secondary"><span>{label}</span><Icon className="h-5 w-5 text-accent-primary" /></div><p className="mt-3 text-2xl font-bold text-text-primary">{value}</p></div>)}</div>

      <div className="flex flex-col gap-3 rounded-lg border border-border-subtle bg-bg-dark-surface p-4 lg:flex-row lg:items-center lg:justify-between"><div className="flex items-center gap-2 overflow-x-auto">{[['overview', 'Overview'], ['threat-intelligence', 'Threat intel'], ['email', 'Email'], ['url', 'URL'], ['domain', 'Domain'], ['network', 'Network'], ['platform', 'Platform'], ['governance', 'Governance']].map(([id, label]) => <button key={id} onClick={() => setPanel(id as Panel)} className={`whitespace-nowrap rounded-md px-3 py-2 text-sm font-semibold transition ${panel === id ? 'bg-accent-primary text-white' : 'text-text-secondary hover:bg-bg-hover-surface'}`}>{label}</button>)}</div><div className="flex flex-wrap gap-2"><label className="relative flex min-w-[220px] items-center"><Search className="absolute left-3 h-4 w-4 text-text-tertiary" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search providers…" className="w-full rounded-md border border-border-subtle bg-bg-near-black py-2 pl-9 pr-3 text-sm text-text-primary" /></label><button onClick={() => setConfiguredOnly((value) => !value)} className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${configuredOnly ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300' : 'border-border-subtle text-text-secondary'}`}><SlidersHorizontal className="h-4 w-4" />Configured only</button></div></div>

      {panel === 'governance' ? <GovernancePanel /> : <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">{visibleProviders.map((provider) => <ProviderCard key={provider.id} provider={provider} />)}{!visibleProviders.length && <div className="col-span-full rounded-md border border-dashed border-border-subtle p-10 text-center text-sm text-text-tertiary">No provider contracts match this filter.</div>}</div>}
      <p className="text-xs text-text-tertiary">{generatedAt ? `State snapshot: ${new Date(generatedAt).toLocaleString()}.` : 'State snapshot pending.'} Configuration status is secret-presence only; it is not a provider health probe.</p>
    </div>
  );
}

function ProviderCard({ provider }: { provider: ProviderRuntime }) {
  return <article className="rounded-lg border border-border-subtle bg-bg-dark-surface p-5 shadow-card"><div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-2"><h3 className="font-semibold text-text-primary">{provider.name}</h3><span className="rounded bg-bg-hover-surface px-2 py-0.5 text-[10px] uppercase tracking-wider text-text-tertiary">{providerCategoryLabel(provider.category)}</span></div><p className="mt-1 text-xs text-text-tertiary">{provider.id}</p></div><span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase ${statusClasses(provider)}`}>{provider.health === 'public-endpoint' ? 'Public adapter' : provider.configured ? 'Configured' : 'Needs config'}</span></div><div className="mt-4 flex flex-wrap gap-1.5">{provider.coverage.map((item) => <span key={item} className="rounded-full border border-border-subtle bg-bg-near-black px-2 py-1 text-xs text-text-secondary">{item}</span>)}</div><div className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2"><div><p className="text-xs uppercase tracking-wider text-text-tertiary">Adapter</p><p className="mt-1 text-text-secondary">{provider.wiring === 'wired' ? 'Wired into existing provider layer' : 'Adapter contract documented'}</p></div><div><p className="text-xs uppercase tracking-wider text-text-tertiary">Auth</p><p className="mt-1 text-text-secondary">{provider.auth === 'api-key' ? 'Edge secret' : provider.auth === 'account' ? 'OAuth/account consent' : 'Public endpoint'}</p></div></div><div className="mt-4 rounded-md border border-border-subtle bg-bg-near-black p-3 text-xs"><p className="font-semibold text-text-primary">Usage policy</p><p className="mt-1 text-text-secondary">{provider.quota}</p><p className="mt-2 text-text-tertiary">{provider.message}</p></div><details className="mt-3"><summary className="cursor-pointer text-xs font-semibold text-accent-primary">Data & legal guardrails</summary><div className="mt-2 space-y-2 text-xs text-text-secondary"><p>{provider.dataHandling}</p><p className="text-amber-200">{provider.legalNote}</p>{provider.envKeys.length ? <p className="font-mono text-text-tertiary">Secrets: {provider.envKeys.join(', ')}</p> : null}</div></details></article>;
}

function GovernancePanel() {
  return <div className="space-y-4"><section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card"><h3 className="text-lg font-semibold text-text-primary">Enterprise provider rules</h3><div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">{['Never ship provider keys to the browser or GitHub.', 'Cache normalized observables before consuming a quota.', 'Record provider, timestamp, query type, and provenance with every enrichment.', 'Treat “unknown” as unknown—not clean—and expose provider failures.', 'Do not submit confidential URLs, mailbox content, or file bytes without explicit policy approval.', 'Review each provider’s current terms, retention, attribution, and commercial-use rules before production activation.'].map((rule, index) => <div key={rule} className="flex gap-3 rounded-md border border-border-subtle bg-bg-near-black p-4"><span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-violet-300/15 text-xs font-bold text-violet-200">{index + 1}</span><p className="text-sm text-text-secondary">{rule}</p></div>)}</div></section><section className="rounded-lg border border-border-subtle bg-bg-dark-surface p-6 shadow-card"><h3 className="text-lg font-semibold text-text-primary">Activation checklist</h3><ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-text-secondary"><li>Store each provider secret in Supabase Edge Function secrets, never Vite variables.</li><li>Run a low-volume health check in a controlled environment.</li><li>Confirm response retention and redistribution rules with legal/security owners.</li><li>Enable the adapter in the provider catalog only after a verified response contract test.</li><li>Monitor quota and error rates in Sync & Audit before increasing volume.</li></ol></section></div>;
}
