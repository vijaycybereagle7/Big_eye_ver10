import { isSupabaseConfigured, supabase } from './supabase';

export type RiskLevel = 'safe' | 'low' | 'medium' | 'high' | 'critical';
export type FindingSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

export interface SecurityFinding {
  id: string;
  category: 'phishing' | 'malware' | 'authentication' | 'platform' | 'link' | 'reputation';
  severity: FindingSeverity;
  title: string;
  evidence: string;
  recommendation: string;
}

export interface SecurityAnalysisResult {
  scanId: string;
  contentHash: string;
  generatedAt: string;
  source: 'supabase' | 'offline';
  parsedEmail: {
    senderEmail: string;
    senderDomain: string;
    senderName: string;
    subject: string;
    linkCount: number;
    links: string[];
    attachments: Array<{ filename: string; contentType?: string }>;
  };
  comprehensiveVerdict: {
    overallVerdict: 'ALLOW' | 'REVIEW' | 'QUARANTINE' | 'BLOCK';
    riskLevel: RiskLevel;
    confidenceScore: number;
    overallScore: number;
    recommendation: string;
    summary: string;
    toolsExecuted: number;
    totalToolsAvailable: number;
  };
  findings: SecurityFinding[];
  engineStatus: Array<{
    id: string;
    label: string;
    score: number;
    status: 'clear' | 'attention' | 'alert' | 'not-run';
    detail: string;
  }>;
  individualAnalyses: Record<string, any>;
  remediation: string[];
  sync?: SyncInfo;
}

export interface SyncInfo {
  status: 'synced' | 'offline' | 'local-only' | 'degraded' | 'failed';
  message: string;
  recordId?: string;
  incidentId?: string;
  timestamp: string;
}

export interface SyncSnapshot {
  mode: 'synced' | 'degraded' | 'offline' | 'not-authenticated';
  configured: boolean;
  authenticated: boolean;
  lastSync: string | null;
  scans: any[];
  incidents: any[];
  watchlist: any[];
  apiUsage: any[];
  localScans: StoredScan[];
  errors: string[];
}

export interface StoredScan {
  id: string;
  createdAt: string;
  verdict: string;
  riskLevel: RiskLevel;
  score: number;
  senderDomain: string;
  subject: string;
  source: 'supabase' | 'offline';
  findingCount: number;
  result: SecurityAnalysisResult;
}

const HISTORY_KEY = 'big-eye.security-scan-history.v8';
const WATCHLIST_KEY = 'big-eye.security-watchlist.v8';
const ALLOW_OFFLINE_FALLBACK = ((import.meta.env || {}) as ImportMetaEnv).VITE_ALLOW_OFFLINE_FALLBACK !== 'false';

const DISPOSABLE_DOMAINS = new Set([
  '10minutemail.com', 'guerrillamail.com', 'mailinator.com', 'temp-mail.org',
  'temp-mail.io', 'tempmail.com', 'throwaway.email', 'trashmail.com',
  'yopmail.com', 'maildrop.cc', 'getnada.com', 'mohmal.com', 'mail.tm',
  'mail.gw', 'sharklasers.com', 'fakeinbox.com', 'dispostable.com',
]);

