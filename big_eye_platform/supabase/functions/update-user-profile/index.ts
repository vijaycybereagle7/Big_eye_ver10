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
        const { ipAddress, deviceInfo, deviceName, browser, os, location } = await req.json();

        // Get user from auth header
        const authHeader = req.headers.get('authorization');
        if (!authHeader) {
            throw new Error('No authorization header');
        }

        const token = authHeader.replace('Bearer ', '');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase configuration missing');
        }

        // Verify token and get user
        const userResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'apikey': serviceRoleKey
            }
        });

        if (!userResponse.ok) {
            throw new Error('Invalid token or unauthorized');
        }

        const userData = await userResponse.json();
        const userId = userData.id;

        // Prepare update data
        const updateData: any = {
            last_login: new Date().toISOString()
        };

        if (ipAddress) updateData.ip_address = ipAddress;
        if (deviceInfo) updateData.device_info = deviceInfo;
        if (deviceName) updateData.device_name = deviceName;
        if (browser) updateData.browser = browser;
        if (os) updateData.os = os;
        if (location) updateData.location = location;

        // Increment login count
        const currentUserResponse = await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${userId}&select=login_count`, {
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey
            }
        });

        if (currentUserResponse.ok) {
            const currentUserData = await currentUserResponse.json();
            if (currentUserData && currentUserData.length > 0) {
                updateData.login_count = (currentUserData[0].login_count || 0) + 1;
            }
        }

        // Update user profile
        const updateResponse = await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${userId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify(updateData)
        });

        if (!updateResponse.ok) {
            const errorText = await updateResponse.text();
            throw new Error(`Profile update failed: ${errorText}`);
        }

        const updatedProfile = await updateResponse.json();

        return new Response(JSON.stringify({ 
            data: { 
                success: true, 
                profile: updatedProfile[0] || null 
            } 
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Update profile error:', error);

        const errorResponse = {
            error: {
                code: 'PROFILE_UPDATE_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
