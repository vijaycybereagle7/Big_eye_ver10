const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

const disposableDomains = new Set([
  '10minutemail.com', 'guerrillamail.com', 'mailinator.com', 'temp-mail.org',
  'tempmail.com', 'throwaway.email', 'trashmail.com', 'yopmail.com', 'mail.tm',
]);
const shorteners = new Set(['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'rb.gy']);
const riskyExtensions = new Set([
  'exe', 'scr', 'js', 'jse', 'vbs', 'vbe', 'wsf', 'ps1', 'bat', 'cmd', 'hta',
  'dll', 'msi', 'lnk', 'iso', 'img', 'jar', 'apk', 'docm', 'xlsm', 'pptm', 'zip', 'rar', '7z',
]);
const brandDomains: Record<string, string[]> = {
  paypal: ['paypal.com'], microsoft: ['microsoft.com', 'live.com', 'office.com'],
  google: ['google.com', 'gmail.com'], amazon: ['amazon.com'], apple: ['apple.com', 'icloud.com'],
  netflix: ['netflix.com'], dhl: ['dhl.com'], fedex: ['fedex.com'],
};

type Finding = {
  id: string;
  category: string;
  severity: string;
  title: string;
  evidence: string;
  recommendation: string;
};

function id(prefix: string) {
  return `${prefix}_${crypto.randomUUID()}`;
}

function clamp(value: number) {
  return Math.min(100, Math.max(0, Math.round(value)));
}

function risk(score: number) {
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 35) return 'medium';
  if (score >= 15) return 'low';
  return 'safe';
}

function verdict(level: string) {
  if (level === 'critical') return 'BLOCK';
  if (level === 'high') return 'QUARANTINE';
  if (level === 'medium') return 'REVIEW';
  return 'ALLOW';
}

function finding(category: string, severity: string, title: string, evidence: string, recommendation: string): Finding {
  return { id: id('finding'), category, severity, title, evidence, recommendation };
}

function parseHeaders(raw: string) {
  const map = new Map<string, string>();
  let current = '';
  let value = '';
  for (const line of raw.replace(/\r\n/g, '\n').split('\n')) {
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

function mailbox(value: string) {
  const angle = value.match(/<([^>]+)>/);
  const email = (angle?.[1] || value.match(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/i)?.[0] || '').toLowerCase();
  return { email, name: angle ? value.replace(angle[0], '').replace(/["']/g, '').trim() : '' };
}

function domain(value: string) {
  return (value.match(/@([^\s>]+)/)?.[1] || '').replace(/[>;,]/g, '').toLowerCase();
}

function authStatus(headers: Map<string, string>, type: string) {
  const auth = headers.get('authentication-results') || '';
  const receivedSpf = headers.get('received-spf') || '';
  if (type === 'spf' && receivedSpf) {
    const result = receivedSpf.match(/^(pass|fail|softfail|neutral|none|temperror|permerror)/i);
    if (result) return result[1].toLowerCase();
  }
  return auth.match(new RegExp(`${type}=([^\\s;]+)`, 'i'))?.[1]?.toLowerCase() || 'none';
}

function parseMessage(rawInput: string) {
  const raw = rawInput.replace(/\r\n/g, '\n');
  const separator = raw.search(/\n\s*\n/);
  const headerText = separator >= 0 ? raw.slice(0, separator) : raw;
  const body = separator >= 0 ? raw.slice(separator).replace(/^\s+/, '') : '';
  const headers = parseHeaders(headerText);
  const from = mailbox(headers.get('from') || '');
  const links = Array.from(body.matchAll(/https?:\/\/[^\s<>"']+/gi)).map((match) => match[0].replace(/[),.;:'"\]}]+$/g, ''));
  const attachments = Array.from(raw.matchAll(/(?:filename|name)\s*=\s*["']?([^"';\s]+)["']?/gi)).map((match) => match[1]).filter((name, index, all) => all.indexOf(name) === index);
  return {
    raw, headerText, body, headers, from,
    senderDomain: from.email.split('@')[1] || '',
    subject: headers.get('subject') || '',
    returnPath: headers.get('return-path') || '',
    replyTo: headers.get('reply-to') || '',
    links, attachments,
  };
}

async function analyze(rawInput: string, source: 'supabase' | 'offline' = 'supabase') {
  const parsed = parseMessage(rawInput);
  const findings: Finding[] = [];
  const authAnomalies: string[] = [];
  let headerScore = 0;
  const spf = authStatus(parsed.headers, 'spf');
  const dkim = authStatus(parsed.headers, 'dkim');
  const dmarc = authStatus(parsed.headers, 'dmarc');
  for (const [name, status] of [['SPF', spf], ['DKIM', dkim], ['DMARC', dmarc]]) {
    if (status === 'fail' || status === 'permerror') {
      headerScore += name === 'DMARC' ? 30 : 25;
      authAnomalies.push(`${name} authentication failed (${status})`);
    } else if (status === 'none' || status === 'softfail' || status === 'neutral') {
      headerScore += name === 'DMARC' ? 15 : 10;
      if (status === 'none') authAnomalies.push(`${name} result is missing`);
    }
  }
  const fromDomain = domain(parsed.headers.get('from') || '');
  const returnDomain = domain(parsed.returnPath);
  const replyDomain = domain(parsed.replyTo);
  if (fromDomain && returnDomain && fromDomain !== returnDomain) {
    headerScore += 20;
    authAnomalies.push(`From domain ${fromDomain} differs from Return-Path ${returnDomain}`);
    findings.push(finding('authentication', 'high', 'Envelope sender mismatch', authAnomalies.at(-1)!, 'Verify the sender through a trusted channel.'));
  }
  if (fromDomain && replyDomain && fromDomain !== replyDomain) {
    headerScore += 20;
    authAnomalies.push(`From domain ${fromDomain} differs from Reply-To ${replyDomain}`);
    findings.push(finding('phishing', 'high', 'Reply-To impersonation risk', authAnomalies.at(-1)!, 'Do not reply until the destination is independently verified.'));
  }
  if (!parsed.headers.get('message-id')) { headerScore += 8; authAnomalies.push('Message-ID header is missing'); }
  if (!parsed.headers.get('date')) { headerScore += 5; authAnomalies.push('Date header is missing'); }
  if (!parsed.headers.get('received')) { headerScore += 8; authAnomalies.push('Received routing headers are missing'); }
  headerScore = clamp(headerScore);
  if (headerScore >= 25) findings.push(finding('authentication', headerScore >= 60 ? 'high' : 'medium', 'Email authentication posture needs review', authAnomalies.slice(0, 4).join('; '), 'Inspect SPF, DKIM, DMARC alignment and the originating relay.'));

  const linkResults = parsed.links.map((url) => {
    let score = 0;
    const indicators: string[] = [];
    const warnings: string[] = [];
    let parsedUrl: URL | null = null;
    try { parsedUrl = new URL(url); } catch { score += 50; indicators.push('unparseable URL'); }
    const host = parsedUrl?.hostname.toLowerCase() || '';
    const lower = url.toLowerCase();
    if (parsedUrl && parsedUrl.protocol !== 'https:') { score += 15; indicators.push('insecure protocol'); warnings.push('HTTP destination'); }
    if (shorteners.has(host)) { score += 30; indicators.push('URL shortener'); warnings.push('Destination is hidden'); }
    if (/^(\d{1,3}\.){3}\d{1,3}$/.test(host)) { score += 25; indicators.push('IP literal host'); }
    if (host.includes('xn--')) { score += 35; indicators.push('punycode/homograph'); }
    if (url.includes('@') || /%[0-9a-f]{2}/i.test(url) || url.length > 180) { score += 20; indicators.push('obfuscated URL'); }
    if (/(login|verify|confirm|password|billing|suspended|secure|account)/.test(lower)) { score += 15; indicators.push('credential-themed path'); }
    const brand = Object.keys(brandDomains).find((candidate) => lower.includes(candidate));
    if (brand && !brandDomains[brand].some((official) => host === official || host.endsWith(`.${official}`))) { score += 35; indicators.push(`${brand} brand impersonation`); warnings.push(`Mentions ${brand} but is not an official domain`); }
    return { url, domain: host || 'unparseable', protocol: parsedUrl?.protocol || 'unknown', threatScore: clamp(score), threatLevel: risk(clamp(score)), warnings, suspiciousIndicators: indicators };
  });
  const linkScore = linkResults.length ? clamp(linkResults.reduce((sum, item) => sum + item.threatScore, 0) / linkResults.length) : 0;
  for (const link of linkResults.filter((item) => item.threatScore >= 35).slice(0, 8)) findings.push(finding('link', link.threatScore >= 60 ? 'high' : 'medium', 'Suspicious link detected', `${link.domain}: ${link.suspiciousIndicators.join(', ')}`, 'Open the trusted destination manually instead of following the message link.'));

  const subject = parsed.subject.toLowerCase();
  const body = parsed.body.toLowerCase();
  let phishingScore = 0;
  const redFlags: string[] = [];
  const urgency = ['urgent', 'immediate', 'action required', 'verify', 'confirm', 'suspended', 'locked', 'expired', 'act now', 'within 24 hours', 'final notice'];
  const credentials = ['verify your account', 'confirm your identity', 'reset your password', 'update your information', 'login to', 'enter your password'];
  const money = ['invoice', 'refund', 'payment', 'gift card', 'wire transfer', 'prize', 'reward', 'bank'];
  const urgencyHits = urgency.filter((word) => subject.includes(word) || body.includes(word));
  const credentialHits = credentials.filter((word) => body.includes(word));
  const moneyHits = money.filter((word) => subject.includes(word) || body.includes(word));
  if (urgencyHits.length) { phishingScore += Math.min(25, urgencyHits.length * 8); redFlags.push(`Urgency language: ${urgencyHits.slice(0, 3).join(', ')}`); }
  if (credentialHits.length) { phishingScore += Math.min(30, credentialHits.length * 12); redFlags.push(`Credential request: ${credentialHits.slice(0, 2).join(', ')}`); }
  if (moneyHits.length) { phishingScore += Math.min(18, moneyHits.length * 7); redFlags.push(`Financial theme: ${moneyHits.slice(0, 3).join(', ')}`); }
  const senderBrand = Object.keys(brandDomains).find((candidate) => parsed.from.name.toLowerCase().includes(candidate) || body.includes(candidate));
  if (senderBrand && parsed.senderDomain && !brandDomains[senderBrand].some((official) => parsed.senderDomain === official || parsed.senderDomain.endsWith(`.${official}`))) {
    phishingScore += 30;
    redFlags.push(`Possible ${senderBrand} impersonation from ${parsed.senderDomain}`);
    findings.push(finding('phishing', 'high', 'Sender may be impersonating a known brand', `${parsed.from.name || 'Sender'} mentions ${senderBrand}, but uses ${parsed.senderDomain}`, 'Verify the sender from the organization’s known website or phone number.'));
  }
  if (/<(form|input|script)\b/i.test(parsed.body)) { phishingScore += 25; redFlags.push('HTML form or active script found in body'); }
  phishingScore = clamp(phishingScore + Math.min(25, Math.round(linkScore / 3)));
  if (phishingScore >= 35) findings.push(finding('phishing', phishingScore >= 60 ? 'high' : 'medium', 'Phishing language or identity deception detected', redFlags.slice(0, 4).join('; '), phishingScore >= 60 ? 'Quarantine and report the message.' : 'Confirm the sender independently.'));

  let malwareScore = 0;
  const malwareFlags: string[] = [];
  for (const name of parsed.attachments) {
    const extension = name.split('.').pop()?.toLowerCase() || '';
    if (riskyExtensions.has(extension)) { malwareScore += ['exe', 'scr', 'js', 'jse', 'vbs', 'vbe', 'wsf', 'ps1', 'bat', 'cmd', 'hta', 'dll', 'msi', 'lnk'].includes(extension) ? 45 : 25; malwareFlags.push(`${name}: risky .${extension} attachment`); }
    if (/\.(pdf|docx?|xlsx?|jpg|png|txt)\.(exe|scr|js|vbs|cmd|bat|hta|zip)$/i.test(name)) { malwareScore += 35; malwareFlags.push(`${name}: double-extension disguise`); }
  }
  if (/enable (macros|content)|password.?protected|extract the archive/i.test(body)) { malwareScore += 20; malwareFlags.push('Message asks recipient to enable content or extract protected material'); }
  for (const link of linkResults) if (/\.(exe|scr|js|vbs|ps1|zip|rar|7z)(\?|$)/i.test(link.url)) { malwareScore += 35; malwareFlags.push(`Download link detected: ${link.domain}`); }
  malwareScore = clamp(malwareScore);
  if (malwareScore >= 25) findings.push(finding('malware', malwareScore >= 60 ? 'critical' : 'high', 'Potential malware delivery vector detected', malwareFlags.slice(0, 5).join('; '), 'Do not open the attachment; detonate only in an approved isolated sandbox.'));

  const platformScore = clamp(headerScore + (parsed.senderDomain ? 0 : 25));
  if (parsed.senderDomain && returnDomain && parsed.senderDomain !== returnDomain) findings.push(finding('platform', 'high', 'Mail platform alignment issue', `Header From uses ${parsed.senderDomain}; Return-Path uses ${returnDomain}`, 'Review DMARC alignment and relay authorization.'));
  const overallScore = clamp(phishingScore * 0.42 + malwareScore * 0.3 + headerScore * 0.2 + linkScore * 0.08);
  const riskLevel = risk(overallScore);
  const overallVerdict = verdict(riskLevel);
  const recommendation = overallVerdict === 'BLOCK' ? 'BLOCK - Do not interact with this message.' : overallVerdict === 'QUARANTINE' ? 'QUARANTINE - Escalate for security review.' : overallVerdict === 'REVIEW' ? 'REVIEW - Verify sender and requested action independently.' : 'ALLOW WITH CAUTION - Continue normal email safety practices.';
  const remediation = [
    ...(overallVerdict === 'BLOCK' || overallVerdict === 'QUARANTINE' ? ['Quarantine the message and preserve headers for incident response.'] : []),
    ...(malwareScore >= 25 ? ['Hash and detonate attachments only in an approved isolated malware workflow.'] : []),
    ...(headerScore >= 25 ? ['Review sender authentication and domain alignment in the mail platform.'] : []),
    ...(linkScore >= 30 ? ['Open destinations manually from a trusted bookmark, not from the message.'] : []),
    'Never treat a static score as proof of safety; confirm high-impact requests out of band.',
  ];
  const result: any = {
    scanId: id('scan'),
    contentHash: await hash(rawInput),
    generatedAt: new Date().toISOString(),
    source,
    parsedEmail: { senderEmail: parsed.from.email, senderDomain: parsed.senderDomain, senderName: parsed.from.name, subject: parsed.subject, linkCount: parsed.links.length, links: parsed.links, attachments: parsed.attachments.map((filename) => ({ filename })) },
    comprehensiveVerdict: {
      overallVerdict, riskLevel, confidenceScore: clamp(45 + (parsed.headerText ? 15 : 0) + (parsed.body ? 15 : 0) + (parsed.from.email ? 10 : 0) + (parsed.links.length ? 8 : 0)), overallScore,
      recommendation, summary: findings.length ? `${overallVerdict} recommendation: ${findings.length} finding(s) across phishing, malware, authentication, and link engines.` : 'No strong static threat indicators were found. Live reputation and DNS checks are still recommended.', toolsExecuted: 6, totalToolsAvailable: 6,
    },
    findings,
    engineStatus: [
      { id: 'phishing', label: 'Phishing & impersonation', score: phishingScore, status: phishingScore >= 60 ? 'alert' : phishingScore >= 25 ? 'attention' : 'clear', detail: `${redFlags.length} signal(s)` },
      { id: 'malware', label: 'Malware delivery triage', score: malwareScore, status: malwareScore >= 60 ? 'alert' : malwareScore >= 25 ? 'attention' : 'clear', detail: `${malwareFlags.length} indicator(s)` },
      { id: 'authentication', label: 'SPF / DKIM / DMARC', score: headerScore, status: headerScore >= 60 ? 'alert' : headerScore >= 25 ? 'attention' : 'clear', detail: `${authAnomalies.length} anomaly(ies)` },
      { id: 'links', label: 'Link reputation', score: linkScore, status: linkScore >= 60 ? 'alert' : linkScore >= 25 ? 'attention' : 'clear', detail: `${linkResults.length} link(s) inspected` },
      { id: 'platform', label: 'Mail platform posture', score: platformScore, status: platformScore >= 60 ? 'alert' : platformScore >= 25 ? 'attention' : 'clear', detail: parsed.senderDomain ? 'Header posture available' : 'Sender domain missing' },
      { id: 'reputation', label: 'External reputation feeds', score: 0, status: 'not-run', detail: 'Configure provider keys for enrichment' },
    ],
    individualAnalyses: {
      emailHeaderAnalysis: { from: parsed.headers.get('from') || '', to: parsed.headers.get('to') || '', subject: parsed.subject, returnPath: parsed.returnPath, replyTo: parsed.replyTo, spf: { status: spf }, dkim: { status: dkim }, dmarc: { status: dmarc }, anomalies: authAnomalies, threatScore: headerScore },
      phishingAnalysis: { phishingScore, confidence: clamp(45 + (parsed.from.email ? 15 : 0) + (parsed.subject ? 10 : 0) + (parsed.body ? 15 : 0)), riskLevel: risk(phishingScore), redFlags, reasoning: ['Composite static signals evaluated from identity, language, headers, and links.'], recommendation },
      malwareAnalysis: { threatScore: malwareScore, riskLevel: risk(malwareScore), status: malwareScore >= 60 ? 'quarantine' : malwareScore >= 25 ? 'review' : 'clear', attachments: parsed.attachments, suspiciousIndicators: malwareFlags, scanScope: 'Static metadata and content indicators only; no file execution.' },
      linkAnalysis: { linksFound: linkResults.length, linksAnalyzed: linkResults.length, overallThreatScore: linkScore, overallThreatLevel: risk(linkScore), links: linkResults },
      platformAnalysis: { domain: parsed.senderDomain, score: platformScore, checks: { spf: { status: spf }, dkim: { status: dkim }, dmarc: { status: dmarc }, mx: { status: parsed.senderDomain ? 'not-queried' : 'unavailable' }, tls: { status: 'not-observable-from-message' } }, recommendations: ['Confirm MX, SPF, DKIM, DMARC, and TLS posture with a live domain lookup.'] },
    },
    remediation,
  };
  return result;
}

async function hash(value: string) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

async function currentUserId(req: Request) {
  const token = req.headers.get('authorization');
  const url = Deno.env.get('SUPABASE_URL');
  const key = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SUPABASE_ANON_KEY');
  if (!token || !url || !key) return null;
  const response = await fetch(`${url}/auth/v1/user`, { headers: { Authorization: token, apikey: key } });
  if (!response.ok) return null;
  return (await response.json()).id || null;
}

async function syncResult(req: Request, result: any) {
  const url = Deno.env.get('SUPABASE_URL');
  const serviceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  const userId = await currentUserId(req);
  if (!url || !serviceKey || !userId) return { status: 'local-only', message: 'No authenticated service-role sync available.', timestamp: new Date().toISOString() };
  const scanResponse = await fetch(`${url}/rest/v1/security_scans`, {
    method: 'POST', headers: { Authorization: `Bearer ${serviceKey}`, apikey: serviceKey, 'Content-Type': 'application/json', Prefer: 'return=representation' },
    body: JSON.stringify([{ user_id: userId, content_hash: result.contentHash, input_type: 'email', sender_domain: result.parsedEmail.senderDomain || null, overall_score: result.comprehensiveVerdict.overallScore, risk_level: result.comprehensiveVerdict.riskLevel, verdict: result.comprehensiveVerdict.overallVerdict, confidence: result.comprehensiveVerdict.confidenceScore, finding_count: result.findings.length, engines: result.engineStatus, result_json: result }]),
  });
  if (!scanResponse.ok) throw new Error(`security_scans insert failed (${scanResponse.status})`);
  const scan = (await scanResponse.json())[0];
  let incidentId: string | undefined;
  if (['high', 'critical'].includes(result.comprehensiveVerdict.riskLevel)) {
    const incidentResponse = await fetch(`${url}/rest/v1/security_incidents`, {
      method: 'POST', headers: { Authorization: `Bearer ${serviceKey}`, apikey: serviceKey, 'Content-Type': 'application/json', Prefer: 'return=representation' },
      body: JSON.stringify([{ user_id: userId, scan_id: scan.id, severity: result.comprehensiveVerdict.riskLevel, title: `${result.comprehensiveVerdict.overallVerdict}: ${result.parsedEmail.subject || 'Email security finding'}`, status: 'open', evidence_json: { findings: result.findings.slice(0, 20), content_hash: result.contentHash } }]),
    });
    if (!incidentResponse.ok) throw new Error(`security_incidents insert failed (${incidentResponse.status})`);
    incidentId = (await incidentResponse.json())[0]?.id;
  }
  return { status: 'synced', message: 'Scan and incident ledger synchronized to Supabase.', recordId: scan.id, incidentId, timestamp: new Date().toISOString() };
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 200, headers: corsHeaders });
  try {
    const body = await req.json();
    if (typeof body.emailContent !== 'string' || !body.emailContent.trim()) throw new Error('emailContent is required');
    if (body.emailContent.length > 1_000_000) throw new Error('Email content exceeds the 1 MB safety limit');
    const result = await analyze(body.emailContent);
    try {
      result.sync = await syncResult(req, result);
    } catch (syncError: any) {
      result.sync = { status: 'degraded', message: `Analysis completed but sync failed: ${syncError.message || 'unknown error'}`, timestamp: new Date().toISOString() };
    }
    return new Response(JSON.stringify({ data: result }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
  } catch (error: any) {
    return new Response(JSON.stringify({ error: { code: 'EMAIL_SECURITY_ANALYSIS_FAILED', message: error.message || 'Analysis failed' } }), { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
  }
});
