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
        const { query_type, value, include_context = true, include_related = true, time_range_days = 30 } = await req.json();

        if (!query_type || !value) {
            throw new Error('Query type and value are required');
        }

        if (!['ip', 'domain', 'url', 'hash'].includes(query_type)) {
            throw new Error('Query type must be one of: ip, domain, url, hash');
        }

        // Threat intelligence query using Big Eye Security Database
        const threatData = await queryThreatIntelligenceBigEyeDB(query_type, value, include_context, include_related, time_range_days, req.headers.get('authorization'));

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Big Eye Database Analysis', 'threat-intelligence', {
            query_type,
            value,
            threats_found: threatData.threats?.length || 0,
            confidence: threatData.confidence_score
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: threatData }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Database threat intelligence error:', error);

        const errorResponse = {
            error: {
                code: 'DATABASE_THREAT_INTELLIGENCE_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function queryThreatIntelligenceBigEyeDB(queryType: string, value: string, includeContext: boolean, includeRelated: boolean, timeRangeDays: number, authHeader: string | null) {
    const normalized = value.trim().toLowerCase();
    const threats: any[] = [];
    const staticIndicators: string[] = [];

    // Static rules are intentionally labelled as indicators, not as proof of
    // maliciousness. Live provider results are added only when configured.
    if (queryType === 'domain' && /\.(tk|ml|ga|cf|gq|top|zip|mov)$/i.test(normalized)) {
        staticIndicators.push('high-risk or frequently abused TLD');
    }
    if ((queryType === 'domain' || queryType === 'url') && /(?:login|verify|secure|account|billing|suspended)/i.test(normalized)) {
        staticIndicators.push('credential-themed indicator');
    }
    if (queryType === 'url' && !normalized.startsWith('https://')) {
        staticIndicators.push('insecure URL scheme');
    }
    if (queryType === 'hash' && !/^[a-f0-9]{32,128}$/i.test(normalized)) {
        staticIndicators.push('hash format could not be validated');
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    let watchlistMatches: any[] = [];
    if (supabaseUrl && serviceRoleKey && authHeader) {
        try {
            const tokenResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
                headers: { Authorization: authHeader, apikey: serviceRoleKey }
            });
            if (tokenResponse.ok) {
                const user = await tokenResponse.json();
                const params = new URLSearchParams({
                    indicator_type: `eq.${queryType === 'ip' ? 'ip' : queryType}`,
                    indicator_value: `eq.${normalized}`,
                    is_active: 'eq.true',
                    user_id: `eq.${user.id}`,
                    select: '*'
                });
                const watchlistResponse = await fetch(`${supabaseUrl}/rest/v1/security_watchlist?${params}`, {
                    headers: { Authorization: `Bearer ${serviceRoleKey}`, apikey: serviceRoleKey }
                });
                if (watchlistResponse.ok) watchlistMatches = await watchlistResponse.json();
            }
        } catch (error) {
            console.warn('Watchlist lookup unavailable:', error);
        }
    }

    for (const item of watchlistMatches) {
        threats.push({
            id: item.id,
            type: 'watchlist_match',
            category: item.indicator_type,
            severity: item.severity,
            description: item.label || 'Exact match in the authenticated user watchlist',
            source: 'Big Eye security watchlist',
            score: item.severity === 'critical' ? 100 : item.severity === 'high' ? 85 : item.severity === 'medium' ? 60 : 30,
            tags: ['watchlist', item.indicator_type],
            first_seen: item.created_at,
            last_seen: new Date().toISOString(),
            ...(includeContext ? { context: { exact_match: true, notes: item.notes || null } } : {})
        });
    }

    if (staticIndicators.length > 0 && threats.length === 0) {
        threats.push({
            id: `static_${normalized.slice(0, 24)}`,
            type: 'static_indicator',
            category: queryType,
            severity: 'low',
            description: staticIndicators.join('; '),
            source: 'Big Eye deterministic rules',
            score: 25,
            tags: ['static-analysis', ...staticIndicators]
        });
    }

    const confidence = threats.some((threat) => threat.type === 'watchlist_match') ? 0.95 : staticIndicators.length ? 0.35 : 0.15;
    return {
        indicator: value,
        indicator_type: queryType,
        threats,
        related_indicators: includeRelated ? [] : [],
        summary: {
            total_threats: threats.length,
            high_severity: threats.filter((threat) => threat.severity === 'high' || threat.severity === 'critical').length,
            medium_severity: threats.filter((threat) => threat.severity === 'medium').length,
            low_severity: threats.filter((threat) => threat.severity === 'low').length,
            average_confidence: confidence,
            time_range_days: timeRangeDays
        },
        confidence_score: confidence,
        data_sources: watchlistMatches.length ? ['security_watchlist'] : ['deterministic_static_rules'],
        last_updated: new Date().toISOString(),
        message: watchlistMatches.length ? 'Exact watchlist match found.' : 'No synchronized threat-feed match was found. Unknown is not the same as clean.'
    };
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
