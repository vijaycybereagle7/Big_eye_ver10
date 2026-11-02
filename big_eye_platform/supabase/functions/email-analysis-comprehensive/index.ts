/**
 * Email Analysis Comprehensive
 * Aggregates multiple email validation and reputation APIs
 * 
 * APIs integrated:
 * - EmailRep.io (rate limited, no key) - Email reputation
 * - Verify Email (unlimited, no key) - Disposable detection
 * - Syntax validation (built-in)
 * - MX record checking (DNS)
 * 
 * Features:
 * - Email syntax validation (RFC5322)
 * - MX record verification
 * - Disposable email detection
 * - Email reputation scoring
 * - Breach detection
 * - Social profile detection
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
        const { email } = await req.json();

        if (!email) {
            throw new Error('Email address is required');
        }

        const cleanEmail = email.toLowerCase().trim();
        if (!isValidEmailSyntax(cleanEmail)) {
            throw new Error('Invalid email format');
        }

        // Check cache
        const cacheKey = `email_analysis:${cleanEmail}`;
        const cached = await checkCache(cacheKey);
        if (cached) {
            console.log('Cache hit for email:', cleanEmail);
            return new Response(JSON.stringify({ data: cached, cached: true }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Run multiple checks in parallel
        const results = await Promise.allSettled([
            checkEmailReputation(cleanEmail),
            checkDisposableEmail(cleanEmail),
            verifyMXRecords(cleanEmail),
            checkEmailDeliverability(cleanEmail)
        ]);

        // Aggregate results
        const aggregated = aggregateEmailResults(results, cleanEmail);

        // Cache result (12 hours TTL)
        await cacheResult(cacheKey, aggregated, 12 * 60 * 60);

        return new Response(JSON.stringify({ data: aggregated, cached: false }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Email analysis error:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'EMAIL_ANALYSIS_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// EmailRep.io - Email reputation (no key for basic usage, rate limited)
async function checkEmailReputation(email: string) {
    try {
        const response = await fetch(`https://emailrep.io/${email}`);
        
        if (response.status === 429) {
            throw new Error('Rate limit exceeded');
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        return {
            provider: 'EmailRep.io',
            success: true,
            data: {
                reputation: data.reputation || 'none',
                suspicious: data.suspicious || false,
                references: data.references || 0,
                blacklisted: data.details?.blacklisted || false,
                malicious_activity: data.details?.malicious_activity || false,
                malicious_activity_recent: data.details?.malicious_activity_recent || false,
                credentials_leaked: data.details?.credentials_leaked || false,
                credentials_leaked_recent: data.details?.credentials_leaked_recent || false,
                data_breach: data.details?.data_breach || false,
                first_seen: data.details?.first_seen || null,
                last_seen: data.details?.last_seen || null,
                domain_exists: data.details?.domain_exists !== false,
                domain_reputation: data.details?.domain_reputation || 'none',
                new_domain: data.details?.new_domain || false,
                days_since_domain_creation: data.details?.days_since_domain_creation || null,
                suspicious_tld: data.details?.suspicious_tld || false,
                spam: data.details?.spam || false,
                free_provider: data.details?.free_provider || false,
                disposable: data.details?.disposable || false,
                deliverable: data.details?.deliverable !== false,
                accept_all: data.details?.accept_all || false,
                valid_mx: data.details?.valid_mx !== false,
                spoofable: data.details?.spoofable || false,
                spf_strict: data.details?.spf_strict || false,
                dmarc_enforced: data.details?.dmarc_enforced || false,
                profiles: data.details?.profiles || []
            }
        };
    } catch (error) {
        return {
            provider: 'EmailRep.io',
            success: false,
            error: error.message
        };
    }
}

// Verify Email API - Disposable email detection (unlimited, no key)
async function checkDisposableEmail(email: string) {
    try {
        const domain = email.split('@')[1];
        
        // Common disposable domains list (fallback)
        const disposableDomains = [
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'tempmail.com', 'throwaway.email', 'yopmail.com',
            'maildrop.cc', 'temp-mail.org', 'getnada.com'
        ];

        const isDisposable = disposableDomains.includes(domain.toLowerCase());

        // Try Verify Email API
        try {
            const response = await fetch(`https://verifyemail.vercel.app/verify/${email}`);
            const data = await response.json();
            
            if (data.disposable !== undefined) {
                return {
                    provider: 'Verify Email',
                    success: true,
                    data: {
                        is_disposable: data.disposable,
                        is_public_provider: data.public_provider || false
                    }
                };
            }
        } catch (e) {
            console.warn('Verify Email API failed, using fallback:', e.message);
        }

        // Fallback to local check
        return {
            provider: 'Local Disposable Check',
            success: true,
            data: {
                is_disposable: isDisposable,
                is_public_provider: false
            }
        };
    } catch (error) {
        return {
            provider: 'Disposable Check',
            success: false,
            error: error.message
        };
    }
}

// MX Record Verification
async function verifyMXRecords(email: string) {
    try {
        const domain = email.split('@')[1];
        
        // Use HackerTarget for MX lookup
        const response = await fetch(
            `https://api.hackertarget.com/mxlookup/?q=${domain}`
        );
        const text = await response.text();

        if (text && !text.includes('error') && !text.includes('API count exceeded')) {
            const mxRecords = text.split('\n')
                .filter(line => line.trim() && !line.includes('API'))
                .map(line => {
                    const parts = line.trim().split(/\s+/);
                    return {
                        priority: parseInt(parts[0]) || 0,
                        host: parts[1] || line.trim()
                    };
                });

            return {
                provider: 'MX Lookup',
                success: true,
                data: {
                    has_mx: mxRecords.length > 0,
                    mx_records: mxRecords,
                    count: mxRecords.length
                }
            };
        }

        throw new Error('MX lookup failed');
    } catch (error) {
        return {
            provider: 'MX Lookup',
            success: false,
            error: error.message
        };
    }
}

// Email deliverability check
async function checkEmailDeliverability(email: string) {
    try {
        const domain = email.split('@')[1];
        
        // Check if domain has A record (basic reachability)
        const response = await fetch(
            `https://api.hackertarget.com/dnslookup/?q=${domain}&type=A`
        );
        const text = await response.text();

        const hasARecord = text && 
                          !text.includes('error') && 
                          !text.includes('API count exceeded') &&
                          text.trim().length > 0;

        return {
            provider: 'Deliverability Check',
            success: true,
            data: {
                domain_reachable: hasARecord,
                can_receive_email: hasARecord // Simplified check
            }
        };
    } catch (error) {
        return {
            provider: 'Deliverability Check',
            success: false,
            error: error.message
        };
    }
}

function aggregateEmailResults(results: any[], email: string) {
    const reputation = results[0].status === 'fulfilled' ? results[0].value : null;
    const disposable = results[1].status === 'fulfilled' ? results[1].value : null;
    const mx = results[2].status === 'fulfilled' ? results[2].value : null;
    const deliverability = results[3].status === 'fulfilled' ? results[3].value : null;

    let riskScore = 0;
    let riskFactors = [];
    let successfulAPIs = [];

    [reputation, disposable, mx, deliverability].forEach(result => {
        if (result && result.success) {
            successfulAPIs.push(result.provider);
        }
    });

    // Extract domain
    const [localPart, domain] = email.split('@');

    // Check EmailRep.io reputation
    if (reputation?.success) {
        const rep = reputation.data;
        
        if (rep.suspicious) {
            riskScore += 40;
            riskFactors.push('Marked as suspicious by EmailRep.io');
        }
        
        if (rep.malicious_activity || rep.malicious_activity_recent) {
            riskScore += 35;
            riskFactors.push('Associated with malicious activity');
        }
        
        if (rep.credentials_leaked || rep.credentials_leaked_recent) {
            riskScore += 25;
            riskFactors.push('Credentials leaked in data breach');
        }
        
        if (rep.data_breach) {
            riskScore += 20;
            riskFactors.push('Email found in data breaches');
        }
        
        if (rep.blacklisted) {
            riskScore += 30;
            riskFactors.push('Email is blacklisted');
        }
        
        if (rep.spam) {
            riskScore += 25;
            riskFactors.push('Associated with spam');
        }
        
        if (rep.new_domain) {
            riskScore += 15;
            riskFactors.push('Domain is very new');
        }
        
        if (rep.suspicious_tld) {
            riskScore += 10;
            riskFactors.push('Suspicious top-level domain');
        }
    }

    // Check disposable
    if (disposable?.success && disposable.data.is_disposable) {
        riskScore += 30;
        riskFactors.push('Disposable/temporary email address');
    }

    // Check MX records
    if (mx?.success && !mx.data.has_mx) {
        riskScore += 25;
        riskFactors.push('No MX records (cannot receive email)');
    }

    // Check deliverability
    if (deliverability?.success && !deliverability.data.domain_reachable) {
        riskScore += 20;
        riskFactors.push('Domain not reachable');
    }

    // Syntax checks
    if (!isValidEmailSyntax(email)) {
        riskScore += 50;
        riskFactors.push('Invalid email syntax');
    }

    riskScore = Math.min(100, Math.round(riskScore));

    let riskLevel = 'low';
    if (riskScore >= 75) riskLevel = 'critical';
    else if (riskScore >= 50) riskLevel = 'high';
    else if (riskScore >= 25) riskLevel = 'medium';

    const recommendations = generateEmailRecommendations(
        riskScore,
        riskFactors,
        reputation,
        disposable,
        mx
    );

    // Determine if email is valid
    const isValid = riskScore < 50 && 
                   (!disposable?.success || !disposable.data.is_disposable) &&
                   (mx?.success && mx.data.has_mx);

    return {
        email: email,
        local_part: localPart,
        domain: domain,
        is_valid: isValid,
        risk_score: riskScore,
        risk_level: riskLevel,
        risk_factors: riskFactors,
        confidence: calculateConfidence(successfulAPIs.length),
        api_sources: successfulAPIs,
        syntax: {
            valid: isValidEmailSyntax(email),
            has_local_part: localPart && localPart.length > 0,
            has_domain: domain && domain.length > 0
        },
        reputation: reputation?.success ? reputation.data : null,
        disposable_check: disposable?.success ? disposable.data : null,
        mx_records: mx?.success ? mx.data : null,
        deliverability: deliverability?.success ? deliverability.data : null,
        recommendations: recommendations,
        analyzed_at: new Date().toISOString()
    };
}

function generateEmailRecommendations(
    riskScore: number,
    riskFactors: string[],
    reputation: any,
    disposable: any,
    mx: any
): string[] {
    const recommendations = [];

    if (riskScore >= 75) {
        recommendations.push('CRITICAL: Do not trust this email address');
        recommendations.push('Block or quarantine emails from this address');
        recommendations.push('Alert security team if already communicated');
    } else if (riskScore >= 50) {
        recommendations.push('HIGH RISK: Exercise extreme caution');
        recommendations.push('Verify sender through alternative communication channel');
        recommendations.push('Apply strict email filtering');
    } else if (riskScore >= 25) {
        recommendations.push('MEDIUM RISK: Proceed with caution');
        recommendations.push('Verify important requests independently');
        recommendations.push('Be wary of suspicious links or attachments');
    } else {
        recommendations.push('LOW RISK: Email appears legitimate');
        recommendations.push('Standard security best practices apply');
    }

    if (disposable?.success && disposable.data.is_disposable) {
        recommendations.push('Disposable email detected - not suitable for account registration');
    }

    if (mx?.success && !mx.data.has_mx) {
        recommendations.push('Cannot receive emails - likely invalid or misconfigured');
    }

    if (reputation?.success) {
        if (reputation.data.credentials_leaked) {
            recommendations.push('WARNING: This email was found in data breaches');
        }
        if (reputation.data.spam) {
            recommendations.push('This email has been associated with spam activity');
        }
    }

    if (riskFactors.length > 0) {
        recommendations.push(`Key concerns: ${riskFactors.slice(0, 3).join(', ')}`);
    }

    return recommendations;
}

function isValidEmailSyntax(email: string): boolean {
    // RFC 5322 compliant email regex (simplified)
    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    
    if (!emailRegex.test(email)) return false;
    
    const [local, domain] = email.split('@');
    
    // Check local part length (max 64 characters)
    if (local.length > 64) return false;
    
    // Check domain length (max 255 characters)
    if (domain.length > 255) return false;
    
    // Check for consecutive dots
    if (email.includes('..')) return false;
    
    return true;
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
                analysis_type: 'email',
                input_value: result.email,
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
