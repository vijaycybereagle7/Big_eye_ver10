const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Credentials': 'false'
};

Deno.serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const { ip } = await req.json();

        if (!ip) {
            throw new Error('IP address is required');
        }

        // Implement automatic failover chain
        let result = null;
        let usedProvider = '';
        let error = null;

        // Primary: ipapi.co (30K/month, existing provider)
        try {
            result = await fetchFromIPAPICo(ip);
            usedProvider = 'ipapi.co';
        } catch (err) {
            console.warn('ipapi.co failed, trying FreeIPAPI:', err.message);
            error = err.message;

            // Fallback 1: FreeIPAPI (60 req/min, no key needed)
            try {
                result = await fetchFromFreeIPAPI(ip);
                usedProvider = 'FreeIPAPI';
            } catch (err2) {
                console.warn('FreeIPAPI failed, trying IP-API:', err2.message);
                
                // Fallback 2: IP-API (45 req/min, adds VPN/proxy detection)
                try {
                    result = await fetchFromIPAPI2(ip);
                    usedProvider = 'IP-API';
                } catch (err3) {
                    throw new Error(`All IP intelligence providers failed. Last error: ${err3.message}`);
                }
            }
        }

        // Add metadata
        result.provider = usedProvider;
        result.timestamp = new Date().toISOString();
        result.ip = ip;

        // Track analytics (non-blocking)
        trackAnalytics(req, 'IP Intelligence', 'ip-reputation-check', {
            provider: usedProvider,
            country: result.country,
            isVPN: result.isVPN || false,
            isProxy: result.isProxy || false
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('IP reputation check error:', error);

        const errorResponse = {
            error: {
                code: 'IP_REPUTATION_CHECK_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function fetchFromIPAPICo(ip: string): Promise<any> {
    const response = await fetch(`https://ipapi.co/${ip}/json/`);
    
    if (!response.ok) {
        throw new Error(`ipapi.co returned ${response.status}`);
    }

    const data = await response.json();
    
    if (data.error) {
        throw new Error(data.reason || 'ipapi.co error');
    }

    return {
        ip: data.ip,
        city: data.city,
        region: data.region,
        country: data.country_name,
        countryCode: data.country_code,
        latitude: data.latitude,
        longitude: data.longitude,
        timezone: data.timezone,
        isp: data.org,
        asn: data.asn,
        postal: data.postal,
        isVPN: false, // ipapi.co doesn't provide VPN detection
        isProxy: false
    };
}

async function fetchFromFreeIPAPI(ip: string): Promise<any> {
    const response = await fetch(`https://freeipapi.com/api/json/${ip}`);
    
    if (!response.ok) {
        throw new Error(`FreeIPAPI returned ${response.status}`);
    }

    const data = await response.json();

    return {
        ip: data.ipAddress,
        city: data.cityName,
        region: data.regionName,
        country: data.countryName,
        countryCode: data.countryCode,
        latitude: data.latitude,
        longitude: data.longitude,
        timezone: data.timeZone,
        isp: data.isProxy ? 'Proxy detected' : 'Unknown',
        asn: null,
        postal: data.zipCode,
        isVPN: false,
        isProxy: data.isProxy || false
    };
}

async function fetchFromIPAPI2(ip: string): Promise<any> {
    const response = await fetch(`http://ip-api.com/json/${ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,mobile,hosting,query`);
    
    if (!response.ok) {
        throw new Error(`IP-API returned ${response.status}`);
    }

    const data = await response.json();
    
    if (data.status === 'fail') {
        throw new Error(data.message || 'IP-API error');
    }

    return {
        ip: data.query,
        city: data.city,
        region: data.regionName,
        country: data.country,
        countryCode: data.countryCode,
        latitude: data.lat,
        longitude: data.lon,
        timezone: data.timezone,
        isp: data.isp,
        asn: data.as,
        postal: data.zip,
        isVPN: data.hosting || false, // Hosting flag often indicates VPN
        isProxy: data.proxy || false
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