const URL_SHORTENERS = new Set(['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'rb.gy']);
const BRAND_DOMAINS: Record<string, string[]> = {
  paypal: ['paypal.com'],
  microsoft: ['microsoft.com', 'live.com', 'office.com'],
  google: ['google.com', 'gmail.com'],
  amazon: ['amazon.com'],
  apple: ['apple.com', 'icloud.com'],
  netflix: ['netflix.com'],
  dhl: ['dhl.com'],
  fedex: ['fedex.com'],
  bank: [],
};
const PHISHING_EXTENSIONS = new Set([
  '.exe', '.scr', '.js', '.jse', '.vbs', '.vbe', '.wsf', '.wsh', '.ps1', '.bat',
  '.cmd', '.com', '.hta', '.dll', '.msi', '.lnk', '.iso', '.img', '.jar', '.apk',
  '.docm', '.xlsm', '.pptm', '.zip', '.rar', '.7z',
]);

function makeId(prefix = 'scan'): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return `${prefix}_${crypto.randomUUID()}`;
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

function clamp(value: number, min = 0, max = 100): number {
  return Math.min(max, Math.max(min, Math.round(value)));
}

function riskFromScore(score: number): RiskLevel {
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 35) return 'medium';
  if (score >= 15) return 'low';
  return 'safe';
}

function verdictFromRisk(risk: RiskLevel): SecurityAnalysisResult['comprehensiveVerdict']['overallVerdict'] {
  if (risk === 'critical') return 'BLOCK';
  if (risk === 'high') return 'QUARANTINE';
  if (risk === 'medium') return 'REVIEW';
  return 'ALLOW';
}

function engineStatus(score: number, notRun = false): 'clear' | 'attention' | 'alert' | 'not-run' {
  if (notRun) return 'not-run';
  if (score >= 60) return 'alert';
  if (score >= 25) return 'attention';
  return 'clear';
}

function cleanUrl(url: string): string {
  return url.replace(/[),.;:'"\]}]+$/g, '');
}

function parseHeaderMap(headerText: string): Map<string, string> {
  const map = new Map<string, string>();
  let current = '';
  let value = '';

  for (const line of headerText.replace(/\r\n/g, '\n').split('\n')) {
    if (/^\s/.test(line) && current) {
      value += ` ${line.trim()}`;
      continue;
    }
    if (current) map.set(current, value.trim());
    const separator = line.indexOf(':');
    if (separator <= 0) {
      current = '';
      value = '';
      continue;
    }
    current = line.slice(0, separator).trim().toLowerCase();
    value = line.slice(separator + 1).trim();
  }
  if (current) map.set(current, value.trim());
  return map;
}

function extractMailbox(value: string): { email: string; name: string } {
  const match = value.match(/<([^>]+)>/);
  if (match) {
    return {
      email: match[1].trim().toLowerCase(),
      name: value.replace(match[0], '').replace(/["']/g, '').trim(),
    };
  }
  const emailMatch = value.match(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/i);
  return { email: emailMatch?.[0]?.toLowerCase() || value.trim().toLowerCase(), name: '' };
}

function parseEmail(rawInput: string) {
  const normalized = rawInput.replace(/\r\n/g, '\n');
  const separator = normalized.search(/\n\s*\n/);
  const headersText = separator >= 0 ? normalized.slice(0, separator) : normalized;
  const body = separator >= 0 ? normalized.slice(separator).replace(/^\s+/, '') : '';
  const headers = parseHeaderMap(headersText);
  const from = extractMailbox(headers.get('from') || '');
  const senderDomain = from.email.split('@')[1] || '';
  const links = Array.from(body.matchAll(/https?:\/\/[^\s<>"']+/gi)).map((match) => cleanUrl(match[0]));
  const attachmentMatches = Array.from(normalized.matchAll(/(?:filename|name)\s*=\s*["']?([^"';\s]+)["']?/gi));
  const attachments = attachmentMatches.map((match) => ({ filename: match[1] })).filter((item, index, all) => (
    all.findIndex((candidate) => candidate.filename.toLowerCase() === item.filename.toLowerCase()) === index
  ));

  return {
    normalized,
    headersText,
    body,
    headers,
    senderEmail: from.email,
    senderName: from.name,
    senderDomain,
    subject: headers.get('subject') || '',
    replyTo: headers.get('reply-to') || '',
    returnPath: headers.get('return-path') || '',
    links,
    attachments,
  };
}

function authStatus(headers: Map<string, string>, type: 'spf' | 'dkim' | 'dmarc'): string {
  const auth = headers.get('authentication-results') || '';
  const receivedSpf = headers.get('received-spf') || '';
  if (type === 'spf' && receivedSpf) {
    const result = receivedSpf.match(/^(pass|fail|softfail|neutral|none|temperror|permerror)/i);
    if (result) return result[1].toLowerCase();
  }
  const result = auth.match(new RegExp(`${type}=([^\\s;]+)`, 'i'));
  return result?.[1]?.toLowerCase() || 'none';
}

function domainFromMailbox(value: string): string {
  return (value.match(/@([^\s>]+)/)?.[1] || '').replace(/[>;,]/g, '').toLowerCase();
}

function makeFinding(
  category: SecurityFinding['category'],
  severity: FindingSeverity,
  title: string,
  evidence: string,
  recommendation: string,
): SecurityFinding {
  return { id: makeId('finding'), category, severity, title, evidence, recommendation };
}

function severityForScore(score: number): FindingSeverity {
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 35) return 'medium';
  return 'low';
}

function levenshtein(left: string, right: string): number {
  const row = Array.from({ length: right.length + 1 }, (_, index) => index);
  for (let i = 1; i <= left.length; i += 1) {
    let diagonal = row[0];
    row[0] = i;
    for (let j = 1; j <= right.length; j += 1) {
      const above = row[j];
      row[j] = left[i - 1] === right[j - 1]
        ? diagonal
        : Math.min(row[j] + 1, row[j - 1] + 1, diagonal + 1);
      diagonal = above;
    }
  }
  return row[right.length];
}

function isLookalike(domain: string, official: string): boolean {
  if (!domain || domain === official || !domain.endsWith(`.${official.split('.').slice(-2).join('.')}`)) return false;
  const left = domain.split('.')[0];
  const brand = official.split('.')[0];
  return left.length >= 4 && levenshtein(left, brand) <= 2;
}

function analyzeHeaders(parsed: ReturnType<typeof parseEmail>): { result: any; findings: SecurityFinding[] } {
  const { headers, headersText } = parsed;
  const spf = authStatus(headers, 'spf');
  const dkim = authStatus(headers, 'dkim');
  const dmarc = authStatus(headers, 'dmarc');
  const anomalies: string[] = [];
  const findings: SecurityFinding[] = [];
  let score = 0;

  const checks = [
    ['SPF', spf],
    ['DKIM', dkim],
    ['DMARC', dmarc],
  ] as const;
  for (const [name, status] of checks) {
    if (status === 'fail' || status === 'permerror') {
      score += name === 'DMARC' ? 30 : 25;
      anomalies.push(`${name} authentication failed (${status})`);
    } else if (status === 'softfail' || status === 'none' || status === 'neutral') {
      score += name === 'DMARC' ? 15 : 10;
      if (status === 'none') anomalies.push(`${name} result is missing`);
    }
  }

  const fromDomain = domainFromMailbox(headers.get('from') || '');
  const returnDomain = domainFromMailbox(headers.get('return-path') || '');
  const replyDomain = domainFromMailbox(headers.get('reply-to') || '');
  if (fromDomain && returnDomain && fromDomain !== returnDomain) {
    score += 20;
    anomalies.push(`From domain ${fromDomain} differs from Return-Path ${returnDomain}`);
    findings.push(makeFinding('authentication', 'high', 'Envelope sender mismatch', anomalies[anomalies.length - 1], 'Verify the sender through a trusted channel before taking action.'));
  }
  if (fromDomain && replyDomain && fromDomain !== replyDomain) {
    score += 20;
    anomalies.push(`From domain ${fromDomain} differs from Reply-To ${replyDomain}`);
    findings.push(makeFinding('phishing', 'high', 'Reply-To impersonation risk', anomalies[anomalies.length - 1], 'Do not reply or follow instructions until the destination is verified.'));
  }
  if (!headers.get('message-id')) {
    score += 8;
    anomalies.push('Message-ID header is missing');
  }
  if (!headers.get('date')) {
    score += 5;
    anomalies.push('Date header is missing');
  }
  if (!headers.get('received')) {
    score += 8;
    anomalies.push('Received routing headers are missing');
  }
  if (headers.get('x-mailer')?.toLowerCase().includes('phpmailer')) {
    score += 12;
    anomalies.push('PHPMailer header detected; common in low-cost campaign infrastructure');
  }
  if (score >= 25) {
    findings.push(makeFinding('authentication', severityForScore(score), 'Email authentication posture needs review', anomalies.slice(0, 3).join('; '), 'Inspect SPF, DKIM, DMARC alignment and the originating relay.'));
  }

  const receivedHops = Array.from(headersText.matchAll(/^Received:\s*(.+?)(?=\n(?![\s]))/gim)).map((match) => {
    const hop = match[1];
    return {
      server: hop.match(/from\s+([^\s]+)/i)?.[1] || 'unknown',
      ip: hop.match(/\[((?:\d{1,3}\.){3}\d{1,3})\]/)?.[1] || '',
      timestamp: hop.match(/;\s*(.+)$/)?.[1]?.trim() || '',
      rawText: hop,
    };
  }).reverse();

  return {
    result: {
      from: headers.get('from') || '',
      to: headers.get('to') || '',
      subject: headers.get('subject') || '',
      returnPath: headers.get('return-path') || '',
      replyTo: headers.get('reply-to') || '',
      spf: { status: spf, details: headers.get('received-spf') || '' },
      dkim: { status: dkim, details: headers.get('authentication-results') || '' },
      dmarc: { status: dmarc, details: headers.get('authentication-results') || '' },
      receivedHops,
      anomalies,
      threatScore: clamp(score),
    },
    findings,
  };
}

function analyzeLinks(parsed: ReturnType<typeof parseEmail>): { result: any; findings: SecurityFinding[] } {
  const findings: SecurityFinding[] = [];
  const links = parsed.links.map((url) => {
    try {
      const parsedUrl = new URL(url);
      const domain = parsedUrl.hostname.toLowerCase();
      const indicators: string[] = [];
      const warnings: string[] = [];
      let score = 0;
      if (parsedUrl.protocol !== 'https:') {
        indicators.push('insecure protocol');
        warnings.push('HTTP transport does not protect the destination in transit');
        score += 15;
      }
      if (URL_SHORTENERS.has(domain)) {
        indicators.push('URL shortener');
        warnings.push('Destination is hidden behind a redirect service');
        score += 30;
      }
      if (/^(\d{1,3}\.){3}\d{1,3}$/.test(domain)) {
        indicators.push('IP literal host');
        score += 25;
      }
      if (domain.includes('xn--')) {
        indicators.push('punycode/homograph');
        score += 35;
      }
      if (url.includes('@') || /%[0-9a-f]{2}/i.test(url) || url.length > 180) {
        indicators.push('obfuscated or oversized URL');
        score += 20;
      }
      const lowerUrl = url.toLowerCase();
      if (/(login|verify|confirm|password|billing|suspended|secure|account)/.test(lowerUrl)) {
        indicators.push('credential-themed path');
        score += 15;
      }
      const brand = Object.keys(BRAND_DOMAINS).find((candidate) => lowerUrl.includes(candidate));
      if (brand && !BRAND_DOMAINS[brand].some((official) => domain === official || domain.endsWith(`.${official}`))) {
        indicators.push(`${brand} brand impersonation`);
        warnings.push(`The link mentions ${brand} but does not use an official ${brand} domain`);
        score += 35;
      }
      if (/^(javascript|data):/i.test(url)) {
        indicators.push('active content scheme');
        score += 60;
      }
      score = clamp(score);
      return { url, domain, protocol: parsedUrl.protocol, threatScore: score, threatLevel: riskFromScore(score), warnings, suspiciousIndicators: indicators };
    } catch {
      return { url, domain: 'unparseable', protocol: 'unknown', threatScore: 50, threatLevel: 'medium', warnings: ['URL could not be parsed safely'], suspiciousIndicators: ['parse failure'] };
    }
  });
  const score = links.length ? clamp(links.reduce((sum, link) => sum + link.threatScore, 0) / links.length) : 0;
  for (const link of links.filter((item) => item.threatScore >= 35).slice(0, 8)) {
    findings.push(makeFinding('link', severityForScore(link.threatScore), 'Suspicious link detected', `${link.domain}: ${link.suspiciousIndicators.join(', ')}`, 'Open the trusted site manually instead of following this message link.'));
  }
  return {
    result: {
      linksFound: links.length,
      linksAnalyzed: links.length,
      overallThreatScore: score,
      overallThreatLevel: riskFromScore(score),
      overallRecommendation: score >= 60 ? 'Quarantine the message and investigate links in a sandbox.' : score >= 30 ? 'Verify each destination before clicking.' : 'No strong URL indicators were detected.',
      statistics: { totalSuspicious: links.filter((link) => link.threatScore >= 35).length },
      links,
    },
    findings,
  };
}

function analyzePhishing(parsed: ReturnType<typeof parseEmail>, linkScore: number): { result: any; findings: SecurityFinding[] } {
  const lowerBody = parsed.body.toLowerCase();
  const lowerSubject = parsed.subject.toLowerCase();
  const lowerName = parsed.senderName.toLowerCase();
  const flags: string[] = [];
  const reasoning: string[] = [];
  const findings: SecurityFinding[] = [];
  let score = 0;
  const urgency = ['urgent', 'immediate', 'action required', 'verify', 'confirm', 'suspended', 'locked', 'expired', 'act now', 'within 24 hours', 'final notice'];
  const credentialPhrases = ['verify your account', 'confirm your identity', 'reset your password', 'update your information', 'login to', 'enter your password'];
  const moneyPhrases = ['invoice', 'refund', 'payment', 'gift card', 'wire transfer', 'prize', 'reward', 'bank'];
  const urgencyHits = urgency.filter((word) => lowerSubject.includes(word) || lowerBody.includes(word));
  const credentialHits = credentialPhrases.filter((phrase) => lowerBody.includes(phrase));
  const moneyHits = moneyPhrases.filter((phrase) => lowerSubject.includes(phrase) || lowerBody.includes(phrase));
  if (urgencyHits.length) {
    score += Math.min(25, urgencyHits.length * 8);
    flags.push(`Urgency language: ${urgencyHits.slice(0, 3).join(', ')}`);
  }
  if (credentialHits.length) {
    score += Math.min(30, credentialHits.length * 12);
    flags.push(`Credential request: ${credentialHits.slice(0, 2).join(', ')}`);
  }
  if (moneyHits.length) {
    score += Math.min(18, moneyHits.length * 7);
    flags.push(`Financial theme: ${moneyHits.slice(0, 3).join(', ')}`);
  }
  if (parsed.senderDomain.includes('xn--')) {
    score += 25;
    flags.push('Sender domain uses punycode');
  }
  const brand = Object.keys(BRAND_DOMAINS).find((candidate) => lowerName.includes(candidate) || lowerBody.includes(candidate));
  if (brand && parsed.senderDomain && !BRAND_DOMAINS[brand].some((official) => parsed.senderDomain === official || parsed.senderDomain.endsWith(`.${official}`))) {
    score += 30;
    flags.push(`Possible ${brand} impersonation from ${parsed.senderDomain}`);
    findings.push(makeFinding('phishing', 'high', 'Sender may be impersonating a known brand', `${parsed.senderName || 'Sender'} mentions ${brand}, but the address uses ${parsed.senderDomain}`, 'Verify the sender using the organization’s known website or phone number.'));
  }
  if (/<(form|input|script)\b/i.test(parsed.body)) {
    score += 25;
    flags.push('HTML form or active script found in body');
  }
  if (linkScore >= 35) score += Math.min(25, Math.round(linkScore / 3));
  if (flags.length) reasoning.push('Multiple social-engineering signals were found in the sender, subject, or body.');
  if (linkScore >= 35) reasoning.push('At least one link needs destination verification.');
  if (!flags.length && linkScore < 35) reasoning.push('No strong phishing language or impersonation signal was detected.');
  score = clamp(score);
  if (score >= 35) {
    findings.push(makeFinding('phishing', severityForScore(score), 'Phishing language or identity deception detected', flags.slice(0, 4).join('; '), score >= 60 ? 'Do not interact; quarantine and report the message.' : 'Confirm the sender independently before responding.'));
  }
  return {
    result: {
      phishingScore: score,
      confidence: clamp(45 + (parsed.senderEmail ? 10 : 0) + (parsed.subject ? 10 : 0) + (parsed.body ? 15 : 0) + (parsed.links.length ? 10 : 0)),
      riskLevel: riskFromScore(score),
      reasoning,
      redFlags: flags,
      recommendation: score >= 75 ? 'BLOCK - Strong phishing indicators detected.' : score >= 50 ? 'QUARANTINE - Verify through an independent channel.' : score >= 30 ? 'REVIEW - Treat links and requests with caution.' : 'ALLOW - Continue normal email safety practices.',
    },
    findings,
  };
}

function analyzeMalware(parsed: ReturnType<typeof parseEmail>, links: any[]): { result: any; findings: SecurityFinding[] } {
  const findings: SecurityFinding[] = [];
  const flags: string[] = [];
  let score = 0;
  for (const attachment of parsed.attachments) {
    const name = attachment.filename.toLowerCase();
    const extension = name.includes('.') ? `.${name.split('.').pop()}` : '';
    const doubleExtension = /\.(pdf|docx?|xlsx?|jpg|png|txt)\.(exe|scr|js|vbs|cmd|bat|hta|zip)$/i.test(name);
    if (PHISHING_EXTENSIONS.has(extension)) {
      score += extension.match(/\.(exe|scr|js|vbs|ps1|bat|cmd|hta|dll|msi|lnk|iso|img|jar|apk)/) ? 45 : 25;
      flags.push(`${attachment.filename}: risky ${extension} attachment`);
    }
    if (doubleExtension) {
      score += 35;
      flags.push(`${attachment.filename}: double-extension disguise`);
    }
    if (/macro|enable content|password.?protected|archive/i.test(parsed.body)) {
      score += 15;
      flags.push(`${attachment.filename}: message asks the recipient to enable content or open protected material`);
    }
  }
  for (const link of links) {
    if (/\.(exe|scr|js|vbs|ps1|zip|rar|7z)(\?|$)/i.test(link.url)) {
      score += 35;
      flags.push(`Download link detected: ${link.domain}`);
    }
  }
  score = clamp(score);
  if (score >= 25) {
    findings.push(makeFinding('malware', severityForScore(score), 'Potential malware delivery vector detected', flags.slice(0, 5).join('; '), 'Do not open the attachment. Submit the file hash to an approved malware sandbox or EDR workflow.'));
  }
  return {
    result: {
      threatScore: score,
      riskLevel: riskFromScore(score),
      status: score >= 60 ? 'quarantine' : score >= 25 ? 'review' : 'clear',
      attachments: parsed.attachments,
      suspiciousIndicators: flags,
      recommendation: score >= 60 ? 'QUARANTINE attachment(s) and inspect with an isolated malware sandbox.' : score >= 25 ? 'Do not open attachment(s) until independently scanned.' : 'No static malware delivery indicator found; hash-based scanning is still recommended.',
      scanScope: 'Static metadata and content indicators only; no file execution.',
    },
    findings,
  };
}

function analyzePlatform(parsed: ReturnType<typeof parseEmail>, headerScore: number): { result: any; findings: SecurityFinding[] } {
  const findings: SecurityFinding[] = [];
  const recommendations: string[] = [];
  const headers = parsed.headers;
  const spf = authStatus(headers, 'spf');
  const dkim = authStatus(headers, 'dkim');
  const dmarc = authStatus(headers, 'dmarc');
  let score = headerScore;
  if (!parsed.senderDomain) {
    score += 25;
    recommendations.push('No sender domain was parsed; the message is not suitable for trust decisions.');
  } else {
    recommendations.push('Confirm the sender domain has MX, SPF, DKIM, and a DMARC enforcement policy.');
  }
  if (dmarc === 'none') recommendations.push('DMARC result was not present in the message headers.');
  if (spf === 'fail' || dkim === 'fail' || dmarc === 'fail') recommendations.push('One or more authentication results failed; check alignment and relay authorization.');
  const senderDomain = parsed.senderDomain;
  const returnDomain = domainFromMailbox(parsed.returnPath);
  if (senderDomain && returnDomain && senderDomain !== returnDomain) {
    score += 15;
    findings.push(makeFinding('platform', 'high', 'Mail platform alignment issue', `Header From uses ${senderDomain}; Return-Path uses ${returnDomain}`, 'Review DMARC alignment and trusted relay configuration.'));
  }
  return {
    result: {
      domain: senderDomain,
      score: clamp(score),
      riskLevel: riskFromScore(score),
      checks: {
        spf: { status: spf, passed: spf === 'pass' },
        dkim: { status: dkim, passed: dkim === 'pass' },
        dmarc: { status: dmarc, passed: dmarc === 'pass' },
        mx: { status: senderDomain ? 'not-queried' : 'unavailable', passed: null },
        tls: { status: 'not-observable-from-message', passed: null },
      },
      recommendations,
      scope: 'Header-level platform posture. DNS and TLS checks require a live domain lookup.',
    },
    findings,
  };
}

function localDomainAnalysis(domainInput: string) {
  const domain = domainInput.toLowerCase().trim().replace(/^https?:\/\//, '').split('/')[0];
  const suspiciousTld = /\.(tk|ml|ga|cf|gq|top|zip|mov)$/i.test(domain);
  const punycode = domain.includes('xn--');
  const score = clamp((suspiciousTld ? 25 : 0) + (punycode ? 35 : 0) + (domain.includes('-') ? 8 : 0));
  return {
    domain,
    dns: { hasARecord: Boolean(domain), hasMXRecord: null, hasSPF: null, hasDMARC: null, status: 'offline-preview' },
    ssl: { hasSSL: null, httpsEnabled: null, message: 'Live TLS check requires Supabase edge function deployment.' },
    domainInfo: { ageInDays: null, registrar: 'Not queried in offline mode' },
    overallThreatScore: score,
    riskLevel: riskFromScore(score),
    recommendations: [
      'Deploy the Supabase domain function to run DNS, RDAP, and TLS checks.',
      ...(suspiciousTld ? ['Review the high-risk TLD before trusting the domain.'] : []),
      ...(punycode ? ['Inspect the Unicode rendering for a possible homograph attack.'] : []),
    ],
  };
}

function localEmailLegitimacy(email: string) {
  const normalized = email.trim().toLowerCase();
  const syntaxValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized);
  const domain = normalized.split('@')[1] || '';
  const disposable = DISPOSABLE_DOMAINS.has(domain);
  const threatScore = !syntaxValid ? 90 : disposable ? 70 : 0;
  return {
    email: normalized,
    syntaxValid,
    hasMXRecord: null,
    disposable,
    deliverable: null,
    riskLevel: riskFromScore(threatScore),
    threatScore,
    recommendation: !syntaxValid ? 'Invalid email format.' : disposable ? 'Treat as disposable and do not use for trusted identity verification.' : 'Syntax is valid; deploy live MX/SMTP checks for deliverability confidence.',
    externalValidation: { available: false, message: 'Offline preview: configure a validation provider in Supabase.' },
  };
}

function localIpAnalysis(ip: string) {
  const parts = ip.split('.').map(Number);
  const valid = parts.length === 4 && parts.every((part) => Number.isInteger(part) && part >= 0 && part <= 255);
  const isPrivate = valid && (parts[0] === 10 || (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) || (parts[0] === 192 && parts[1] === 168) || parts[0] === 127);
  const threatScore = valid && isPrivate ? 10 : valid ? 0 : 90;
  return {
    ip,
    threatScore,
    riskLevel: riskFromScore(threatScore),
    geolocation: { error: 'Live geolocation is only queried by the edge function.' },
    whois: { error: 'Live WHOIS is only queried by the edge function.' },
    recommendations: [valid ? (isPrivate ? 'Private/loopback address found; it is unusual in an internet-delivered message.' : 'Address syntax is valid; query threat feeds for reputation.') : 'Invalid IPv4 address.'],
  };
}

function localLinkAnalysis(url: string) {
  const parsed = parseEmail(`From: preview@example.com\n\n${url}`);
  return analyzeLinks(parsed).result.links[0] || { url, threatScore: 0, threatLevel: 'safe', warnings: [], suspiciousIndicators: [] };
}

function localApiUsage() {
  return { usage: [], message: 'No live API quota data in offline preview mode.' };
}

function localBulkAnalysis(body: any) {
  const emails = Array.isArray(body.emails) ? body.emails : [];
  const domains = Array.isArray(body.domains) ? body.domains : [];
  const ips = Array.isArray(body.ip_addresses) ? body.ip_addresses : [];
  const urls = Array.isArray(body.urls) ? body.urls : [];
  const detailedResults = {
    emails: emails.map((email: string) => {
      const item = localEmailLegitimacy(email);
      return { item: email, type: 'email', is_valid: item.syntaxValid, risk_level: item.riskLevel, threats: item.disposable ? [{ type: 'disposable_email', severity: 'medium', description: 'Disposable email address detected', source: 'Offline rules' }] : [], confidence_score: item.syntaxValid ? 0.7 : 0.95 };
    }),
    domains: domains.map((domain: string) => {
      const item = localDomainAnalysis(domain);
      return { item: domain, type: 'domain', is_valid: Boolean(item.domain.includes('.')), risk_level: item.riskLevel, threats: item.overallThreatScore ? [{ type: 'suspicious_domain', severity: item.riskLevel, description: 'Static domain indicators detected', source: 'Offline rules' }] : [], confidence_score: 0.65 };
    }),
    ip_addresses: ips.map((ip: string) => {
      const item = localIpAnalysis(ip);
      return { item: ip, type: 'ip_address', is_valid: item.riskLevel !== 'critical', risk_level: item.riskLevel, threats: [], confidence_score: 0.6 };
    }),
    urls: urls.map((url: string) => {
      const item = localLinkAnalysis(url);
      return { item: url, type: 'url', is_valid: item.threatLevel !== 'critical', risk_level: item.threatLevel.toLowerCase(), threats: item.warnings.map((description: string) => ({ type: 'suspicious_url', severity: item.threatLevel.toLowerCase(), description, source: 'Offline rules' })), confidence_score: 0.7 };
    }),
  };
  const all = Object.values(detailedResults).flat() as any[];
  const high = all.filter((item) => ['high', 'critical'].includes(item.risk_level)).length;
  const medium = all.filter((item) => item.risk_level === 'medium').length;
  return {
    analysis_type: body.analysis_type || 'comprehensive',
    total_items: all.length,
    summary: { threats_found: high + medium, high_risk_items: high, medium_risk_items: medium, low_risk_items: 0, clean_items: all.length - high - medium },
    detailed_results: detailedResults,
    recommendations: ['Offline preview uses deterministic static rules. Deploy Supabase functions for live DNS and threat-feed enrichment.'],
    analysis_duration: 0,
    threats_found: high + medium,
  };
}

async function hashText(value: string): Promise<string> {
  try {
    const bytes = new TextEncoder().encode(value);
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, '0')).join('');
  } catch {
    let hash = 2166136261;
    for (let index = 0; index < value.length; index += 1) hash = Math.imul(hash ^ value.charCodeAt(index), 16777619);
    return (hash >>> 0).toString(16).padStart(8, '0');
  }
}

async function runOfflineEmailAnalysis(emailContent: string): Promise<SecurityAnalysisResult> {
  const parsed = parseEmail(emailContent);
  const header = analyzeHeaders(parsed);
  const links = analyzeLinks(parsed);
  const phishing = analyzePhishing(parsed, links.result.overallThreatScore);
  const malware = analyzeMalware(parsed, links.result.links || []);
  const platform = analyzePlatform(parsed, header.result.threatScore);
  const findings = [...header.findings, ...links.findings, ...phishing.findings, ...malware.findings, ...platform.findings];
  const score = clamp(phishing.result.phishingScore * 0.42 + malware.result.threatScore * 0.3 + header.result.threatScore * 0.2 + links.result.overallThreatScore * 0.08);
  const riskLevel = riskFromScore(score);
  const verdict = verdictFromRisk(riskLevel);
  const confidence = clamp(45 + (parsed.headersText ? 15 : 0) + (parsed.body ? 15 : 0) + (parsed.senderEmail ? 10 : 0) + (parsed.links.length ? 8 : 0) + (parsed.attachments.length ? 5 : 0));
  const remediation = [
    ...(verdict === 'BLOCK' || verdict === 'QUARANTINE' ? ['Quarantine the message and preserve headers for incident response.'] : []),
    ...(malware.result.threatScore >= 25 ? ['Hash and detonate attachments only in an approved isolated malware workflow.'] : []),
    ...(header.result.threatScore >= 25 ? ['Review sender authentication and domain alignment in the mail platform.'] : []),
    ...(links.result.overallThreatScore >= 30 ? ['Open destinations manually from a trusted bookmark, not from the message.'] : []),
    'Never treat a static score as proof of safety; confirm high-impact requests out of band.',
  ];
  const summary = findings.length
    ? `${verdict} recommendation: ${findings.length} finding${findings.length === 1 ? '' : 's'} across phishing, malware, authentication, and link engines.`
    : 'No strong static threat indicators were found. Live reputation and DNS checks are still recommended.';
  const result: SecurityAnalysisResult = {
    scanId: makeId(),
    contentHash: await hashText(emailContent),
    generatedAt: new Date().toISOString(),
    source: 'offline',
    parsedEmail: {
      senderEmail: parsed.senderEmail,
      senderDomain: parsed.senderDomain,
      senderName: parsed.senderName,
      subject: parsed.subject,
      linkCount: parsed.links.length,
      links: parsed.links,
      attachments: parsed.attachments,
    },
    comprehensiveVerdict: {
      overallVerdict: verdict,
      riskLevel,
      confidenceScore: confidence,
      overallScore: score,
      recommendation: verdict === 'BLOCK' ? 'BLOCK - Do not interact with this message.' : verdict === 'QUARANTINE' ? 'QUARANTINE - Escalate for security review.' : verdict === 'REVIEW' ? 'REVIEW - Verify sender and requested action independently.' : 'ALLOW WITH CAUTION - Continue normal email safety practices.',
      summary,
      toolsExecuted: 6,
      totalToolsAvailable: 6,
    },
    findings,
    engineStatus: [
      { id: 'phishing', label: 'Phishing & impersonation', score: phishing.result.phishingScore, status: engineStatus(phishing.result.phishingScore), detail: `${phishing.result.redFlags.length} signal(s)` },
      { id: 'malware', label: 'Malware delivery triage', score: malware.result.threatScore, status: engineStatus(malware.result.threatScore), detail: `${malware.result.suspiciousIndicators.length} indicator(s)` },
      { id: 'authentication', label: 'SPF / DKIM / DMARC', score: header.result.threatScore, status: engineStatus(header.result.threatScore), detail: `${header.result.anomalies.length} anomaly(ies)` },
      { id: 'links', label: 'Link reputation', score: links.result.overallThreatScore, status: engineStatus(links.result.overallThreatScore), detail: `${links.result.linksFound} link(s) inspected` },
      { id: 'platform', label: 'Mail platform posture', score: platform.result.score, status: engineStatus(platform.result.score), detail: parsed.senderDomain ? 'Header posture available' : 'Sender domain missing' },
      { id: 'reputation', label: 'External reputation feeds', score: 0, status: 'not-run', detail: 'Configure edge functions and provider keys' },
    ],
    individualAnalyses: {
      emailHeaderAnalysis: header.result,
      domainAnalysis: parsed.senderDomain ? localDomainAnalysis(parsed.senderDomain) : { error: true, message: 'No sender domain found' },
      legitimacyAnalysis: parsed.senderEmail ? localEmailLegitimacy(parsed.senderEmail) : { error: true, message: 'No sender email found' },
      blacklistAnalysis: { error: true, message: 'No public IP was found; live blacklist lookup not run' },
      ipAnalysis: { error: true, message: 'No public IP was found in the pasted headers' },
      phishingAnalysis: phishing.result,
      tempEmailAnalysis: parsed.senderEmail ? { ...localEmailLegitimacy(parsed.senderEmail), isTemporary: DISPOSABLE_DOMAINS.has(parsed.senderDomain), isFreemail: ['gmail.com', 'outlook.com', 'yahoo.com'].includes(parsed.senderDomain), domain: parsed.senderDomain, confidence: DISPOSABLE_DOMAINS.has(parsed.senderDomain) ? 98 : 75 } : { error: true, message: 'No sender email found' },
      domainAgeAnalysis: parsed.senderDomain ? { domain: parsed.senderDomain, ageInDays: null, ageDescription: 'Live lookup not run', threatScore: 0, riskLevel: 'safe' } : { error: true, message: 'No sender domain found' },
      linkAnalysis: links.result,
      malwareAnalysis: malware.result,
      platformAnalysis: platform.result,
    },
    remediation,
  };
  return result;
}

async function localInvoke(functionName: string, body: any): Promise<any> {
  switch (functionName) {
    case 'analyze-email-security':
    case 'comprehensive-email-analysis':
      return runOfflineEmailAnalysis(body.emailContent || '');
    case 'analyze-email-header':
      return analyzeHeaders(parseEmail(body.headers || '')).result;
    case 'analyze-phishing-probability': {
      const parsed = parseEmail([`From: ${body.email || ''}`, `Subject: ${body.subject || ''}`, '', body.body || ''].join('\n'));
      return analyzePhishing(parsed, analyzeLinks(parsed).result.overallThreatScore).result;
    }
    case 'check-domain':
    case 'domain-analysis-comprehensive':
      return localDomainAnalysis(body.domain || '');
    case 'check-email-legitimacy':
      return localEmailLegitimacy(body.email || '');
    case 'detect-temp-email': {
      const validation = localEmailLegitimacy(body.email || '');
      const domain = validation.email.split('@')[1] || '';
      return { ...validation, domain, isTemporary: DISPOSABLE_DOMAINS.has(domain), isFreemail: ['gmail.com', 'outlook.com', 'yahoo.com'].includes(domain), confidence: DISPOSABLE_DOMAINS.has(domain) ? 98 : 80 };
    }
    case 'get-domain-age':
      return { domain: body.domain || '', ageInDays: null, ageDescription: 'Live lookup not run', threatScore: 0, riskLevel: 'safe', riskReason: 'Deploy the Supabase edge function for RDAP/WHOIS age data.' };
    case 'check-ip-reputation':
    case 'ip-analysis-comprehensive':
      return localIpAnalysis(body.ip || '');
    case 'scan-blacklist': {
      const target = body.ip || body.domain || (body.email || '').split('@')[1] || '';
      const isIp = /^(\d{1,3}\.){3}\d{1,3}$/.test(target);
      const result: any = isIp ? localIpAnalysis(target) : localDomainAnalysis(target);
      return { ip: target, overallThreatScore: result.threatScore || result.overallThreatScore || 0, riskLevel: result.riskLevel, blacklisted: false, basicChecks: isIp ? { ...result, ip: target } : {}, abuseIPDB: { available: false, message: 'Live blacklist lookup not run in offline preview.' }, recommendation: 'Deploy Supabase and configure AbuseIPDB for live blacklist data.' };
    }
    case 'check-link-reputation':
      return localLinkAnalysis(body.url || '');
    case 'analyze-email-links':
      return analyzeLinks(parseEmail(`From: preview@example.com\n\n${body.emailContent || ''}`)).result;
    case 'database-email-validation': {
      const validation = localEmailLegitimacy(body.email || '');
      return { email: validation.email, is_valid: validation.syntaxValid, confidence_score: validation.syntaxValid ? 0.7 : 0.95, validation_details: { syntax_valid: validation.syntaxValid, domain_valid: Boolean(validation.email.split('@')[1]), mx_record_valid: null, disposable: validation.disposable }, threats: validation.disposable ? [{ type: 'disposable_email', description: 'Disposable email detected', source: 'Offline rules' }] : [], recommendations: [validation.recommendation] };
    }
    case 'database-threat-intelligence':
      return { indicator: body.value || '', indicator_type: body.query_type || 'domain', confidence_score: 0.5, summary: { total_threats: 0, high_severity: 0, medium_severity: 0 }, threats: [], related_indicators: [], message: 'Live threat feed lookup not run in offline preview.' };
    case 'database-comprehensive-analysis':
      return localBulkAnalysis(body);
    case 'get-api-usage':
      return localApiUsage();
    case 'scan-attachment-hash':
      return {
        status: 'not-configured',
        message: 'Offline preview: hash-only provider lookup is disabled. Configure VirusTotal in Supabase for live reputation.',
        hash: body.hash,
        filename: body.filename,
      };
    case 'track-user-analytics':
      return { success: true, message: 'Stored locally in preview mode.' };
    default:
      throw new Error(`Offline preview does not implement ${functionName}`);
  }
}

export async function invokeEdgeFunction(functionName: string, body: any = {}) {
  if (!isSupabaseConfigured) {
    return { data: { data: await localInvoke(functionName, body) }, error: null, source: 'offline' as const };
  }

  const response = await supabase.functions.invoke(functionName, { body });
  if (!response.error || !ALLOW_OFFLINE_FALLBACK) return { ...response, source: 'supabase' as const };

  console.warn(`${functionName} failed; using offline safety rules for preview:`, response.error);
  return { data: { data: await localInvoke(functionName, body) }, error: null, source: 'offline' as const };
}

export async function runEmailSecurityAnalysis(emailContent: string): Promise<SecurityAnalysisResult> {
  if (!emailContent.trim()) throw new Error('Paste an email before running analysis.');
  const response = await invokeEdgeFunction('analyze-email-security', { emailContent: emailContent.slice(0, 1_000_000) });
  const payload = response.data?.data || response.data;
  if (!payload) throw new Error('The analysis service returned an empty response.');
  const localResult = await runOfflineEmailAnalysis(emailContent);
  const result = { ...localResult, ...payload, source: response.source } as SecurityAnalysisResult;
  result.source = response.source;
  result.sync = result.sync || { status: response.source === 'supabase' ? 'degraded' : 'offline', message: response.source === 'supabase' ? 'Analysis completed; sync will be attempted after the result is reviewed.' : 'Offline preview: result is stored in this browser only.', timestamp: new Date().toISOString() };
  return result;
}

function readHistory(): StoredScan[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(window.localStorage.getItem(HISTORY_KEY) || '[]');
  } catch {
    return [];
  }
}

function writeHistory(history: StoredScan[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 50)));
}

export function getLocalScanHistory(): StoredScan[] {
  return readHistory();
}

export async function persistScan(result: SecurityAnalysisResult): Promise<SyncInfo> {
  const localEntry: StoredScan = {
    id: result.scanId,
    createdAt: result.generatedAt,
    verdict: result.comprehensiveVerdict.overallVerdict,
    riskLevel: result.comprehensiveVerdict.riskLevel,
    score: result.comprehensiveVerdict.overallScore,
    senderDomain: result.parsedEmail.senderDomain,
    subject: result.parsedEmail.subject,
    source: result.source,
    findingCount: result.findings.length,
    result,
  };
  writeHistory([localEntry, ...readHistory().filter((entry) => entry.id !== localEntry.id)]);

  // The v8 edge function persists an authenticated live scan atomically. Do
  // not insert a duplicate row from the browser when it already returned a
  // successful ledger sync.
  if (result.source === 'supabase' && result.sync?.status === 'synced') {
    return result.sync;
  }

  const localOnly: SyncInfo = {
    status: isSupabaseConfigured ? 'local-only' : 'offline',
    message: isSupabaseConfigured ? 'Sign in to sync this scan to Supabase.' : 'Offline preview: scan saved to browser history.',
    timestamp: new Date().toISOString(),
  };
  if (!isSupabaseConfigured) return localOnly;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return localOnly;
    const row = {
      user_id: user.id,
      content_hash: result.contentHash,
      input_type: 'email',
      sender_domain: result.parsedEmail.senderDomain || null,
      overall_score: result.comprehensiveVerdict.overallScore,
      risk_level: result.comprehensiveVerdict.riskLevel,
      verdict: result.comprehensiveVerdict.overallVerdict,
      confidence: result.comprehensiveVerdict.confidenceScore,
      finding_count: result.findings.length,
      engines: result.engineStatus,
      result_json: result,
    };
    const { data, error } = await supabase.from('security_scans').insert(row).select('id').single();
    if (error) throw error;
    let incidentId: string | undefined;
    if (['high', 'critical'].includes(result.comprehensiveVerdict.riskLevel)) {
      const incident = await supabase.from('security_incidents').insert({
        user_id: user.id,
        scan_id: data.id,
        severity: result.comprehensiveVerdict.riskLevel,
        title: `${result.comprehensiveVerdict.overallVerdict}: ${result.parsedEmail.subject || 'Email security finding'}`,
        status: 'open',
        evidence_json: { findings: result.findings.slice(0, 20), content_hash: result.contentHash },
      }).select('id').single();
      if (incident.error) throw incident.error;
      incidentId = incident.data?.id;
    }
    const sync: SyncInfo = { status: 'synced', message: 'Scan and incident ledger synchronized to Supabase.', recordId: data.id, incidentId, timestamp: new Date().toISOString() };
    result.sync = sync;
    return sync;
  } catch (error: any) {
    console.warn('Supabase scan sync failed; local copy retained:', error);
    return { status: 'degraded', message: `Local copy saved; Supabase sync failed: ${error.message || 'unknown error'}`, timestamp: new Date().toISOString() };
  }
}

