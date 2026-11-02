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

        // Try multiple free WHOIS/RDAP APIs in sequence
        let whoisData = null;
        let source = '';

        // Try RDAP (free, official protocol)
        try {
            const response = await fetch(`https://rdap.org/domain/${encodeURIComponent(cleanDomain)}`, {
                headers: { 'Accept': 'application/json' },
                signal: AbortSignal.timeout(8000)
            });
            
            if (response.ok) {
                const data = await response.json();
                // Transform RDAP format to our format
                const events = data.events || [];
                const registrationEvent = events.find((e: any) => e.eventAction === 'registration');
                const lastChangedEvent = events.find((e: any) => e.eventAction === 'last changed');
                const expirationEvent = events.find((e: any) => e.eventAction === 'expiration');
                
                whoisData = {
                    created_date: registrationEvent?.eventDate || null,
                    updated_date: lastChangedEvent?.eventDate || null,
                    expires_date: expirationEvent?.eventDate || null,
                    registrar: data.entities?.find((e: any) => e.roles?.includes('registrar'))?.vcardArray?.[1]?.find((v: any) => v[0] === 'fn')?.[3] || null,
                    domain_name: cleanDomain
                };
                source = 'rdap.org';
            }
        } catch (error) {
            console.warn('rdap.org failed:', error.message);
        }

        // Fallback to rdap.net (another RDAP service)
        if (!whoisData) {
            try {
                const response = await fetch(`https://rdap.net/domain/${encodeURIComponent(cleanDomain)}`, {
                    headers: { 'Accept': 'application/json' },
                    signal: AbortSignal.timeout(8000)
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const events = data.events || [];
                    const registrationEvent = events.find((e: any) => e.eventAction === 'registration');
                    const lastChangedEvent = events.find((e: any) => e.eventAction === 'last changed');
                    const expirationEvent = events.find((e: any) => e.eventAction === 'expiration');
                    
                    whoisData = {
                        created_date: registrationEvent?.eventDate || null,
                        updated_date: lastChangedEvent?.eventDate || null,
                        expires_date: expirationEvent?.eventDate || null,
                        registrar: data.entities?.find((e: any) => e.roles?.includes('registrar'))?.vcardArray?.[1]?.find((v: any) => v[0] === 'fn')?.[3] || null,
                        domain_name: cleanDomain
                    };
                    source = 'rdap.net';
                }
            } catch (error) {
                console.warn('rdap.net failed:', error.message);
            }
        }

        // Fallback to local estimate for well-known domains
        if (!whoisData) {
            const estimatedAge = estimateDomainAge(cleanDomain);
            if (estimatedAge) {
                whoisData = {
                    created_date: estimatedAge.createdDate,
                    updated_date: null,
                    expires_date: null,
                    registrar: 'Estimated',
                    domain_name: cleanDomain
                };
                source = 'estimated (well-known domain)';
            }
        }

        if (!whoisData) {
            // Return partial result with warning instead of error
            const partialResult = {
                domain: cleanDomain,
                createdDate: null,
                updatedDate: null,
                expiresDate: null,
                ageInDays: null,
                ageInYears: null,
                ageDescription: 'Unable to determine',
                registrar: 'Unknown',
                riskLevel: 'medium',
                riskReason: 'Domain age could not be verified - exercise caution',
                threatScore: 50,
                dataSource: 'unavailable',
                warning: 'WHOIS/RDAP data unavailable. This may indicate: 1) Privacy protection enabled, 2) New/unregistered domain, 3) API rate limiting. Recommend additional verification.',
                rawData: null
            };

            return new Response(JSON.stringify({ data: partialResult }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Parse dates
        const createdDate = parseDateSafely(whoisData.created_date || whoisData.created);
        const updatedDate = parseDateSafely(whoisData.updated_date || whoisData.updated);
        const expiresDate = parseDateSafely(whoisData.expires_date || whoisData.expires);

        const now = new Date();
        const ageInDays = createdDate ? Math.floor((now.getTime() - createdDate.getTime()) / (1000 * 60 * 60 * 24)) : null;
        const ageInYears = ageInDays ? (ageInDays / 365).toFixed(1) : null;

        // Risk assessment based on age
        let riskLevel = 'unknown';
        let riskReason = '';
        
        if (ageInDays !== null) {
            if (ageInDays < 30) {
                riskLevel = 'critical';
                riskReason = 'Domain created less than 30 days ago (very suspicious)';
            } else if (ageInDays < 90) {
                riskLevel = 'high';
                riskReason = 'Domain created less than 90 days ago (suspicious)';
            } else if (ageInDays < 180) {
                riskLevel = 'medium';
                riskReason = 'Domain created less than 6 months ago (watch carefully)';
            } else if (ageInDays < 365) {
                riskLevel = 'low';
                riskReason = 'Domain created less than 1 year ago';
            } else {
                riskLevel = 'safe';
                riskReason = 'Domain is over 1 year old (established)';
            }
        }

        const result = {
            domain: cleanDomain,
            createdDate: createdDate ? createdDate.toISOString() : null,
            updatedDate: updatedDate ? updatedDate.toISOString() : null,
            expiresDate: expiresDate ? expiresDate.toISOString() : null,
            ageInDays,
            ageInYears,
            ageDescription: formatAgeDescription(ageInDays),
            registrar: whoisData.registrar || 'Unknown',
            riskLevel,
            riskReason,
            threatScore: calculateAgeBasedThreatScore(ageInDays),
            dataSource: source,
            rawData: whoisData
        };

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Domain Age Tracker', 'domain-age-check', {
            domain: cleanDomain,
            ageInDays,
            riskLevel,
            threatScore: result.threatScore
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Domain age check error:', error);

        const errorResponse = {
            error: {
                code: 'DOMAIN_AGE_CHECK_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function parseDateSafely(dateString: any): Date | null {
    if (!dateString) return null;
    
    try {
        // Handle various date formats
        if (typeof dateString === 'string') {
            // Try ISO format first
            const isoDate = new Date(dateString);
            if (!isNaN(isoDate.getTime())) {
                return isoDate;
            }
            
            // Try common WHOIS formats (e.g., "2023-01-15T10:30:00Z" or "2023-01-15")
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

function formatAgeDescription(ageInDays: number | null): string {
    if (ageInDays === null) return 'Unknown';
    
    if (ageInDays < 1) return 'Less than 1 day old';
    if (ageInDays === 1) return '1 day old';
    if (ageInDays < 30) return `${ageInDays} days old`;
    if (ageInDays < 365) {
        const months = Math.floor(ageInDays / 30);
        return `${months} ${months === 1 ? 'month' : 'months'} old`;
    }
    
    const years = Math.floor(ageInDays / 365);
    const remainingMonths = Math.floor((ageInDays % 365) / 30);
    
    if (remainingMonths === 0) {
        return `${years} ${years === 1 ? 'year' : 'years'} old`;
    }
    
    return `${years} ${years === 1 ? 'year' : 'years'}, ${remainingMonths} ${remainingMonths === 1 ? 'month' : 'months'} old`;
}

function calculateAgeBasedThreatScore(ageInDays: number | null): number {
    if (ageInDays === null) return 50; // Unknown = medium risk
    
    if (ageInDays < 7) return 100;      // Less than 1 week = critical
    if (ageInDays < 30) return 90;      // Less than 1 month = very high
    if (ageInDays < 90) return 75;      // Less than 3 months = high
    if (ageInDays < 180) return 50;     // Less than 6 months = medium
    if (ageInDays < 365) return 30;     // Less than 1 year = low-medium
    if (ageInDays < 730) return 15;     // 1-2 years = low
    
    return 5;                            // Over 2 years = very low risk
}

// Estimate ages for well-known domains when WHOIS is unavailable
function estimateDomainAge(domain: string): { createdDate: string } | null {
    const wellKnownDomains: Record<string, string> = {
        'google.com': '1997-09-15',
        'facebook.com': '1997-03-29',
        'youtube.com': '2005-02-15',
        'amazon.com': '1994-11-01',
        'twitter.com': '2000-01-21',
        'instagram.com': '2004-06-08',
        'linkedin.com': '2002-05-05',
        'wikipedia.org': '2001-01-13',
        'reddit.com': '2005-06-23',
        'netflix.com': '1997-08-29',
        'microsoft.com': '1991-05-02',
        'apple.com': '1987-02-19',
        'yahoo.com': '1995-01-18',
        'ebay.com': '1995-09-04',
        'pinterest.com': '2009-11-26',
        'github.com': '2007-10-09',
        'stackoverflow.com': '2008-09-15',
        'paypal.com': '1999-12-17',
        'bbc.co.uk': '1994-12-05',
        'cnn.com': '1993-09-22',
        'nytimes.com': '1996-01-19',
        'imdb.com': '1996-03-05',
        'wordpress.com': '2005-08-08',
        'tumblr.com': '2007-02-19',
        'dropbox.com': '2007-10-05',
        'adobe.com': '1993-11-17',
        'walmart.com': '1995-07-03',
        'target.com': '1995-10-07',
        'bestbuy.com': '1995-05-02'
    };

    const createdDate = wellKnownDomains[domain];
    if (createdDate) {
        return { createdDate: new Date(createdDate).toISOString() };
    }

    return null;
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
