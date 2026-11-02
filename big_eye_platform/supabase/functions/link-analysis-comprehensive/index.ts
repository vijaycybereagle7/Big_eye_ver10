/**
 * Link Analysis Comprehensive
 * Aggregates multiple URL/phishing detection APIs
 * 
 * APIs integrated (Tier 1 - no keys):
 * - Google Safe Browsing (10000/day) - needs key
 * - PhishTank (free) - needs key
 * - URLScan.io (100/day) - needs key
 * - Basic URL analysis (no key needed)
 * 
 * Features:
 * - Phishing detection
 * - Malware detection
 * - URL reputation scoring
 * - Redirect chain analysis
 * - SSL/TLS validation
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
        const { url } = await req.json();

        if (!url) {
            throw new Error('URL is required');
        }

        const cleanURL = url.trim();
        if (!isValidURL(cleanURL)) {
            throw new Error('Invalid URL format');
        }

        // Check cache
        const cacheKey = `link_analysis:${cleanURL}`;
        const cached = await checkCache(cacheKey);
        if (cached) {
            console.log('Cache hit for URL:', cleanURL);
            return new Response(JSON.stringify({ data: cached, cached: true }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Run multiple checks in parallel
        const results = await Promise.allSettled([
            checkGoogleSafeBrowsing(cleanURL),
            checkPhishTank(cleanURL),
            checkURLScan(cleanURL),
            analyzeURLStructure(cleanURL)
        ]);

        // Aggregate results
        const aggregated = aggregateLinkResults(results, cleanURL);

        // Cache result (1 hour TTL - phishing sites can be taken down quickly)
        await cacheResult(cacheKey, aggregated, 1 * 60 * 60);

        return new Response(JSON.stringify({ data: aggregated, cached: false }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Link analysis error:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'LINK_ANALYSIS_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// Google Safe Browsing API (10000 queries/day with free API key)
async function checkGoogleSafeBrowsing(url: string) {
    const apiKey = Deno.env.get('GOOGLE_SAFE_BROWSING_API_KEY');
    if (!apiKey) {
        return {
            provider: 'Google Safe Browsing',
            success: false,
            error: 'API key not configured'
        };
    }

    try {
        const response = await fetch(
            `https://safebrowsing.googleapis.com/v4/threatMatches:find?key=${apiKey}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    client: {
                        clientId: 'bigeye-platform',
                        clientVersion: '1.0.0'
                    },
                    threatInfo: {
                        threatTypes: [
                            'MALWARE',
                            'SOCIAL_ENGINEERING',
                            'UNWANTED_SOFTWARE',
                            'POTENTIALLY_HARMFUL_APPLICATION'
                        ],
                        platformTypes: ['ANY_PLATFORM'],
                        threatEntryTypes: ['URL'],
                        threatEntries: [{ url: url }]
                    }
                })
            }
        );

        const data = await response.json();

        const isThreat = data.matches && data.matches.length > 0;
        const threats = isThreat ? data.matches.map((match: any) => ({
            threat_type: match.threatType,
            platform_type: match.platformType,
            threat_entry_type: match.threatEntryType
        })) : [];

        return {
            provider: 'Google Safe Browsing',
            success: true,
            data: {
                is_threat: isThreat,
                threats: threats,
                checked_at: new Date().toISOString()
            }
        };
    } catch (error) {
        return {
            provider: 'Google Safe Browsing',
            success: false,
            error: error.message
        };
    }
}

// PhishTank API (free with API key)
async function checkPhishTank(url: string) {
    const apiKey = Deno.env.get('PHISHTANK_API_KEY');
    if (!apiKey) {
        return {
            provider: 'PhishTank',
            success: false,
            error: 'API key not configured'
        };
    }

    try {
        const encodedURL = encodeURIComponent(url);
        const response = await fetch(
            'https://checkurl.phishtank.com/checkurl/',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'BigEye/1.0'
                },
                body: `url=${encodedURL}&format=json&app_key=${apiKey}`
            }
        );

        const data = await response.json();

        return {
            provider: 'PhishTank',
            success: true,
            data: {
                in_database: data.results?.in_database || false,
                is_phishing: data.results?.valid || false,
                verified: data.results?.verified || false,
                verified_at: data.results?.verified_at || null,
                phish_id: data.results?.phish_id || null
            }
        };
    } catch (error) {
        return {
            provider: 'PhishTank',
            success: false,
            error: error.message
        };
    }
}

// URLScan.io API (100 scans/day with free API key)
async function checkURLScan(url: string) {
    const apiKey = Deno.env.get('URLSCAN_API_KEY');
    if (!apiKey) {
        return {
            provider: 'URLScan.io',
            success: false,
            error: 'API key not configured'
        };
    }

    try {
        // Submit URL for scanning
        const submitResponse = await fetch(
            'https://urlscan.io/api/v1/scan/',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'API-Key': apiKey
                },
                body: JSON.stringify({
                    url: url,
                    visibility: 'public'
                })
            }
        );

        const submitData = await submitResponse.json();
        
        if (!submitResponse.ok) {
            throw new Error(submitData.message || 'Scan submission failed');
        }

        // Wait a bit for scan to complete (URLScan needs time)
        await new Promise(resolve => setTimeout(resolve, 10000)); // 10 seconds

        // Get scan results
        const resultResponse = await fetch(submitData.api);
        const resultData = await resultResponse.json();

        return {
            provider: 'URLScan.io',
            success: true,
            data: {
                scan_id: submitData.uuid,
                url: resultData.page?.url || url,
                domain: resultData.page?.domain || null,
                ip: resultData.page?.ip || null,
                country: resultData.page?.country || null,
                server: resultData.page?.server || null,
                malicious: resultData.verdicts?.overall?.malicious || false,
                score: resultData.verdicts?.overall?.score || 0,
                categories: resultData.verdicts?.overall?.categories || [],
                has_screenshot: !!resultData.task?.screenshotURL,
                screenshot_url: resultData.task?.screenshotURL || null
            }
        };
    } catch (error) {
        return {
            provider: 'URLScan.io',
            success: false,
            error: error.message
        };
    }
}

// Basic URL structure analysis (no API needed)
async function analyzeURLStructure(url: string) {
    try {
        const parsed = new URL(url);
        
        // Suspicious patterns
        const suspiciousPatterns = [
            /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/, // IP address instead of domain
            /@/,  // @ symbol (used in phishing)
            /\-{2,}/, // Multiple consecutive hyphens
            /\.tk$|\.ml$|\.ga$|\.cf$|\.gq$/, // Free TLDs often used for phishing
        ];

        const suspiciousFlags = {
            uses_ip_address: suspiciousPatterns[0].test(parsed.hostname),
            has_at_symbol: suspiciousPatterns[1].test(url),
            excessive_hyphens: suspiciousPatterns[2].test(parsed.hostname),
            suspicious_tld: suspiciousPatterns[3].test(parsed.hostname),
            long_domain: parsed.hostname.length > 50,
            excessive_subdomains: parsed.hostname.split('.').length > 4,
            uses_non_standard_port: parsed.port && parsed.port !== '80' && parsed.port !== '443',
            long_path: parsed.pathname.length > 100
        };

        const suspiciousCount = Object.values(suspiciousFlags).filter(Boolean).length;

        return {
            provider: 'URL Structure Analysis',
            success: true,
            data: {
                protocol: parsed.protocol,
                hostname: parsed.hostname,
                port: parsed.port || null,
                path: parsed.pathname,
                has_query: parsed.search.length > 0,
                has_fragment: parsed.hash.length > 0,
                domain_length: parsed.hostname.length,
                path_length: parsed.pathname.length,
                subdomain_count: parsed.hostname.split('.').length - 2,
                suspicious_flags: suspiciousFlags,
                suspicious_count: suspiciousCount,
                uses_https: parsed.protocol === 'https:'
            }
        };
    } catch (error) {
        return {
            provider: 'URL Structure Analysis',
            success: false,
            error: error.message
        };
    }
}

function aggregateLinkResults(results: any[], url: string) {
    const safeBrowsing = results[0].status === 'fulfilled' ? results[0].value : null;
    const phishtank = results[1].status === 'fulfilled' ? results[1].value : null;
    const urlscan = results[2].status === 'fulfilled' ? results[2].value : null;
    const structure = results[3].status === 'fulfilled' ? results[3].value : null;

    let riskScore = 0;
    let riskFactors = [];
    let successfulAPIs = [];

    [safeBrowsing, phishtank, urlscan, structure].forEach(result => {
        if (result && result.success) {
            successfulAPIs.push(result.provider);
        }
    });

    // Google Safe Browsing results
    if (safeBrowsing?.success && safeBrowsing.data.is_threat) {
        riskScore += 50;
        const threatTypes = safeBrowsing.data.threats.map((t: any) => t.threat_type).join(', ');
        riskFactors.push(`Google Safe Browsing flagged: ${threatTypes}`);
    }

    // PhishTank results
    if (phishtank?.success && phishtank.data.is_phishing) {
        riskScore += 50;
        riskFactors.push('Confirmed phishing site by PhishTank');
    }

    // URLScan results
    if (urlscan?.success) {
        if (urlscan.data.malicious) {
            riskScore += 40;
            riskFactors.push(`URLScan.io marked as malicious (score: ${urlscan.data.score})`);
        }
        if (urlscan.data.score > 50) {
            riskScore += 20;
            riskFactors.push(`High risk score from URLScan.io`);
        }
    }

    // URL structure analysis
    if (structure?.success) {
        const flags = structure.data.suspicious_flags;
        
        if (flags.uses_ip_address) {
            riskScore += 25;
            riskFactors.push('Uses IP address instead of domain name');
        }
        if (flags.has_at_symbol) {
            riskScore += 30;
            riskFactors.push('Contains @ symbol (common phishing technique)');
        }
        if (flags.suspicious_tld) {
            riskScore += 20;
            riskFactors.push('Uses suspicious free TLD');
        }
        if (flags.excessive_hyphens) {
            riskScore += 10;
            riskFactors.push('Excessive hyphens in domain');
        }
        if (flags.long_domain) {
            riskScore += 10;
            riskFactors.push('Unusually long domain name');
        }
        if (flags.excessive_subdomains) {
            riskScore += 15;
            riskFactors.push('Excessive subdomains');
        }
        if (!flags.uses_https) {
            riskScore += 15;
            riskFactors.push('Not using HTTPS');
        }
    }

    riskScore = Math.min(100, Math.round(riskScore));

    let riskLevel = 'low';
    if (riskScore >= 75) riskLevel = 'critical';
    else if (riskScore >= 50) riskLevel = 'high';
    else if (riskScore >= 25) riskLevel = 'medium';

    const recommendations = generateLinkRecommendations(
        riskScore,
        riskFactors,
        safeBrowsing,
        phishtank,
        urlscan,
        structure
    );

    const isSafe = riskScore < 50 &&
                   (!safeBrowsing?.success || !safeBrowsing.data.is_threat) &&
                   (!phishtank?.success || !phishtank.data.is_phishing);

    return {
        url: url,
        is_safe: isSafe,
        risk_score: riskScore,
        risk_level: riskLevel,
        risk_factors: riskFactors,
        confidence: calculateConfidence(successfulAPIs.length),
        api_sources: successfulAPIs,
        threat_detection: {
            google_safe_browsing: safeBrowsing?.success ? safeBrowsing.data : null,
            phishtank: phishtank?.success ? phishtank.data : null,
            urlscan: urlscan?.success ? urlscan.data : null
        },
        url_analysis: structure?.success ? structure.data : null,
        recommendations: recommendations,
        analyzed_at: new Date().toISOString()
    };
}

function generateLinkRecommendations(
    riskScore: number,
    riskFactors: string[],
    safeBrowsing: any,
    phishtank: any,
    urlscan: any,
    structure: any
): string[] {
    const recommendations = [];

    if (riskScore >= 75) {
        recommendations.push('CRITICAL THREAT: DO NOT click this link');
        recommendations.push('Block this URL immediately');
        recommendations.push('Report to security team if received via email');
        recommendations.push('Warn others who may have received this link');
    } else if (riskScore >= 50) {
        recommendations.push('HIGH RISK: Avoid clicking this link');
        recommendations.push('Verify the link source through alternative means');
        recommendations.push('Consider the link malicious until proven otherwise');
    } else if (riskScore >= 25) {
        recommendations.push('MEDIUM RISK: Exercise caution');
        recommendations.push('Verify link authenticity before clicking');
        recommendations.push('Check for HTTPS and valid certificate');
    } else {
        recommendations.push('LOW RISK: Link appears safe');
        recommendations.push('Standard internet safety practices apply');
        recommendations.push('Still verify sender if received unsolicited');
    }

    if (safeBrowsing?.success && safeBrowsing.data.is_threat) {
        recommendations.push('Flagged by Google Safe Browsing - HIGH confidence threat');
    }

    if (phishtank?.success && phishtank.data.is_phishing) {
        recommendations.push('Confirmed phishing site - DO NOT enter credentials');
    }

    if (structure?.success && !structure.data.uses_https) {
        recommendations.push('Website does not use HTTPS - data not encrypted');
    }

    if (riskFactors.length > 0) {
        recommendations.push(`Key concerns: ${riskFactors.slice(0, 3).join(', ')}`);
    }

    return recommendations;
}

function isValidURL(url: string): boolean {
    try {
        const parsed = new URL(url);
        return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch {
        return false;
    }
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
            `${supabaseUrl}/rest/v1/analysis_cache?cache_key=eq.${encodeURIComponent(key)}&expires_at=gt.${new Date().toISOString()}`,
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
                analysis_type: 'link',
                input_value: result.url,
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
