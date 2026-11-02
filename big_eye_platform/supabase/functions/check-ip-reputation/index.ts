Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
        'Access-Control-Max-Age': '86400',
        'Access-Control-Allow-Credentials': 'false'
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const { ip, domain } = await req.json();

        let targetIP = ip;

        // If domain provided, resolve to IP
        if (domain && !ip) {
            targetIP = await resolveToIP(domain);
        }

        if (!targetIP) {
            throw new Error('IP address or domain is required');
        }

        // Validate IP format
        if (!isValidIP(targetIP)) {
            throw new Error('Invalid IP address format');
        }

        // Get comprehensive IP intelligence
        const [geoData, whoisData] = await Promise.allSettled([
            getGeoLocation(targetIP),
            getIPWhois(targetIP)
        ]);

        const result = {
            ip: targetIP,
            geolocation: geoData.status === 'fulfilled' ? geoData.value : { error: geoData.reason?.message },
            whois: whoisData.status === 'fulfilled' ? whoisData.value : { error: whoisData.reason?.message },
            threatScore: 0,
            riskLevel: 'unknown',
            recommendations: []
        };

        // Calculate threat score
        result.threatScore = calculateIPThreatScore(result);
        result.riskLevel = getThreatLevel(result.threatScore);
        result.recommendations = generateIPRecommendations(result);

        // Track analytics (non-blocking)
        trackAnalytics(req, 'IP Intelligence Dashboard', 'ip-reputation-check', {
            ip: targetIP,
            threatScore: result.threatScore,
            riskLevel: result.riskLevel,
            country: result.geolocation?.countryCode || 'unknown'
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('IP intelligence error:', error);

        const errorResponse = {
            error: {
                code: 'IP_INTELLIGENCE_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function resolveToIP(domain: string): Promise<string> {
    try {
        const cleanDomain = domain.toLowerCase().trim().replace(/^https?:\/\//, '').replace(/\/.*$/, '');
        
        // Use Cloudflare DNS-over-HTTPS
        const response = await fetch(`https://cloudflare-dns.com/dns-query?name=${cleanDomain}&type=A`, {
            headers: { 'Accept': 'application/dns-json' },
            signal: AbortSignal.timeout(5000)
        });

        if (!response.ok) {
            throw new Error('DNS resolution failed');
        }

        const data = await response.json();
        if (data.Answer && data.Answer.length > 0) {
            return data.Answer[0].data;
        }

        throw new Error('No A record found for domain');
    } catch (error) {
        throw new Error(`Domain resolution failed: ${error.message}`);
    }
}

function isValidIP(ip: string): boolean {
    // IPv4 validation
    const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (ipv4Pattern.test(ip)) {
        const parts = ip.split('.');
        return parts.every(part => {
            const num = parseInt(part, 10);
            return num >= 0 && num <= 255;
        });
    }
    return false;
}

async function getGeoLocation(ip: string): Promise<any> {
    try {
        // Use ipwhois.app (free, no key required)
        const response = await fetch(`https://ipwhois.app/json/${ip}`, {
            headers: { 'Accept': 'application/json' },
            signal: AbortSignal.timeout(5000)
        });

        if (!response.ok) {
            throw new Error('Geolocation lookup failed');
        }

        const data = await response.json();

        return {
            country: data.country || 'Unknown',
            countryCode: data.country_code || 'Unknown',
            region: data.region || 'Unknown',
            city: data.city || 'Unknown',
            latitude: data.latitude || null,
            longitude: data.longitude || null,
            timezone: data.timezone || 'Unknown',
            isp: data.isp || 'Unknown',
            org: data.org || 'Unknown',
            as: data.as || 'Unknown',
            asn: data.asn || 'Unknown'
        };
    } catch (error) {
        throw new Error(`Geolocation failed: ${error.message}`);
    }
}

async function getIPWhois(ip: string): Promise<any> {
    try {
        // Use ipwhois.app for WHOIS data
        const response = await fetch(`https://ipwhois.app/json/${ip}`, {
            headers: { 'Accept': 'application/json' },
            signal: AbortSignal.timeout(5000)
        });

        if (!response.ok) {
            throw new Error('WHOIS lookup failed');
        }

        const data = await response.json();

        return {
            isp: data.isp || 'Unknown',
            organization: data.org || 'Unknown',
            asn: data.asn || 'Unknown',
            networkRange: data.range || 'Unknown',
            type: data.type || 'Unknown',
            isHosting: detectHosting(data),
            isVPN: detectVPN(data),
            isTor: data.is_tor === true || data.is_tor === 'true'
        };
    } catch (error) {
        throw new Error(`WHOIS failed: ${error.message}`);
    }
}

function detectHosting(data: any): boolean {
    const hostingKeywords = [
        'amazon', 'aws', 'azure', 'google cloud', 'digitalocean',
        'linode', 'vultr', 'ovh', 'hetzner', 'hosting', 'datacenter',
        'cloud', 'server'
    ];

    const orgLower = (data.org || '').toLowerCase();
    const ispLower = (data.isp || '').toLowerCase();

    return hostingKeywords.some(keyword =>
        orgLower.includes(keyword) || ispLower.includes(keyword)
    );
}

function detectVPN(data: any): boolean {
    const vpnKeywords = [
        'vpn', 'proxy', 'tor', 'anonymizer', 'privacy',
        'nordvpn', 'expressvpn', 'mullvad', 'protonvpn'
    ];

    const orgLower = (data.org || '').toLowerCase();
    const ispLower = (data.isp || '').toLowerCase();

    return vpnKeywords.some(keyword =>
        orgLower.includes(keyword) || ispLower.includes(keyword)
    );
}

function calculateIPThreatScore(result: any): number {
    let score = 0;

    // Check for suspicious characteristics
    if (result.whois && !result.whois.error) {
        // Hosting provider IPs are more likely to be used for phishing
        if (result.whois.isHosting) {
            score += 20;
        }

        // VPN/Proxy usage
        if (result.whois.isVPN) {
            score += 25;
        }

        // Tor exit nodes
        if (result.whois.isTor) {
            score += 40;
        }
    }

    // Check geolocation for known high-risk regions
    if (result.geolocation && !result.geolocation.error) {
        const highRiskCountries = ['RU', 'CN', 'NK', 'IR']; // Example
        if (highRiskCountries.includes(result.geolocation.countryCode)) {
            score += 15;
        }
    }

    return Math.min(score, 100);
}

function getThreatLevel(score: number): string {
    if (score >= 75) return 'critical';
    if (score >= 50) return 'high';
    if (score >= 30) return 'medium';
    if (score >= 15) return 'low';
    return 'safe';
}

function generateIPRecommendations(result: any): string[] {
    const recommendations: string[] = [];

    if (result.whois && !result.whois.error) {
        if (result.whois.isTor) {
            recommendations.push('IP is a Tor exit node - HIGH RISK for anonymous activity');
        }
        if (result.whois.isVPN) {
            recommendations.push('IP appears to be from a VPN/proxy service - exercise caution');
        }
        if (result.whois.isHosting) {
            recommendations.push('IP is from a hosting provider - commonly used for phishing campaigns');
        }
    }

    if (result.geolocation && !result.geolocation.error) {
        recommendations.push(`IP geolocation: ${result.geolocation.city}, ${result.geolocation.country}`);
        recommendations.push(`ISP: ${result.geolocation.isp}`);
    }

    if (recommendations.length === 0) {
        recommendations.push('No significant risk indicators detected for this IP address');
    }

    return recommendations;
}

async function trackAnalytics(req: Request, toolName: string, analysisType: string, additionalData: any): Promise<void> {
    try {
        const authHeader = req.headers.get('authorization');
        if (!authHeader) return;

        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        if (!supabaseUrl || !serviceRoleKey) return;

        const token = authHeader.replace('Bearer ', '');
        const userResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'apikey': serviceRoleKey
            }
        });

        if (!userResponse.ok) return;

        const userData = await userResponse.json();
        const userId = userData.id;

        await fetch(`${supabaseUrl}/rest/v1/user_analytics`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                tool_name: toolName,
                analysis_type: analysisType,
                success: true,
                additional_data: additionalData,
                timestamp: new Date().toISOString()
            })
        });
    } catch (error) {
        console.error('Failed to track analytics:', error);
    }
}