export async function getSyncSnapshot(): Promise<SyncSnapshot> {
  const localScans = readHistory();
  const empty: SyncSnapshot = {
    mode: 'offline', configured: isSupabaseConfigured, authenticated: false, lastSync: null,
    scans: [], incidents: [], watchlist: readLocalWatchlist(), apiUsage: [], localScans, errors: [],
  };
  if (!isSupabaseConfigured) return empty;
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return { ...empty, mode: 'not-authenticated' };
    const [scans, incidents, watchlist, apiUsage] = await Promise.all([
      supabase.from('security_scans').select('id, overall_score, risk_level, verdict, sender_domain, created_at, finding_count').order('created_at', { ascending: false }).limit(50),
      supabase.from('security_incidents').select('id, severity, status, title, created_at').order('created_at', { ascending: false }).limit(50),
      supabase.from('security_watchlist').select('id, indicator_type, indicator_value, label, severity, is_active, created_at').eq('is_active', true).order('created_at', { ascending: false }).limit(100),
      supabase.from('api_usage_tracking').select('api_name, reset_period, limit_total, request_count, date').order('date', { ascending: false }).limit(100),
    ]);
    const queries = [scans, incidents, watchlist, apiUsage];
    const errors = queries.filter((query) => query.error).map((query) => query.error?.message || 'Supabase query failed');
    const syncedAt = new Date().toISOString();
    return {
      mode: errors.length ? 'degraded' : 'synced', configured: true, authenticated: true, lastSync: syncedAt,
      scans: scans.data || [], incidents: incidents.data || [], watchlist: watchlist.data || [], apiUsage: apiUsage.data || [], localScans, errors,
    };
  } catch (error: any) {
    return { ...empty, mode: 'degraded', authenticated: true, errors: [error.message || 'Supabase sync failed'] };
  }
}

