/**
 * IP Analysis Comprehensive
 * Aggregates multiple IP analysis APIs for comprehensive IP intelligence
 * 
 * APIs integrated:
 * - IP-API (free, 45/min) - Primary geolocation
 * - AbuseIPDB (1000/day) - IP reputation (if key available)
 * - IPQualityScore (5000/month) - Fraud scoring (if key available)
 * - Spamhaus - DNS-based blacklist checking
 * 
 * Tier 1 (No API key): IP-API, Spamhaus
 * Tier 2 (API key): AbuseIPDB, IPQualityScore
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
        const { ip_address } = await req.json();

        if (!ip_address) {
            throw new Error('IP address is required');
        }

        // Validate IP format
        if (!isValidIP(ip_address)) {
            throw new Error('Invalid IP address format');
        }

        // Check cache first
        const cacheKey = `ip_analysis:${ip_address}`;
        const cached = await checkCache(cacheKey);
        if (cached) {
            console.log('Cache hit for IP:', ip_address);
            return new Response(JSON.stringify({ data: cached, cached: true }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Run multiple API checks in parallel
        const results = await Promise.allSettled([
            checkIPAPI(ip_address),
            checkAbuseIPDB(ip_address),
            checkIPQualityScore(ip_address),
            checkSpamhaus(ip_address)
        ]);

        // Aggregate results
        const aggregated = aggregateIPResults(results, ip_address);

        // Cache the result (6 hours TTL)
        await cacheResult(cacheKey, aggregated, 6 * 60 * 60);

        return new Response(JSON.stringify({ data: aggregated, cached: false }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('IP analysis error:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'IP_ANALYSIS_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// IP-API (Free, no key needed, 45 req/min)
async function checkIPAPI(ip: string) {
    try {
        const response = await fetch(
            `http://ip-api.com/json/${ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,mobile,proxy,hosting,query`
        );
        const data = await response.json();
        
        if (data.status === 'fail') {
            throw new Error(data.message || 'IP-API request failed');
        }

        return {
            provider: 'IP-API',
            success: true,
            data: {
                geolocation: {
                    country: data.country,
                    country_code: data.countryCode,
                    region: data.regionName,
                    city: data.city,
                    zip: data.zip,
                    latitude: data.lat,
                    longitude: data.lon,
                    timezone: data.timezone
                },
                network: {
                    isp: data.isp,
                    organization: data.org,
                    asn: data.as,
                    as_name: data.asname
                },
                flags: {
                    is_mobile: data.mobile || false,
                    is_proxy: data.proxy || false,
                    is_hosting: data.hosting || false
                }
            }
        };
    } catch (error) {
        return {
            provider: 'IP-API',
            success: false,
            error: error.message
        };
    }
}

// AbuseIPDB (1000/day with free API key)
async function checkAbuseIPDB(ip: string) {
    const apiKey = Deno.env.get('ABUSEIPDB_API_KEY');
    if (!apiKey) {
        return {
            provider: 'AbuseIPDB',
            success: false,
            error: 'API key not configured'
        };
    }

    try {
        const response = await fetch(
            `https://api.abuseipdb.com/api/v2/check?ipAddress=${ip}&maxAgeInDays=90&verbose`,
            {
                headers: {
                    'Key': apiKey,
                    'Accept': 'application/json'
                }
            }
        );

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.errors?.[0]?.detail || 'AbuseIPDB request failed');
        }

        const data = result.data;
        
        return {
            provider: 'AbuseIPDB',
            success: true,
            data: {
                abuse_confidence_score: data.abuseConfidenceScore,
                total_reports: data.totalReports,
                num_distinct_users: data.numDistinctUsers,
                last_reported_at: data.lastReportedAt,
                is_public: data.isPublic,
                is_whitelisted: data.isWhitelisted,
                country_code: data.countryCode,
                usage_type: data.usageType,
                isp: data.isp,
                domain: data.domain,
                is_tor: data.isTor,
                reports: data.reports || []
            }
        };
    } catch (error) {
        return {
            provider: 'AbuseIPDB',
            success: false,
            error: error.message
        };
    }
}

// IPQualityScore (5000/month with free API key)
async function checkIPQualityScore(ip: string) {
    const apiKey = Deno.env.get('IPQUALITYSCORE_API_KEY');
    if (!apiKey) {
        return {
            provider: 'IPQualityScore',
            success: false,
            error: 'API key not configured'
        };
    }

    try {
        const response = await fetch(
            `https://ipqualityscore.com/api/json/ip/${apiKey}/${ip}?strictness=0&allow_public_access_points=true`
        );

        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'IPQualityScore request failed');
        }

        return {
            provider: 'IPQualityScore',
            success: true,
            data: {
                fraud_score: data.fraud_score,
                country_code: data.country_code,
                region: data.region,
                city: data.city,
                isp: data.ISP,
                asn: data.ASN,
                organization: data.organization,
                is_crawler: data.is_crawler,
                timezone: data.timezone,
                mobile: data.mobile,
                host: data.host,
                proxy: data.proxy,
                vpn: data.vpn,
                tor: data.tor,
                active_vpn: data.active_vpn,
                active_tor: data.active_tor,
                recent_abuse: data.recent_abuse,
                bot_status: data.bot_status,
                connection_type: data.connection_type,
                abuse_velocity: data.abuse_velocity
            }
        };
    } catch (error) {
        return {
            provider: 'IPQualityScore',
            success: false,
            error: error.message
        };
    }
}

// Spamhaus (DNS-based, free for low volume)
async function checkSpamhaus(ip: string) {
    try {
        // Reverse IP for DNS query
        const reversedIP = ip.split('.').reverse().join('.');
        const zones = [
            'zen.spamhaus.org',  // Combined list
            'sbl.spamhaus.org',  // Spam Block List
            'xbl.spamhaus.org'   // Exploit Block List
        ];

        const checks = await Promise.allSettled(
            zones.map(zone => checkDNSBL(reversedIP, zone))
        );

        const listed = checks.filter(r => r.status === 'fulfilled' && r.value.listed);
        
        return {
            provider: 'Spamhaus',
            success: true,
            data: {
                is_listed: listed.length > 0,
                lists: listed.map(r => r.value),
                checked_zones: zones.length
            }
        };
    } catch (error) {
        return {
            provider: 'Spamhaus',
            success: false,
            error: error.message
        };
    }
}

async function checkDNSBL(reversedIP: string, zone: string): Promise<any> {
    try {
        const query = `${reversedIP}.${zone}`;
        // Simple DNS check - in production, use proper DNS library
        const response = await fetch(`https://dns.google/resolve?name=${query}&type=A`);
        const data = await response.json();
        
        return {
            listed: data.Status === 0 && data.Answer && data.Answer.length > 0,
            zone: zone,
            response_code: data.Status
        };
    } catch {
        return { listed: false, zone: zone };
    }
}

function aggregateIPResults(results: any[], ip: string) {
    const ipapi = results[0].status === 'fulfilled' ? results[0].value : null;
    const abuseipdb = results[1].status === 'fulfilled' ? results[1].value : null;
    const ipqs = results[2].status === 'fulfilled' ? results[2].value : null;
    const spamhaus = results[3].status === 'fulfilled' ? results[3].value : null;

    // Calculate overall risk score (0-100, where 100 is highest risk)
    let riskScore = 0;
    let riskFactors = [];
    let successfulAPIs = [];

    // Collect successful API responses
    [ipapi, abuseipdb, ipqs, spamhaus].forEach(result => {
        if (result && result.success) {
            successfulAPIs.push(result.provider);
        }
    });

    // Check AbuseIPDB score
    if (abuseipdb?.success && abuseipdb.data.abuse_confidence_score) {
        riskScore += abuseipdb.data.abuse_confidence_score * 0.4; // 40% weight
        if (abuseipdb.data.abuse_confidence_score > 50) {
            riskFactors.push(`High abuse confidence (${abuseipdb.data.abuse_confidence_score}%)`);
        }
    }

    // Check IPQualityScore
    if (ipqs?.success && ipqs.data.fraud_score) {
        riskScore += ipqs.data.fraud_score * 0.3; // 30% weight
        if (ipqs.data.fraud_score > 75) {
            riskFactors.push(`High fraud score (${ipqs.data.fraud_score})`);
        }
        if (ipqs.data.vpn || ipqs.data.proxy || ipqs.data.tor) {
            riskScore += 20;
            riskFactors.push('VPN/Proxy/Tor detected');
        }
    }

    // Check Spamhaus
    if (spamhaus?.success && spamhaus.data.is_listed) {
        riskScore += 30; // 30% weight
        riskFactors.push(`Listed on Spamhaus (${spamhaus.data.lists.length} lists)`);
    }

    // Check IP-API flags
    if (ipapi?.success) {
        if (ipapi.data.flags.is_proxy) {
            riskScore += 10;
            riskFactors.push('Proxy detected');
        }
        if (ipapi.data.flags.is_hosting) {
            riskScore += 5;
            riskFactors.push('Hosting/datacenter IP');
        }
    }

    // Cap at 100
    riskScore = Math.min(100, Math.round(riskScore));

    // Determine risk level
    let riskLevel = 'low';
    if (riskScore >= 75) riskLevel = 'critical';
    else if (riskScore >= 50) riskLevel = 'high';
    else if (riskScore >= 25) riskLevel = 'medium';

    // Generate recommendations
    const recommendations = generateIPRecommendations(riskScore, riskFactors, ipapi, abuseipdb, ipqs);

    return {
        ip_address: ip,
        risk_score: riskScore,
        risk_level: riskLevel,
        risk_factors: riskFactors,
        confidence: calculateConfidence(successfulAPIs.length),
        api_sources: successfulAPIs,
        geolocation: ipapi?.success ? ipapi.data.geolocation : null,
        network_info: ipapi?.success ? ipapi.data.network : null,
        reputation: {
            abuseipdb: abuseipdb?.success ? abuseipdb.data : null,
            ipqualityscore: ipqs?.success ? ipqs.data : null,
            spamhaus: spamhaus?.success ? spamhaus.data : null
        },
        flags: {
            is_proxy: ipapi?.data?.flags?.is_proxy || ipqs?.data?.proxy || false,
            is_vpn: ipqs?.data?.vpn || false,
            is_tor: ipqs?.data?.tor || abuseipdb?.data?.is_tor || false,
            is_hosting: ipapi?.data?.flags?.is_hosting || false,
            is_mobile: ipapi?.data?.flags?.is_mobile || ipqs?.data?.mobile || false,
            is_crawler: ipqs?.data?.is_crawler || false,
            is_blacklisted: spamhaus?.data?.is_listed || false
        },
        recommendations: recommendations,
        analyzed_at: new Date().toISOString()
    };
}

function generateIPRecommendations(riskScore: number, riskFactors: string[], ipapi: any, abuseipdb: any, ipqs: any): string[] {
    const recommendations = [];

    if (riskScore >= 75) {
        recommendations.push('CRITICAL: Block this IP immediately');
        recommendations.push('Investigate all activity from this IP address');
        recommendations.push('Review security logs for potential compromise');
    } else if (riskScore >= 50) {
        recommendations.push('HIGH RISK: Implement additional authentication measures');
        recommendations.push('Monitor activity from this IP closely');
        recommendations.push('Consider temporary blocking or rate limiting');
    } else if (riskScore >= 25) {
        recommendations.push('MEDIUM RISK: Exercise caution with this IP');
        recommendations.push('Apply standard security measures');
        recommendations.push('Monitor for suspicious patterns');
    } else {
        recommendations.push('LOW RISK: IP appears legitimate');
        recommendations.push('Standard security protocols apply');
    }

    if (riskFactors.length > 0) {
        recommendations.push(`Key concerns: ${riskFactors.join(', ')}`);
    }

    if (abuseipdb?.success && abuseipdb.data.total_reports > 0) {
        recommendations.push(`This IP has ${abuseipdb.data.total_reports} abuse reports`);
    }

    return recommendations;
}

function calculateConfidence(successfulAPIs: number): number {
    // Confidence based on number of successful API responses
    // 4 APIs = 100%, 3 = 75%, 2 = 50%, 1 = 25%
    return Math.round((successfulAPIs / 4) * 100);
}

function isValidIP(ip: string): boolean {
    // Basic IPv4 validation
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipv4Regex.test(ip)) return false;
    
    const parts = ip.split('.');
    return parts.every(part => {
        const num = parseInt(part);
        return num >= 0 && num <= 255;
    });
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
            // Increment hit count
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
                analysis_type: 'ip',
                input_value: result.ip_address,
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
