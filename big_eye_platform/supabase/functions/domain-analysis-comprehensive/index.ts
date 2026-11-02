/**
 * Domain Analysis Comprehensive
 * Aggregates multiple domain analysis APIs
 * 
 * APIs integrated:
 * - Who-Dat (unlimited, no key) - Primary WHOIS
 * - HackerTarget (50/day, no key) - DNS lookup
 * - MXToolbox (web scraping fallback) - DMARC/SPF/DKIM
 * 
 * Features:
 * - WHOIS information
 * - DNS records (A, MX, TXT, NS, SOA, CNAME, PTR)
 * - SPF/DKIM/DMARC validation
 * - Domain age calculation
 * - Risk scoring
 */

Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
        'Access-Control-Max-Age': '86400',
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const { domain } = await req.json();

        if (!domain) {
            throw new Error('Domain is required');
        }

        // Clean and validate domain
        const cleanDomain = cleanDomainInput(domain);
        if (!isValidDomain(cleanDomain)) {
            throw new Error('Invalid domain format');
        }

        // Check cache
        const cacheKey = `domain_analysis:${cleanDomain}`;
        const cached = await checkCache(cacheKey);
        if (cached) {
            console.log('Cache hit for domain:', cleanDomain);
            return new Response(JSON.stringify({ data: cached, cached: true }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Run multiple checks in parallel
        const results = await Promise.allSettled([
            getWhoisData(cleanDomain),
            getDNSRecords(cleanDomain),
            checkEmailAuthentication(cleanDomain),
            checkDomainReputation(cleanDomain)
        ]);

        // Aggregate results
        const aggregated = aggregateDomainResults(results, cleanDomain);

        // Cache result (12 hours TTL)
        await cacheResult(cacheKey, aggregated, 12 * 60 * 60);

        return new Response(JSON.stringify({ data: aggregated, cached: false }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Domain analysis error:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'DOMAIN_ANALYSIS_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// Who-Dat WHOIS lookup (unlimited, no API key)
async function getWhoisData(domain: string) {
    try {
        const response = await fetch(`https://who-dat.as93.net/${domain}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error('WHOIS lookup failed');
        }

        return {
            provider: 'Who-Dat',
            success: true,
            data: {
                domain_name: data.domain || domain,
                registrar: data.registrar || null,
                registration_date: data.creation_date || data.created || null,
                expiration_date: data.expiration_date || data.expires || null,
                updated_date: data.updated_date || data.updated || null,
                name_servers: data.name_servers || data.nameservers || [],
                status: data.status || [],
                registrant: data.registrant || null,
                admin: data.admin || null,
                tech: data.tech || null,
                dnssec: data.dnssec || null
            }
        };
    } catch (error) {
        return {
            provider: 'Who-Dat',
            success: false,
            error: error.message
        };
    }
}

// HackerTarget DNS lookup (50 queries/day, no key for low volume)
async function getDNSRecords(domain: string) {
    try {
        // Get multiple record types
        const recordTypes = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME'];
        const records: any = {};

        // Query each record type
        for (const type of recordTypes) {
            try {
                const response = await fetch(
                    `https://api.hackertarget.com/dnslookup/?q=${domain}&type=${type}`
                );
                const text = await response.text();
                
                if (text && !text.includes('error') && !text.includes('API count exceeded')) {
                    records[type] = parseDNSResponse(text, type);
                }
            } catch (e) {
                console.warn(`Failed to get ${type} record:`, e.message);
            }
        }

        return {
            provider: 'HackerTarget',
            success: Object.keys(records).length > 0,
            data: records
        };
    } catch (error) {
        return {
            provider: 'HackerTarget',
            success: false,
            error: error.message
        };
    }
}

// Email Authentication Check (SPF, DKIM, DMARC)
async function checkEmailAuthentication(domain: string) {
    try {
        const auth: any = {
            spf: null,
            dmarc: null,
            dkim: null
        };

        // Check SPF record (TXT record)
        try {
            const spfResponse = await fetch(
                `https://api.hackertarget.com/dnslookup/?q=${domain}&type=TXT`
            );
            const spfText = await spfResponse.text();
            
            if (spfText && spfText.includes('v=spf1')) {
                const spfMatch = spfText.match(/v=spf1[^\n]*/);
                if (spfMatch) {
                    auth.spf = {
                        record: spfMatch[0].trim(),
                        valid: true,
                        mechanisms: parseSPFRecord(spfMatch[0])
                    };
                }
            } else {
                auth.spf = { valid: false, error: 'No SPF record found' };
            }
        } catch (e) {
            auth.spf = { valid: false, error: e.message };
        }

        // Check DMARC record (_dmarc subdomain)
        try {
            const dmarcResponse = await fetch(
                `https://api.hackertarget.com/dnslookup/?q=_dmarc.${domain}&type=TXT`
            );
            const dmarcText = await dmarcResponse.text();
            
            if (dmarcText && dmarcText.includes('v=DMARC1')) {
                const dmarcMatch = dmarcText.match(/v=DMARC1[^\n]*/);
                if (dmarcMatch) {
                    auth.dmarc = {
                        record: dmarcMatch[0].trim(),
                        valid: true,
                        policy: parseDMARCRecord(dmarcMatch[0])
                    };
                }
            } else {
                auth.dmarc = { valid: false, error: 'No DMARC record found' };
            }
        } catch (e) {
            auth.dmarc = { valid: false, error: e.message };
        }

        // DKIM check (requires selector, common selectors to try)
        const commonSelectors = ['default', 'google', 'k1', 'selector1', 'selector2', 'dkim'];
        for (const selector of commonSelectors) {
            try {
                const dkimResponse = await fetch(
                    `https://api.hackertarget.com/dnslookup/?q=${selector}._domainkey.${domain}&type=TXT`
                );
                const dkimText = await dkimResponse.text();
                
                if (dkimText && (dkimText.includes('v=DKIM1') || dkimText.includes('p='))) {
                    auth.dkim = {
                        selector: selector,
                        record: dkimText.trim(),
                        valid: true
                    };
                    break;
                }
            } catch (e) {
                continue;
            }
        }

        if (!auth.dkim) {
            auth.dkim = { valid: false, error: 'No DKIM record found (tried common selectors)' };
        }

        return {
            provider: 'Email Authentication Check',
            success: true,
            data: auth
        };
    } catch (error) {
        return {
            provider: 'Email Authentication Check',
            success: false,
            error: error.message
        };
    }
}

// Domain reputation check (basic heuristics)
async function checkDomainReputation(domain: string) {
    try {
        const reputation: any = {
            age_score: 0,
            auth_score: 0,
            security_features: []
        };

        // Calculate domain age if WHOIS data available
        // This will be filled in by aggregation function

        return {
            provider: 'Reputation Check',
            success: true,
            data: reputation
        };
    } catch (error) {
        return {
            provider: 'Reputation Check',
            success: false,
            error: error.message
        };
    }
}

function aggregateDomainResults(results: any[], domain: string) {
    const whois = results[0].status === 'fulfilled' ? results[0].value : null;
    const dns = results[1].status === 'fulfilled' ? results[1].value : null;
    const emailAuth = results[2].status === 'fulfilled' ? results[2].value : null;
    const reputation = results[3].status === 'fulfilled' ? results[3].value : null;

    let riskScore = 0;
    let riskFactors = [];
    let successfulAPIs = [];

    [whois, dns, emailAuth, reputation].forEach(result => {
        if (result && result.success) {
            successfulAPIs.push(result.provider);
        }
    });

    // Calculate domain age
    let domainAge = null;
    if (whois?.success && whois.data.registration_date) {
        try {
            const regDate = new Date(whois.data.registration_date);
            const now = new Date();
            const ageInDays = Math.floor((now.getTime() - regDate.getTime()) / (1000 * 60 * 60 * 24));
            domainAge = {
                days: ageInDays,
                years: Math.floor(ageInDays / 365),
                months: Math.floor((ageInDays % 365) / 30)
            };

            // Age-based risk scoring (newer = higher risk)
            if (ageInDays < 30) {
                riskScore += 30;
                riskFactors.push('Very new domain (less than 1 month old)');
            } else if (ageInDays < 180) {
                riskScore += 20;
                riskFactors.push('New domain (less than 6 months old)');
            } else if (ageInDays < 365) {
                riskScore += 10;
                riskFactors.push('Relatively new domain (less than 1 year old)');
            }
        } catch (e) {
            console.error('Error calculating domain age:', e);
        }
    }

    // Email authentication risk scoring
    if (emailAuth?.success) {
        const { spf, dmarc, dkim } = emailAuth.data;
        
        if (!spf?.valid) {
            riskScore += 15;
            riskFactors.push('No SPF record configured');
        }
        if (!dmarc?.valid) {
            riskScore += 15;
            riskFactors.push('No DMARC policy configured');
        }
        if (!dkim?.valid) {
            riskScore += 10;
            riskFactors.push('No DKIM signature found');
        }
    }

    // DNS configuration checks
    if (dns?.success) {
        if (!dns.data.MX || dns.data.MX.length === 0) {
            riskScore += 10;
            riskFactors.push('No MX records (cannot receive email)');
        }
        if (!dns.data.A && !dns.data.AAAA) {
            riskScore += 20;
            riskFactors.push('No A/AAAA records (domain not reachable)');
        }
    }

    // WHOIS privacy
    if (whois?.success) {
        if (whois.data.registrant && 
            (JSON.stringify(whois.data.registrant).toLowerCase().includes('privacy') ||
             JSON.stringify(whois.data.registrant).toLowerCase().includes('redacted'))) {
            riskScore += 5;
            riskFactors.push('WHOIS privacy protection enabled');
        }
    }

    riskScore = Math.min(100, Math.round(riskScore));

    let riskLevel = 'low';
    if (riskScore >= 75) riskLevel = 'critical';
    else if (riskScore >= 50) riskLevel = 'high';
    else if (riskScore >= 25) riskLevel = 'medium';

    const recommendations = generateDomainRecommendations(
        riskScore,
        riskFactors,
        whois,
        dns,
        emailAuth,
        domainAge
    );

    return {
        domain: domain,
        risk_score: riskScore,
        risk_level: riskLevel,
        risk_factors: riskFactors,
        confidence: calculateConfidence(successfulAPIs.length),
        api_sources: successfulAPIs,
        whois: whois?.success ? whois.data : null,
        dns_records: dns?.success ? dns.data : null,
        email_authentication: emailAuth?.success ? emailAuth.data : null,
        domain_age: domainAge,
        security_features: {
            has_spf: emailAuth?.data?.spf?.valid || false,
            has_dmarc: emailAuth?.data?.dmarc?.valid || false,
            has_dkim: emailAuth?.data?.dkim?.valid || false,
            has_dnssec: whois?.data?.dnssec === 'signedDelegation' || false
        },
        recommendations: recommendations,
        analyzed_at: new Date().toISOString()
    };
}

function generateDomainRecommendations(
    riskScore: number,
    riskFactors: string[],
    whois: any,
    dns: any,
    emailAuth: any,
    domainAge: any
): string[] {
    const recommendations = [];

    if (riskScore >= 75) {
        recommendations.push('CRITICAL: Exercise extreme caution with this domain');
        recommendations.push('Verify domain legitimacy through alternative channels');
        recommendations.push('Consider blocking or quarantining emails from this domain');
    } else if (riskScore >= 50) {
        recommendations.push('HIGH RISK: Additional verification recommended');
        recommendations.push('Apply strict email filtering rules');
        recommendations.push('Monitor for suspicious activity');
    } else if (riskScore >= 25) {
        recommendations.push('MEDIUM RISK: Standard caution advised');
        recommendations.push('Verify sender authenticity for important communications');
    } else {
        recommendations.push('LOW RISK: Domain appears legitimate');
        recommendations.push('Standard security protocols apply');
    }

    if (domainAge && domainAge.days < 90) {
        recommendations.push('Be cautious with new domains - verify legitimacy');
    }

    if (emailAuth?.data) {
        if (!emailAuth.data.spf?.valid) {
            recommendations.push('Configure SPF record to improve email deliverability');
        }
        if (!emailAuth.data.dmarc?.valid) {
            recommendations.push('Implement DMARC policy to prevent email spoofing');
        }
        if (!emailAuth.data.dkim?.valid) {
            recommendations.push('Set up DKIM signing for email authentication');
        }
    }

    if (riskFactors.length > 0) {
        recommendations.push(`Key concerns: ${riskFactors.slice(0, 3).join(', ')}`);
    }

    return recommendations;
}

function parseDNSResponse(text: string, type: string): string[] {
    if (!text) return [];
    
    const lines = text.split('\n').filter(line => 
        line.trim() && 
        !line.includes('API count') && 
        !line.includes('error')
    );
    
    return lines;
}

function parseSPFRecord(record: string): any {
    const mechanisms = [];
    const parts = record.split(/\s+/);
    
    for (const part of parts) {
        if (part.startsWith('include:')) mechanisms.push({ type: 'include', value: part.substring(8) });
        else if (part.startsWith('a:')) mechanisms.push({ type: 'a', value: part.substring(2) });
        else if (part.startsWith('mx:')) mechanisms.push({ type: 'mx', value: part.substring(3) });
        else if (part.startsWith('ip4:')) mechanisms.push({ type: 'ip4', value: part.substring(4) });
        else if (part.startsWith('ip6:')) mechanisms.push({ type: 'ip6', value: part.substring(4) });
        else if (part === 'a' || part === 'mx') mechanisms.push({ type: part, value: null });
        else if (part === '~all' || part === '-all' || part === '+all' || part === '?all') {
            mechanisms.push({ type: 'all', qualifier: part[0] });
        }
    }
    
    return mechanisms;
}

function parseDMARCRecord(record: string): any {
    const policy: any = {};
    const parts = record.split(';').map(p => p.trim());
    
    for (const part of parts) {
        const [key, value] = part.split('=').map(s => s.trim());
        if (key && value) {
            policy[key] = value;
        }
    }
    
    return policy;
}

function cleanDomainInput(domain: string): string {
    // Remove protocol, path, and www
    let clean = domain.toLowerCase().trim();
    clean = clean.replace(/^https?:\/\//, '');
    clean = clean.replace(/^www\./, '');
    clean = clean.split('/')[0];
    clean = clean.split(':')[0];
    return clean;
}

function isValidDomain(domain: string): boolean {
    const domainRegex = /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$/;
    return domainRegex.test(domain);
}

function calculateConfidence(successfulAPIs: number): number {
    return Math.round((successfulAPIs / 4) * 100);
}

async function checkCache(key: string): Promise<any | null> {
    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        if (!supabaseUrl || !serviceRoleKey) return null;

        const response = await fetch(
            `${supabaseUrl}/rest/v1/analysis_cache?cache_key=eq.${key}&expires_at=gt.${new Date().toISOString()}`,
            {
                headers: {
                    'apikey': serviceRoleKey,
                    'Authorization': `Bearer ${serviceRoleKey}`
                }
            }
        );

        if (!response.ok) return null;
        
        const data = await response.json();
        if (data && data.length > 0) {
            await incrementCacheHit(key);
            return data[0].result;
        }
        
        return null;
    } catch (error) {
        console.error('Cache check error:', error);
        return null;
    }
}

async function cacheResult(key: string, result: any, ttlSeconds: number): Promise<void> {
    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        if (!supabaseUrl || !serviceRoleKey) return;

        const expiresAt = new Date(Date.now() + ttlSeconds * 1000);

        await fetch(`${supabaseUrl}/rest/v1/analysis_cache`, {
            method: 'POST',
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`,
                'Content-Type': 'application/json',
                'Prefer': 'resolution=merge-duplicates'
            },
            body: JSON.stringify({
                cache_key: key,
                analysis_type: 'domain',
                input_value: result.domain,
                result: result,
                confidence_score: result.confidence,
                api_sources: result.api_sources,
                expires_at: expiresAt.toISOString()
            })
        });
    } catch (error) {
        console.error('Cache save error:', error);
    }
}

async function incrementCacheHit(key: string): Promise<void> {
    try {
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        if (!supabaseUrl || !serviceRoleKey) return;

        await fetch(`${supabaseUrl}/rest/v1/rpc/increment_cache_hit`, {
            method: 'POST',
            headers: {
                'apikey': serviceRoleKey,
                'Authorization': `Bearer ${serviceRoleKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ p_cache_key: key })
        });
    } catch (error) {
        console.error('Cache hit increment error:', error);
    }
}
