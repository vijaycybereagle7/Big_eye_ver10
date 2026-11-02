const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

type ProviderConfig = {
  keys: string[];
  any?: boolean;
  public?: boolean;
  wired: boolean;
};

const providerConfig: Record<string, ProviderConfig> = {
  virustotal: { keys: ['VIRUSTOTAL_API_KEY'], wired: true },
  abuseipdb: { keys: ['ABUSEIPDB_API_KEY'], wired: true },
  google_safe_browsing: { keys: ['GOOGLE_SAFE_BROWSING_API_KEY'], wired: true },
  otx: { keys: ['OTX_API_KEY', 'ALIENVAULT_OTX_API_KEY'], any: true, wired: true },
  shodan: { keys: ['SHODAN_API_KEY'], wired: true },
  securitytrails: { keys: ['SECURITYTRAILS_API_KEY'], wired: true },
  urlhaus: { keys: [], public: true, wired: true },
  phishtank: { keys: ['PHISHTANK_API_KEY', 'PHISHTANK_APP_KEY'], any: true, wired: true },
  malwarebazaar: { keys: [], public: true, wired: true },
  threatfox: { keys: [], public: true, wired: true },
  circl_hashlookup: { keys: ['CIRCL_USERNAME', 'CIRCL_PASSWORD'], wired: true },
  spamhaus: { keys: ['SPAMHAUS_API_KEY'], wired: true },
  greynoise: { keys: ['GREYNOISE_API_KEY'], wired: true },
  ipqualityscore: { keys: ['IPQS_API_KEY', 'IPQUALITYSCORE_API_KEY'], any: true, wired: false },
  freeipapi: { keys: [], public: true, wired: true },
  ipapi: { keys: [], public: true, wired: true },
  quick_email_verification: { keys: ['QUICK_EMAIL_API_KEY', 'EMAIL_VALIDATION_API_KEY'], any: true, wired: false },
  urlscan: { keys: ['URLSCAN_API_KEY'], wired: false },
  cloudflare_dns: { keys: [], public: true, wired: true },
  rdap: { keys: [], public: true, wired: true },
  whoisjson: { keys: ['WHOISJSON_API_KEY'], wired: true },
  ssl_labs: { keys: [], public: true, wired: true },
  emailrep: { keys: ['EMAILREP_API_KEY'], wired: true },
  debounce_disposable: { keys: [], public: true, wired: true },
  microsoft_graph: { keys: ['MICROSOFT_TENANT_ID', 'MICROSOFT_CLIENT_ID', 'MICROSOFT_CLIENT_SECRET'], wired: false },
  gmail_api: { keys: ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET'], wired: false },
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 200, headers: corsHeaders });

  const generatedAt = new Date().toISOString();
  const providers = Object.entries(providerConfig).map(([id, config]) => {
    const configuredKeys = config.keys.filter((key) => Boolean(Deno.env.get(key)?.trim()));
    const configured = config.public || (config.any ? configuredKeys.length > 0 : configuredKeys.length === config.keys.length);
    return {
      id,
      configured,
      wired: config.wired,
      health: config.public ? 'public-endpoint' : configured ? 'ready' : 'needs-configuration',
      secretNames: config.keys,
      configuredSecretCount: configuredKeys.length,
      message: config.public
        ? 'Public adapter available; rate-limit and terms checks still apply.'
        : configured
          ? 'Required secret(s) detected in Supabase Edge Function environment.'
          : 'No usable secret configured. The provider is not queried.',
    };
  });

  return new Response(JSON.stringify({
    data: {
      providers,
      generatedAt,
      secretsNotExposed: true,
      usage: [],
      note: 'Configured state is based on secret presence, not a live provider probe. No provider request is made by this endpoint.',
    },
  }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
});
