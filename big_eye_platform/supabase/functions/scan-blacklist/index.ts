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
        const { ip, domain, email } = await req.json();

        let targetIP = ip;

        // If domain provided, resolve to IP
        if (domain && !ip) {
            targetIP = await resolveToIP(domain);
        }

        // If email provided, extract domain and resolve
        if (email && !ip && !domain) {
            const emailDomain = email.split('@')[1];
            if (emailDomain) {
                targetIP = await resolveToIP(emailDomain);
            }
        }

        if (!targetIP) {
            throw new Error('IP address, domain, or email is required');
        }

        // Validate IP format
        if (!isValidIP(targetIP)) {
            throw new Error('Invalid IP address format');
        }

        // Get AbuseIPDB API key
        const apiKey = Deno.env.get('ABUSEIPDB_API_KEY');

        let abuseIPDBData = null;

        if (apiKey) {
            // Use AbuseIPDB API for comprehensive reputation check
            try {
                abuseIPDBData = await checkAbuseIPDB(targetIP, apiKey);
            } catch (error) {
                console.warn('AbuseIPDB check failed:', error.message);
            }
        }

        // Perform basic checks even without API key
        const basicChecks = performBasicIPChecks(targetIP);

        const result = {
            ip: targetIP,
            abuseIPDB: abuseIPDBData || {
                available: false,
                message: 'Configure ABUSEIPDB_API_KEY for comprehensive blacklist scanning',
                configureInstructions: 'Set ABUSEIPDB_API_KEY environment variable with your API key from abuseipdb.com'
            },
            basicChecks,
            overallThreatScore: abuseIPDBData ? abuseIPDBData.abuseConfidenceScore : basicChecks.threatScore,
            riskLevel: getThreatLevel(abuseIPDBData ? abuseIPDBData.abuseConfidenceScore : basicChecks.threatScore),
            blacklisted: abuseIPDBData ? abuseIPDBData.isBlacklisted : false,
            recommendation: getRecommendation(abuseIPDBData ? abuseIPDBData.abuseConfidenceScore : basicChecks.threatScore)
        };

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Blacklist & Reputation Scanner', 'blacklist-scan', {
            ip: targetIP,
            threatScore: result.overallThreatScore,
            riskLevel: result.riskLevel,
            blacklisted: result.blacklisted
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Blacklist scan error:', error);

        const errorResponse = {
            error: {
                code: 'BLACKLIST_SCAN_FAILED',
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

async function checkAbuseIPDB(ip: string, apiKey: string): Promise<any> {
    try {
        const response = await fetch(`https://api.abuseipdb.com/api/v2/check?ipAddress=${ip}&maxAgeInDays=90&verbose`, {
            headers: {
                'Key': apiKey,
                'Accept': 'application/json'
            },
            signal: AbortSignal.timeout(10000)
        });

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Invalid AbuseIPDB API key');
            }
            throw new Error(`AbuseIPDB API returned status ${response.status}`);
        }

        const result = await response.json();
        const data = result.data;

        return {
            available: true,
            ipAddress: data.ipAddress,
            isPublic: data.isPublic,
            isWhitelisted: data.isWhitelisted,
            abuseConfidenceScore: data.abuseConfidenceScore,
            countryCode: data.countryCode,
            countryName: data.countryName,
            usageType: data.usageType,
            isp: data.isp,
            domain: data.domain,
            hostnames: data.hostnames || [],
            isTor: data.isTor,
            totalReports: data.totalReports,
            numDistinctUsers: data.numDistinctUsers,
            lastReportedAt: data.lastReportedAt,
            isBlacklisted: data.abuseConfidenceScore >= 75 || data.totalReports > 10,
            reports: data.reports ? data.reports.slice(0, 5) : [] // Limit to 5 most recent
        };
    } catch (error) {
        throw new Error(`AbuseIPDB check failed: ${error.message}`);
    }
}

function performBasicIPChecks(ip: string): any {
    // Basic IP checks without external API
    const parts = ip.split('.').map(Number);
    
    // Check for private IP ranges
    const isPrivate = 
        parts[0] === 10 ||
        (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) ||
        (parts[0] === 192 && parts[1] === 168) ||
        parts[0] === 127;

    // Check for reserved IP ranges
    const isReserved = parts[0] === 0 || parts[0] === 255;

    // Basic threat score based on IP characteristics
    let threatScore = 0;
    
    if (isPrivate) {
        threatScore = 10; // Private IPs are unusual in email headers
    } else if (isReserved) {
        threatScore = 50; // Reserved IPs are very suspicious
    }

    return {
        ip,
        isPrivate,
        isReserved,
        isPublic: !isPrivate && !isReserved,
        threatScore,
        checks: {
            privateIP: isPrivate,
            reservedIP: isReserved,
            publicIP: !isPrivate && !isReserved
        },
        note: 'Limited analysis without AbuseIPDB API key. Configure API key for comprehensive blacklist scanning.'
    };
}

function getThreatLevel(score: number): string {
    if (score >= 75) return 'critical';
    if (score >= 50) return 'high';
    if (score >= 30) return 'medium';
    if (score >= 15) return 'low';
    return 'safe';
}

function getRecommendation(score: number): string {
    if (score >= 75) {
        return 'BLOCK - IP has high abuse confidence score and is likely malicious';
    } else if (score >= 50) {
        return 'QUARANTINE - IP has moderate abuse reports, exercise extreme caution';
    } else if (score >= 30) {
        return 'REVIEW - IP has some abuse history, verify legitimacy';
    } else if (score >= 15) {
        return 'MONITOR - IP has minor concerns, standard security practices apply';
    }
    return 'ALLOW - IP appears clean with no significant abuse reports';
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