function readLocalWatchlist(): any[] {
  if (typeof window === 'undefined') return [];
  try { return JSON.parse(window.localStorage.getItem(WATCHLIST_KEY) || '[]'); } catch { return []; }
}

export async function addWatchlistIndicator(indicator: { indicator_type: string; indicator_value: string; label: string; severity: string; notes?: string }) {
  if (isSupabaseConfigured) {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const { data, error } = await supabase.from('security_watchlist').insert({ ...indicator, user_id: user.id }).select().single();
      if (!error) return data;
    }
  }
  const item = { ...indicator, id: makeId('watch'), is_active: true, created_at: new Date().toISOString() };
  if (typeof window !== 'undefined') window.localStorage.setItem(WATCHLIST_KEY, JSON.stringify([item, ...readLocalWatchlist()].slice(0, 100)));
  return item;
}

export function downloadJson(filename: string, payload: unknown) {
  if (typeof window === 'undefined') return;
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function severityClass(severity: string): string {
  if (severity === 'critical' || severity === 'high') return 'text-red-400 border-red-400/30 bg-red-400/10';
  if (severity === 'medium') return 'text-amber-300 border-amber-300/30 bg-amber-300/10';
  if (severity === 'low') return 'text-blue-300 border-blue-300/30 bg-blue-300/10';
  return 'text-emerald-300 border-emerald-300/30 bg-emerald-300/10';
}
