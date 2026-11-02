export type ProviderCategory = 'threat-intelligence' | 'email' | 'network' | 'domain' | 'url' | 'platform';

export type ProviderDefinition = {
  id: string;
  name: string;
  category: ProviderCategory;
  coverage: string[];
  auth: 'api-key' | 'account' | 'public';
  envKeys: string[];
  wiring: 'wired' | 'adapter-ready';
  quota: string;
  dataHandling: string;
  legalNote: string;
};

export type ProviderRuntime = ProviderDefinition & {
  configured: boolean;
  secretNames: string[];
  lastKnownUsage?: number;
  health: 'ready' | 'needs-configuration' | 'public-endpoint' | 'not-checked';
  message: string;
};

/**
 * Provider manifest. This is metadata only: no secret or provider response is
 * shipped to the browser. The edge function resolves configured state from
 * Supabase secrets and the UI renders the result.
 */
export const PROVIDER_CATALOG: ProviderDefinition[] = [
  {
    id: 'virustotal', name: 'VirusTotal', category: 'threat-intelligence', coverage: ['file hash', 'URL', 'domain', 'IP'], auth: 'api-key', envKeys: ['VIRUSTOTAL_API_KEY'], wiring: 'wired', quota: 'Plan-dependent; cache before lookup.', dataHandling: 'Send hashes/observables only; never upload raw email by default.', legalNote: 'Review VirusTotal terms before redistributing vendor results.',
  },
  {
    id: 'abuseipdb', name: 'AbuseIPDB', category: 'threat-intelligence', coverage: ['IP reputation', 'abuse reports'], auth: 'api-key', envKeys: ['ABUSEIPDB_API_KEY'], wiring: 'wired', quota: 'Plan-dependent daily quota.', dataHandling: 'IP observables and lookup metadata.', legalNote: 'Respect provider attribution and redistribution rules.',
  },
  {
    id: 'google_safe_browsing', name: 'Google Safe Browsing', category: 'url', coverage: ['phishing URL', 'malware URL', 'unwanted software'], auth: 'api-key', envKeys: ['GOOGLE_SAFE_BROWSING_API_KEY'], wiring: 'wired', quota: 'Google Cloud project quota.', dataHandling: 'Canonical URLs only; avoid sending message bodies.', legalNote: 'Use results according to Google API terms and display requirements.',
  },
  {
    id: 'otx', name: 'AlienVault OTX', category: 'threat-intelligence', coverage: ['IP', 'domain', 'URL', 'hash', 'pulses'], auth: 'api-key', envKeys: ['OTX_API_KEY', 'ALIENVAULT_OTX_API_KEY'], wiring: 'wired', quota: 'Provider limits are not consistently published; pace conservatively.', dataHandling: 'Indicators and pulse metadata.', legalNote: 'Community data may have source-specific sharing restrictions.',
  },
  {
    id: 'shodan', name: 'Shodan', category: 'network', coverage: ['IP', 'services', 'banners'], auth: 'api-key', envKeys: ['SHODAN_API_KEY'], wiring: 'wired', quota: 'Plan and scan-credit dependent.', dataHandling: 'Public internet service metadata.', legalNote: 'Do not use results to conduct unauthorized scanning.',
  },
  {
    id: 'securitytrails', name: 'SecurityTrails', category: 'domain', coverage: ['DNS', 'WHOIS history', 'domain/IP'], auth: 'api-key', envKeys: ['SECURITYTRAILS_API_KEY'], wiring: 'wired', quota: 'Plan-dependent monthly quota.', dataHandling: 'Domain and DNS observables.', legalNote: 'Check commercial redistribution terms before exporting history.',
  },
  {
    id: 'urlhaus', name: 'URLhaus', category: 'url', coverage: ['malware URLs', 'payloads', 'hostnames'], auth: 'public', envKeys: [], wiring: 'wired', quota: 'Respect abuse.ch request guidance.', dataHandling: 'URLs and malware metadata.', legalNote: 'Preserve abuse.ch attribution and source provenance.',
  },
  {
    id: 'phishtank', name: 'PhishTank', category: 'url', coverage: ['verified phishing URLs'], auth: 'account', envKeys: ['PHISHTANK_API_KEY', 'PHISHTANK_APP_KEY'], wiring: 'wired', quota: 'Registration and feed policy dependent.', dataHandling: 'URLs and verification metadata.', legalNote: 'Follow OpenDNS/PhishTank terms and do not imply endorsement.',
  },
  {
    id: 'malwarebazaar', name: 'MalwareBazaar', category: 'threat-intelligence', coverage: ['malware hashes', 'samples', 'signatures'], auth: 'public', envKeys: ['MALWAREBAZAAR_API_KEY'], wiring: 'wired', quota: 'Abuse.ch request guidance.', dataHandling: 'Hashes by default; never download samples automatically.', legalNote: 'Sample access is high risk; require explicit analyst action and legal approval.',
  },
  {
    id: 'threatfox', name: 'ThreatFox', category: 'threat-intelligence', coverage: ['IOCs', 'malware families', 'campaign context'], auth: 'public', envKeys: ['THREATFOX_API_KEY'], wiring: 'wired', quota: 'Abuse.ch request guidance.', dataHandling: 'Indicators and malware context.', legalNote: 'Preserve source attribution and do not redistribute raw feeds without review.',
  },
  {
    id: 'circl_hashlookup', name: 'CIRCL Hashlookup', category: 'threat-intelligence', coverage: ['MD5', 'SHA-1', 'SHA-256'], auth: 'account', envKeys: ['CIRCL_USERNAME', 'CIRCL_PASSWORD'], wiring: 'wired', quota: 'Provider service limits.', dataHandling: 'File hashes only.', legalNote: 'Use only for authorized investigation workflows.',
  },
  {
    id: 'spamhaus', name: 'Spamhaus', category: 'threat-intelligence', coverage: ['IP/domain blocklists'], auth: 'account', envKeys: ['SPAMHAUS_API_KEY'], wiring: 'wired', quota: 'Dataset and commercial access dependent.', dataHandling: 'IP/domain indicators.', legalNote: 'Spamhaus datasets have strict use and redistribution conditions.',
  },
  {
    id: 'greynoise', name: 'GreyNoise', category: 'network', coverage: ['IP noise', 'scanning context', 'classification'], auth: 'api-key', envKeys: ['GREYNOISE_API_KEY'], wiring: 'wired', quota: 'Community or plan-dependent quota.', dataHandling: 'IP observables and classification.', legalNote: 'Follow GreyNoise license and plan restrictions.',
  },
  {
    id: 'ipqualityscore', name: 'IPQualityScore', category: 'platform', coverage: ['email fraud', 'URL risk', 'IP fraud', 'domain risk'], auth: 'api-key', envKeys: ['IPQS_API_KEY', 'IPQUALITYSCORE_API_KEY'], wiring: 'adapter-ready', quota: 'Plan-dependent monthly quota.', dataHandling: 'Email/IP/domain/URL observables.', legalNote: 'Confirm permitted use for personal data and fraud decisions.',
  },
  {
    id: 'freeipapi', name: 'FreeIPAPI', category: 'network', coverage: ['IP geolocation', 'ISP'], auth: 'public', envKeys: [], wiring: 'wired', quota: 'Public endpoint; conservative pacing.', dataHandling: 'IP address.', legalNote: 'Review public endpoint terms and avoid bulk scraping.',
  },
  {
    id: 'ipapi', name: 'IP-API / IPWhois fallback', category: 'network', coverage: ['IP geolocation', 'ASN', 'ISP'], auth: 'public', envKeys: [], wiring: 'wired', quota: 'Public tier limits apply.', dataHandling: 'IP address.', legalNote: 'Do not use geolocation as a sole security decision.',
  },
  {
    id: 'quick_email_verification', name: 'Quick Email Verification', category: 'email', coverage: ['syntax', 'MX', 'SMTP', 'catch-all', 'disposable'], auth: 'api-key', envKeys: ['QUICK_EMAIL_API_KEY', 'EMAIL_VALIDATION_API_KEY'], wiring: 'adapter-ready', quota: 'Plan-dependent monthly quota.', dataHandling: 'Email address and domain only.', legalNote: 'Minimize retention of email addresses and comply with privacy law.',
  },
  {
    id: 'urlscan', name: 'URLScan.io', category: 'url', coverage: ['redirects', 'DOM', 'screenshot', 'JavaScript'], auth: 'api-key', envKeys: ['URLSCAN_API_KEY'], wiring: 'adapter-ready', quota: 'Public submission and visibility policy dependent.', dataHandling: 'URLs can become visible to third parties; use private scans only when permitted.', legalNote: 'Never submit confidential links without an approved privacy setting.',
  },
  {
    id: 'cloudflare_dns', name: 'Cloudflare DNS over HTTPS', category: 'domain', coverage: ['A', 'MX', 'TXT', 'NS', 'SPF', 'DMARC'], auth: 'public', envKeys: [], wiring: 'wired', quota: 'Public resolver policy applies.', dataHandling: 'Domain names.', legalNote: 'Resolver responses are enrichment, not proof of ownership.',
  },
  {
    id: 'rdap', name: 'RDAP', category: 'domain', coverage: ['registration date', 'registrar', 'status'], auth: 'public', envKeys: [], wiring: 'wired', quota: 'Registry and RDAP service limits.', dataHandling: 'Domain names.', legalNote: 'Registration data may be incomplete or privacy-protected.',
  },
  {
    id: 'whoisjson', name: 'WhoisJSON', category: 'domain', coverage: ['WHOIS', 'registration age'], auth: 'public', envKeys: ['WHOISJSON_API_KEY'], wiring: 'wired', quota: 'Service-specific limits.', dataHandling: 'Domain names.', legalNote: 'Use registration data for security context, not identity profiling.',
  },
  {
    id: 'ssl_labs', name: 'SSL Labs', category: 'domain', coverage: ['TLS certificate', 'cipher posture', 'grade'], auth: 'public', envKeys: [], wiring: 'wired', quota: 'Public scan queue limits.', dataHandling: 'Public hostnames.', legalNote: 'Only scan domains you are authorized to assess.',
  },
  {
    id: 'emailrep', name: 'EmailRep.io', category: 'email', coverage: ['email reputation', 'disposable', 'profiles'], auth: 'public', envKeys: ['EMAILREP_API_KEY'], wiring: 'wired', quota: 'Public endpoint limits.', dataHandling: 'Email address; treat as personal data.', legalNote: 'Apply data minimization and access controls.',
  },
  {
    id: 'debounce_disposable', name: 'Debounce disposable check', category: 'email', coverage: ['disposable email domain'], auth: 'public', envKeys: [], wiring: 'wired', quota: 'Public endpoint limits.', dataHandling: 'Email address.', legalNote: 'Do not use disposable status as an automated denial without policy review.',
  },
  {
    id: 'microsoft_graph', name: 'Microsoft Graph / M365', category: 'platform', coverage: ['mailbox telemetry', 'message trace', 'security events'], auth: 'account', envKeys: ['MICROSOFT_TENANT_ID', 'MICROSOFT_CLIENT_ID', 'MICROSOFT_CLIENT_SECRET'], wiring: 'adapter-ready', quota: 'Tenant and Graph throttling policies.', dataHandling: 'Highly sensitive mailbox and tenant data.', legalNote: 'Requires tenant consent, least privilege, DPA, and strict retention controls.',
  },
  {
    id: 'gmail_api', name: 'Gmail API', category: 'platform', coverage: ['mailbox telemetry', 'message headers', 'security events'], auth: 'account', envKeys: ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET'], wiring: 'adapter-ready', quota: 'Google project and user quota.', dataHandling: 'Highly sensitive mailbox data.', legalNote: 'Requires OAuth consent, restricted scopes review, and Google API policies.',
  },
];

export function getProviderDefinition(id: string) {
  return PROVIDER_CATALOG.find((provider) => provider.id === id);
}

export function providerCategoryLabel(category: ProviderCategory) {
  return category === 'threat-intelligence' ? 'Threat intelligence' : category.charAt(0).toUpperCase() + category.slice(1);
}
