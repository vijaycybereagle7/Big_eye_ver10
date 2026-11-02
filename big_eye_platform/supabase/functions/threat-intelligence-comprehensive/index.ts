/**
 * Threat Intelligence Comprehensive
 * Aggregates multiple threat intelligence and IoC lookup APIs
 * 
 * APIs integrated:
 * - AlienVault OTX (unlimited with free API key)
 * - CrowdSec (50/day with free API key)
 * - VirusTotal (500/day with free API key) 
 * - Local threat feed analysis
 * 
 * Features:
 * - IoC (Indicator of Compromise) lookup
 * - File hash reputation (MD5, SHA1, SHA256)
 * - Threat pulse monitoring
 * - Malware family identification
 * - Attack pattern detection
 * - Historical threat data
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
        const { indicator, indicator_type } = await req.json();

        if (!indicator) {
            throw new Error('Indicator is required');
        }

        if (!indicator_type) {
            throw new Error('Indicator type is required (ip, domain, hash, url)');
        }

        // Validate indicator type
        const validTypes = ['ip', 'domain', 'hash', 'url', 'email'];
        if (!validTypes.includes(indicator_type)) {
            throw new Error(`Invalid indicator type. Must be one of: ${validTypes.join(', ')}`);
        }

        // Check cache
        const cacheKey = `threat_intel:${indicator_type}:${indicator}`;
        const cached = await checkCache(cacheKey);
        if (cached) {
            console.log('Cache hit for indicator:', indicator);
            return new Response(JSON.stringify({ data: cached, cached: true }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Run multiple checks in parallel
        const results = await Promise.allSettled([
            checkAlienVaultOTX(indicator, indicator_type),
            checkCrowdSec(indicator, indicator_type),
            checkVirusTotalReputation(indicator, indicator_type),
            analyzeThreatContext(indicator, indicator_type)
        ]);

        // Aggregate results
        const aggregated = aggregateThreatResults(results, indicator, indicator_type);

        // Cache result (2 hours TTL - threat landscape changes quickly)
        await cacheResult(cacheKey, aggregated, 2 * 60 * 60);

        return new Response(JSON.stringify({ data: aggregated, cached: false }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Threat intelligence error:', error);
        return new Response(JSON.stringify({
            error: {
                code: 'THREAT_INTEL_FAILED',
                message: error.message
            }
        }), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

// AlienVault OTX (unlimited with free API key)
async function checkAlienVaultOTX(indicator: string, type: string) {
    const apiKey = Deno.env.get('ALIENVAULT_OTX_API_KEY');
    if (!apiKey) {
        return {
            provider: 'AlienVault OTX',
            success: false,
            error: 'API key not configured'
        };
    }

    try {
        // Map our types to OTX types
        const otxType = type === 'hash' ? 'file' : type === 'url' ? 'url' : type;
        
        // Get general indicator data
        const response = await fetch(
            `https://otx.alienvault.com/api/v1/indicators/${otxType}/${indicator}/general`,
            {
                headers: {
                    'X-OTX-API-KEY': apiKey
                }
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Get pulse information (threat intelligence reports)
        const pulsesResponse = await fetch(
            `https://otx.alienvault.com/api/v1/indicators/${otxType}/${indicator}/url_list`,
            {
                headers: {
                    'X-OTX-API-KEY': apiKey
                }
            }
        );

        let pulses = [];
        if (pulsesResponse.ok) {
            const pulsesData = await pulsesResponse.json();
            pulses = pulsesData.url_list || [];
        }

        return {
            provider: 'AlienVault OTX',
            success: true,
            data: {
                pulse_count: data.pulse_info?.count || 0,
                pulses: pulses.slice(0, 10), // Top 10 pulses
                reputation: data.reputation || 0,
                malware_families: data.malware_families || [],
                adversary: data.adversary || null,
                first_seen: data.first_seen || null,
                last_seen: data.last_seen || null,
                whitelisted: data.whitelisted || false,
                validation: data.validation || []
            }
        };
    } catch (error) {
        return {
            provider: 'AlienVault OTX',
            success: false,
            error: error.message
        };
    }
}

// CrowdSec (50 queries/day with free API key)
async function checkCrowdSec(indicator: string, type: string) {
    const apiKey = Deno.env.get('CROWDSEC_API_KEY');
    
    // CrowdSec primarily focuses on IPs
    if (type !== 'ip' || !apiKey) {
        return {
            provider: 'CrowdSec',
            success: false,
            error: type !== 'ip' ? 'Only supports IP addresses' : 'API key not configured'
        };
    }

    try {
        const response = await fetch(
            `https://cti.api.crowdsec.net/v2/smoke/${indicator}`,
            {
                headers: {
                    'x-api-key': apiKey
                }
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        return {
            provider: 'CrowdSec',
            success: true,
            data: {
                reputation: data.reputation || 'neutral',
                aggressiveness: data.scores?.overall?.aggressiveness || 0,
                threat: data.scores?.overall?.threat || 0,
                trust: data.scores?.overall?.trust || 0,
                anomaly: data.scores?.overall?.anomaly || 0,
                total_score: data.scores?.overall?.total || 0,
                behaviors: data.behaviors || [],
                attack_details: data.attack_details || [],
                target_countries: data.target_countries || [],
                first_seen: data.history?.first_seen || null,
                last_seen: data.history?.last_seen || null,
                as_name: data.as_name || null,
                location: data.location || null
            }
        };
    } catch (error) {
        return {
            provider: 'CrowdSec',
            success: false,
            error: error.message
        };
    }
}

// VirusTotal (500/day with free API key)
async function checkVirusTotalReputation(indicator: string, type: string) {
    const apiKey = Deno.env.get('VIRUSTOTAL_API_KEY');
    if (!apiKey) {
        return {
            provider: 'VirusTotal',
            success: false,
            error: 'API key not configured'
        };
    }

    try {
        let endpoint = '';
        let identifier = indicator;

        // Determine endpoint based on type
        switch (type) {
            case 'ip':
                endpoint = `ip_addresses/${indicator}`;
                break;
            case 'domain':
                endpoint = `domains/${indicator}`;
                break;
            case 'url':
                // URLs need to be base64 encoded (without padding)
                identifier = btoa(indicator).replace(/=/g, '');
                endpoint = `urls/${identifier}`;
                break;
            case 'hash':
                endpoint = `files/${indicator}`;
                break;
            default:
                throw new Error(`Unsupported indicator type for VirusTotal: ${type}`);
        }

        const response = await fetch(
            `https://www.virustotal.com/api/v3/${endpoint}`,
            {
                headers: {
                    'x-apikey': apiKey
                }
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const attributes = data.data?.attributes || {};

        // Extract relevant data based on type
        const stats = attributes.last_analysis_stats || {};
        
        return {
            provider: 'VirusTotal',
            success: true,
            data: {
                malicious_count: stats.malicious || 0,
                suspicious_count: stats.suspicious || 0,
                harmless_count: stats.harmless || 0,
                undetected_count: stats.undetected || 0,
                total_engines: Object.values(stats).reduce((a: number, b: number) => a + b, 0),
                reputation: attributes.reputation || 0,
                last_analysis_date: attributes.last_analysis_date 
                    ? new Date(attributes.last_analysis_date * 1000).toISOString() 
                    : null,
                tags: attributes.tags || [],
                categories: attributes.categories || {},
                popular_threat_classification: attributes.popular_threat_classification || null
            }
        };
    } catch (error) {
        return {
            provider: 'VirusTotal',
            success: false,
            error: error.message
        };
    }
}

// Local threat context analysis
async function analyzeThreatContext(indicator: string, type: string) {
    try {
        const context: any = {
            indicator_age: null,
            threat_level: 'unknown',
            confidence: 0
        };

        // Analyze based on type
        if (type === 'hash') {
            // Check hash format and extract info
            const hashLength = indicator.length;
            if (hashLength === 32) context.hash_type = 'MD5';
            else if (hashLength === 40) context.hash_type = 'SHA1';
            else if (hashLength === 64) context.hash_type = 'SHA256';
        }

        return {
            provider: 'Threat Context Analysis',
            success: true,
            data: context
        };
    } catch (error) {
        return {
            provider: 'Threat Context Analysis',
            success: false,
            error: error.message
        };
    }
}

function aggregateThreatResults(results: any[], indicator: string, type: string) {
    const otx = results[0].status === 'fulfilled' ? results[0].value : null;
    const crowdsec = results[1].status === 'fulfilled' ? results[1].value : null;
    const virustotal = results[2].status === 'fulfilled' ? results[2].value : null;
    const context = results[3].status === 'fulfilled' ? results[3].value : null;

    let threatScore = 0;
    let threatFactors = [];
    let successfulAPIs = [];

    [otx, crowdsec, virustotal, context].forEach(result => {
        if (result && result.success) {
            successfulAPIs.push(result.provider);
        }
    });

    // AlienVault OTX analysis
    if (otx?.success) {
        if (otx.data.pulse_count > 0) {
            threatScore += Math.min(40, otx.data.pulse_count * 2);
            threatFactors.push(`Found in ${otx.data.pulse_count} threat intelligence reports`);
        }
        if (otx.data.malware_families && otx.data.malware_families.length > 0) {
            threatScore += 30;
            threatFactors.push(`Associated with malware: ${otx.data.malware_families.slice(0, 3).join(', ')}`);
        }
        if (otx.data.adversary) {
            threatScore += 20;
            threatFactors.push(`Linked to adversary: ${otx.data.adversary}`);
        }
    }

    // CrowdSec analysis
    if (crowdsec?.success) {
        const score = crowdsec.data.total_score || 0;
        if (score > 3) {
            threatScore += 30;
            threatFactors.push(`High CrowdSec threat score: ${score}/5`);
        } else if (score > 1) {
            threatScore += 15;
            threatFactors.push(`Moderate CrowdSec threat score: ${score}/5`);
        }

        if (crowdsec.data.behaviors && crowdsec.data.behaviors.length > 0) {
            threatFactors.push(`Attack behaviors: ${crowdsec.data.behaviors.slice(0, 3).join(', ')}`);
        }
    }

    // VirusTotal analysis
    if (virustotal?.success) {
        const maliciousCount = virustotal.data.malicious_count || 0;
        const totalEngines = virustotal.data.total_engines || 1;
        const detectionRate = (maliciousCount / totalEngines) * 100;

        if (detectionRate > 50) {
            threatScore += 50;
            threatFactors.push(`${maliciousCount}/${totalEngines} AV engines detected as malicious`);
        } else if (detectionRate > 20) {
            threatScore += 30;
            threatFactors.push(`${maliciousCount}/${totalEngines} AV engines flagged`);
        } else if (detectionRate > 0) {
            threatScore += 15;
            threatFactors.push(`${maliciousCount}/${totalEngines} AV engines show suspicion`);
        }

        if (virustotal.data.tags && virustotal.data.tags.length > 0) {
            const maliciousTags = virustotal.data.tags.filter((tag: string) =>
                tag.includes('malware') || tag.includes('trojan') || tag.includes('ransomware')
            );
            if (maliciousTags.length > 0) {
                threatFactors.push(`Tags: ${maliciousTags.slice(0, 3).join(', ')}`);
            }
        }
    }

    threatScore = Math.min(100, Math.round(threatScore));

    let threatLevel = 'low';
    if (threatScore >= 75) threatLevel = 'critical';
    else if (threatScore >= 50) threatLevel = 'high';
    else if (threatScore >= 25) threatLevel = 'medium';

    const recommendations = generateThreatRecommendations(
        threatScore,
        threatFactors,
        otx,
        crowdsec,
        virustotal,
        type
    );

    const isMalicious = threatScore >= 50 ||
                       (virustotal?.success && virustotal.data.malicious_count > 5) ||
                       (otx?.success && otx.data.pulse_count > 10);

    return {
        indicator: indicator,
        indicator_type: type,
        is_malicious: isMalicious,
        threat_score: threatScore,
        threat_level: threatLevel,
        threat_factors: threatFactors,
        confidence: calculateConfidence(successfulAPIs.length),
        api_sources: successfulAPIs,
        threat_intelligence: {
            alienvault_otx: otx?.success ? otx.data : null,
            crowdsec: crowdsec?.success ? crowdsec.data : null,
            virustotal: virustotal?.success ? virustotal.data : null,
            context: context?.success ? context.data : null
        },
        malware_families: otx?.data?.malware_families || [],
        attack_vectors: crowdsec?.data?.behaviors || [],
        recommendations: recommendations,
        analyzed_at: new Date().toISOString()
    };
}

function generateThreatRecommendations(
    threatScore: number,
    threatFactors: string[],
    otx: any,
    crowdsec: any,
    virustotal: any,
    type: string
): string[] {
    const recommendations = [];

    if (threatScore >= 75) {
        recommendations.push('CRITICAL THREAT: Immediate action required');
        recommendations.push('Block this indicator across all systems');
        recommendations.push('Investigate any systems that have interacted with this indicator');
        recommendations.push('Alert security team and initiate incident response');
    } else if (threatScore >= 50) {
        recommendations.push('HIGH THREAT: Strong evidence of malicious activity');
        recommendations.push('Implement blocking rules immediately');
        recommendations.push('Review logs for any exposure');
        recommendations.push('Consider this a confirmed threat');
    } else if (threatScore >= 25) {
        recommendations.push('MEDIUM THREAT: Suspicious activity detected');
        recommendations.push('Monitor closely for additional indicators');
        recommendations.push('Apply enhanced filtering rules');
        recommendations.push('Verify legitimacy before allowing access');
    } else if (threatScore > 0) {
        recommendations.push('LOW THREAT: Minor suspicion detected');
        recommendations.push('Continue standard monitoring');
        recommendations.push('No immediate action required');
    } else {
        recommendations.push('NO THREAT: No malicious indicators found');
        recommendations.push('Indicator appears clean');
        recommendations.push('Standard security protocols apply');
    }

    // Type-specific recommendations
    if (type === 'hash') {
        recommendations.push('For file hashes: Quarantine any files matching this hash');
    } else if (type === 'ip') {
        recommendations.push('For IP addresses: Consider blocking at firewall level');
    } else if (type === 'domain') {
        recommendations.push('For domains: Update DNS filtering rules');
    } else if (type === 'url') {
        recommendations.push('For URLs: Block in web proxy/gateway');
    }

    if (otx?.success && otx.data.malware_families?.length > 0) {
        recommendations.push(`Associated malware families: ${otx.data.malware_families.slice(0, 3).join(', ')}`);
        recommendations.push('Review malware family TTPs and check for related IoCs');
    }

    if (virustotal?.success && virustotal.data.malicious_count > 0) {
        recommendations.push(`${virustotal.data.malicious_count} security vendors flagged this as malicious`);
    }

    if (threatFactors.length > 0) {
        recommendations.push(`Key findings: ${threatFactors.slice(0, 2).join('; ')}`);
    }

    return recommendations;
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
                analysis_type: 'threat',
                input_value: result.indicator,
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
