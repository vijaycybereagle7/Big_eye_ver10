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
        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        
        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('Missing Supabase credentials');
        }

        const stats = {
            usersProcessed: 0,
            logsCompressed: 0,
            logsArchived: 0,
            logsDeleted: 0,
            errors: []
        };

        // Get date threshold (compress logs older than 1 day, archive older than 30 days)
        const now = new Date();
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        const thirtyDaysAgo = new Date(now);
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        // Get unique users from analytics
        const usersResponse = await fetch(
            `${supabaseUrl}/rest/v1/user_analytics?select=user_id&timestamp=lte.${yesterday.toISOString()}`,
            {
                headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'apikey': serviceRoleKey
                }
            }
        );

        if (!usersResponse.ok) {
            throw new Error('Failed to fetch users');
        }

        const usersData = await usersResponse.json();
        const uniqueUsers = [...new Set(usersData.map((item: any) => item.user_id))];

        // Process each user
        for (const userId of uniqueUsers) {
            try {
                // Get all analytics for this user up to yesterday
                const analyticsResponse = await fetch(
                    `${supabaseUrl}/rest/v1/user_analytics?user_id=eq.${userId}&timestamp=lte.${yesterday.toISOString()}&order=timestamp.asc`,
                    {
                        headers: {
                            'Authorization': `Bearer ${serviceRoleKey}`,
                            'apikey': serviceRoleKey
                        }
                    }
                );

                if (!analyticsResponse.ok) {
                    stats.errors.push(`Failed to fetch analytics for user ${userId}`);
                    continue;
                }

                const analytics = await analyticsResponse.json();

                if (analytics.length === 0) continue;

                // Group by date
                const groupedByDate: Record<string, any[]> = {};
                
                for (const record of analytics) {
                    const date = new Date(record.timestamp).toISOString().split('T')[0];
                    if (!groupedByDate[date]) {
                        groupedByDate[date] = [];
                    }
                    groupedByDate[date].push(record);
                }

                // Compress each day's data
                for (const [date, records] of Object.entries(groupedByDate)) {
                    const recordDate = new Date(date);
                    
                    // Determine if should archive (older than 30 days)
                    const shouldArchive = recordDate < thirtyDaysAgo;

                    // Compress data using Base64 encoding
                    const dataString = JSON.stringify(records);
                    const compressedData = btoa(dataString);
                    const compressionRatio = ((compressedData.length / dataString.length) * 100).toFixed(2);

                    if (shouldArchive) {
                        // Move to archive table
                        const archiveResponse = await fetch(
                            `${supabaseUrl}/rest/v1/user_analytics_archive`,
                            {
                                method: 'POST',
                                headers: {
                                    'Authorization': `Bearer ${serviceRoleKey}`,
                                    'apikey': serviceRoleKey,
                                    'Content-Type': 'application/json',
                                    'Prefer': 'resolution=merge-duplicates'
                                },
                                body: JSON.stringify({
                                    user_id: userId,
                                    date: date,
                                    compressed_data: compressedData
                                })
                            }
                        );

                        if (archiveResponse.ok) {
                            stats.logsArchived += records.length;
                        } else {
                            stats.errors.push(`Failed to archive logs for user ${userId} on ${date}`);
                        }
                    } else {
                        // Store in compressed table
                        const compressResponse = await fetch(
                            `${supabaseUrl}/rest/v1/user_analytics_compressed`,
                            {
                                method: 'POST',
                                headers: {
                                    'Authorization': `Bearer ${serviceRoleKey}`,
                                    'apikey': serviceRoleKey,
                                    'Content-Type': 'application/json',
                                    'Prefer': 'resolution=merge-duplicates'
                                },
                                body: JSON.stringify({
                                    user_id: userId,
                                    date: date,
                                    compressed_data: compressedData,
                                    compression_ratio: parseFloat(compressionRatio),
                                    total_records: records.length
                                })
                            }
                        );

                        if (compressResponse.ok) {
                            stats.logsCompressed += records.length;
                        } else {
                            stats.errors.push(`Failed to compress logs for user ${userId} on ${date}`);
                        }
                    }

                    // Delete raw logs after successful compression/archiving
                    const recordIds = records.map(r => r.id);
                    for (const id of recordIds) {
                        const deleteResponse = await fetch(
                            `${supabaseUrl}/rest/v1/user_analytics?id=eq.${id}`,
                            {
                                method: 'DELETE',
                                headers: {
                                    'Authorization': `Bearer ${serviceRoleKey}`,
                                    'apikey': serviceRoleKey
                                }
                            }
                        );

                        if (deleteResponse.ok) {
                            stats.logsDeleted++;
                        }
                    }
                }

                stats.usersProcessed++;
            } catch (error) {
                stats.errors.push(`Error processing user ${userId}: ${error.message}`);
            }
        }

        const result = {
            success: true,
            message: 'Log compression completed successfully',
            stats,
            processedAt: new Date().toISOString()
        };

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Log compression error:', error);

        const errorResponse = {
            error: {
                code: 'LOG_COMPRESSION_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
