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
        const { domain } = await req.json();

        if (!domain || typeof domain !== 'string') {
            throw new Error('Domain is required');
        }

        const cleanDomain = domain.toLowerCase().trim().replace(/^https?:\/\//, '').replace(/\/.*$/, '');

        // Parallel API calls for comprehensive domain analysis
        const [dnsInfo, sslInfo, domainAge] = await Promise.allSettled([
            getDNSInfo(cleanDomain),
            getSSLInfo(cleanDomain),
            getDomainAge(cleanDomain)
        ]);

        const result = {
            domain: cleanDomain,
            dns: dnsInfo.status === 'fulfilled' ? dnsInfo.value : { error: dnsInfo.reason?.message },
            ssl: sslInfo.status === 'fulfilled' ? sslInfo.value : { error: sslInfo.reason?.message },
            domainInfo: domainAge.status === 'fulfilled' ? domainAge.value : { error: domainAge.reason?.message },
            overallThreatScore: 0,
            riskLevel: 'unknown',
            recommendations: []
        };

        // Calculate overall threat score
        result.overallThreatScore = calculateOverallThreatScore(result);
        result.riskLevel = getThreatLevel(result.overallThreatScore);
        result.recommendations = generateRecommendations(result);

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Domain Checker', 'domain-analysis', {
            domain: cleanDomain,
            threatScore: result.overallThreatScore,
            riskLevel: result.riskLevel
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Domain check error:', error);

        const errorResponse = {
            error: {
                code: 'DOMAIN_CHECK_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function getDNSInfo(domain: string): Promise<any> {
    try {
        // Use Cloudflare DNS-over-HTTPS for DNS queries
        const dnsTypes = ['A', 'MX', 'TXT', 'NS'];
        const results: any = {};

        for (const type of dnsTypes) {
            try {
                const response = await fetch(`https://cloudflare-dns.com/dns-query?name=${domain}&type=${type}`, {
                    headers: { 'Accept': 'application/dns-json' },
                    signal: AbortSignal.timeout(5000)
                });

                if (response.ok) {
                    const data = await response.json();
                    results[type] = data.Answer || [];
                } else {
                    results[type] = [];
                }
            } catch (error) {
                results[type] = [];
            }
        }

        // Check for SPF, DKIM, DMARC in TXT records
        const txtRecords = results.TXT || [];
        const spf = txtRecords.find((r: any) => r.data?.includes('v=spf1'));
        const dmarc = txtRecords.find((r: any) => r.data?.includes('v=DMARC1'));

        return {
            hasARecord: results.A.length > 0,
            hasMXRecord: results.MX.length > 0,
            hasNSRecord: results.NS.length > 0,
            hasSPF: !!spf,
            hasDMARC: !!dmarc,
            aRecords: results.A.map((r: any) => r.data),
            mxRecords: results.MX.map((r: any) => r.data),
            nsRecords: results.NS.map((r: any) => r.data),
            txtRecords: results.TXT.map((r: any) => r.data),
            spfRecord: spf?.data || null,
            dmarcRecord: dmarc?.data || null,
            validConfiguration: results.A.length > 0 && results.MX.length > 0
        };
    } catch (error) {
        throw new Error(`DNS lookup failed: ${error.message}`);
    }
}

async function getSSLInfo(domain: string): Promise<any> {
    try {
        // Try to connect and get SSL certificate info
        const response = await fetch(`https://${domain}`, {
            method: 'HEAD',
            signal: AbortSignal.timeout(5000)
        });

        // Basic SSL check - if HTTPS works, SSL is valid
        const hasSSL = response.ok || response.status < 500;

        // Try to get more detailed SSL info using SSL Labs-like checks
        // For now, we'll do basic HTTPS connectivity check
        return {
            hasSSL,
            httpsEnabled: hasSSL,
            message: hasSSL ? 'HTTPS is enabled' : 'HTTPS connection failed',
            recommendation: hasSSL ? 'SSL/TLS is configured' : 'SSL/TLS is not properly configured'
        };
    } catch (error) {
        return {
            hasSSL: false,
            httpsEnabled: false,
            message: 'HTTPS not available or misconfigured',
            error: error.message
        };
    }
}

async function getDomainAge(domain: string): Promise<any> {
    try {
        // Use free WHOIS API
        const response = await fetch(`https://whoisjson.com/api/v1/whois?domain=${encodeURIComponent(domain)}`, {
            headers: { 'Accept': 'application/json' },
            signal: AbortSignal.timeout(5000)
        });

        if (!response.ok) {
            throw new Error('WHOIS lookup failed');
        }

        const whoisData = await response.json();
        const createdDate = parseDateSafely(whoisData.created_date || whoisData.created);
        
        if (!createdDate) {
            return {
                ageInDays: null,
                registrar: whoisData.registrar || 'Unknown',
                createdDate: null
            };
        }

        const now = new Date();
        const ageInDays = Math.floor((now.getTime() - createdDate.getTime()) / (1000 * 60 * 60 * 24));

        return {
            ageInDays,
            ageInYears: (ageInDays / 365).toFixed(1),
            registrar: whoisData.registrar || 'Unknown',
            createdDate: createdDate.toISOString()
        };
    } catch (error) {
        return {
            ageInDays: null,
            error: error.message
        };
    }
}

function parseDateSafely(dateString: any): Date | null {
    if (!dateString) return null;
    
    try {
        if (typeof dateString === 'string') {
            const isoDate = new Date(dateString);
            if (!isNaN(isoDate.getTime())) {
                return isoDate;
            }
            
            const match = dateString.match(/(\d{4})-(\d{2})-(\d{2})/);
            if (match) {
                return new Date(`${match[1]}-${match[2]}-${match[3]}`);
            }
        }
        
        return null;
    } catch (error) {
        return null;
    }
}

function calculateOverallThreatScore(result: any): number {
    let score = 0;

    // DNS configuration issues (max 30 points)
    if (result.dns && !result.dns.error) {
        if (!result.dns.hasSPF) score += 10;
        if (!result.dns.hasDMARC) score += 10;
        if (!result.dns.hasMXRecord) score += 5;
        if (!result.dns.hasARecord) score += 5;
    } else {
        score += 20; // DNS lookup failed = suspicious
    }

    // SSL/TLS issues (max 20 points)
    if (result.ssl && !result.ssl.error) {
        if (!result.ssl.hasSSL) score += 20;
    } else {
        score += 15; // SSL check failed
    }

    // Domain age issues (max 50 points)
    if (result.domainInfo && !result.domainInfo.error) {
        const ageInDays = result.domainInfo.ageInDays;
        if (ageInDays !== null) {
            if (ageInDays < 30) score += 50;
            else if (ageInDays < 90) score += 35;
            else if (ageInDays < 180) score += 20;
            else if (ageInDays < 365) score += 10;
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

function generateRecommendations(result: any): string[] {
    const recommendations: string[] = [];

    if (result.dns && !result.dns.error) {
        if (!result.dns.hasSPF) {
            recommendations.push('Domain lacks SPF record - email authentication is incomplete');
        }
        if (!result.dns.hasDMARC) {
            recommendations.push('Domain lacks DMARC policy - vulnerable to email spoofing');
        }
        if (!result.dns.hasMXRecord) {
            recommendations.push('No MX records found - domain may not be configured for email');
        }
    }

    if (result.ssl && !result.ssl.hasSSL) {
        recommendations.push('HTTPS/SSL not properly configured - increases phishing risk');
    }

    if (result.domainInfo && result.domainInfo.ageInDays !== null) {
        const age = result.domainInfo.ageInDays;
        if (age < 30) {
            recommendations.push('Domain is less than 30 days old - HIGH RISK of phishing');
        } else if (age < 90) {
            recommendations.push('Domain is less than 90 days old - exercise caution');
        }
    }

    if (recommendations.length === 0) {
        recommendations.push('Domain appears to have standard security configurations');
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
