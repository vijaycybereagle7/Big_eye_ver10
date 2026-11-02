import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

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
        // Verify user is admin
        const authHeader = req.headers.get('Authorization');
        if (!authHeader) {
            return new Response(JSON.stringify({ error: 'Unauthorized - No auth header' }), {
                status: 401,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        const supabase = createClient(
            Deno.env.get('SUPABASE_URL')!,
            Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
        );

        const token = authHeader.replace('Bearer ', '');
        const { data: { user }, error: authError } = await supabase.auth.getUser(token);

        if (authError || !user) {
            return new Response(JSON.stringify({ error: 'Unauthorized - Invalid token' }), {
                status: 401,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Check if user is admin
        const { data: userData, error: userError } = await supabase
            .from('users')
            .select('is_admin')
            .eq('id', user.id)
            .single();

        if (userError || !userData?.is_admin) {
            return new Response(JSON.stringify({ error: 'Admin access required' }), {
                status: 403,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Fetch API usage stats (last 7 days for context)
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        const sevenDaysAgoStr = sevenDaysAgo.toISOString().split('T')[0];

        const { data: usage, error } = await supabase
            .from('api_usage_tracking')
            .select('*')
            .gte('date', sevenDaysAgoStr)
            .order('date', { ascending: false });

        if (error) {
            return new Response(JSON.stringify({ error: error.message }), {
                status: 500,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Group by API name and get today's usage
        const today = new Date().toISOString().split('T')[0];
        const apiSummary = usage.reduce((acc: any, row: any) => {
            if (!acc[row.api_name]) {
                acc[row.api_name] = {
                    api_name: row.api_name,
                    reset_period: row.reset_period,
                    limit_total: row.limit_total,
                    today_usage: 0,
                    history: []
                };
            }
            
            if (row.date === today) {
                acc[row.api_name].today_usage = row.request_count;
            }
            
            acc[row.api_name].history.push({
                date: row.date,
                request_count: row.request_count
            });
            
            return acc;
        }, {});

        return new Response(JSON.stringify({ 
            usage: Object.values(apiSummary),
            raw_data: usage 
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Get API usage error:', error);

        const errorResponse = {
            error: {
                code: 'GET_API_USAGE_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
