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
        const { headers: emailHeaders } = await req.json();

        if (!emailHeaders || typeof emailHeaders !== 'string') {
            throw new Error('Email headers are required as a string');
        }

        // Parse email headers
        const parsedHeaders = parseEmailHeaders(emailHeaders);
        
        // Extract key information
        const analysis = {
            from: extractHeader(parsedHeaders, 'from'),
            to: extractHeader(parsedHeaders, 'to'),
            subject: extractHeader(parsedHeaders, 'subject'),
            returnPath: extractHeader(parsedHeaders, 'return-path'),
            replyTo: extractHeader(parsedHeaders, 'reply-to'),
            messageId: extractHeader(parsedHeaders, 'message-id'),
            date: extractHeader(parsedHeaders, 'date'),
            
            // Authentication results
            spf: extractAuthenticationResult(parsedHeaders, 'spf'),
            dkim: extractAuthenticationResult(parsedHeaders, 'dkim'),
            dmarc: extractAuthenticationResult(parsedHeaders, 'dmarc'),
            
            // Routing information
            receivedHops: extractReceivedHops(emailHeaders),
            
            // Anomaly detection
            anomalies: detectAnomalies(parsedHeaders),
            
            // Threat score
            threatScore: calculateThreatScore(parsedHeaders),
        };

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Email Header Analyzer', 'header-analysis', {
            threatScore: analysis.threatScore,
            anomalyCount: analysis.anomalies.length
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: analysis }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Email header analysis error:', error);

        const errorResponse = {
            error: {
                code: 'HEADER_ANALYSIS_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function parseEmailHeaders(headersText: string): Map<string, string> {
    const headers = new Map<string, string>();
    const lines = headersText.split('\n');
    let currentHeader = '';
    let currentValue = '';

    for (const line of lines) {
        // Check if this is a continuation line (starts with whitespace)
        if (line.match(/^\s/) && currentHeader) {
            currentValue += ' ' + line.trim();
        } else {
            // Save previous header
            if (currentHeader) {
                headers.set(currentHeader.toLowerCase(), currentValue.trim());
            }
            
            // Parse new header
            const colonIndex = line.indexOf(':');
            if (colonIndex > 0) {
                currentHeader = line.substring(0, colonIndex).trim();
                currentValue = line.substring(colonIndex + 1).trim();
            }
        }
    }

    // Save last header
    if (currentHeader) {
        headers.set(currentHeader.toLowerCase(), currentValue.trim());
    }

    return headers;
}

function extractHeader(headers: Map<string, string>, key: string): string {
    return headers.get(key.toLowerCase()) || '';
}

function extractAuthenticationResult(headers: Map<string, string>, type: string): any {
    const authResults = headers.get('authentication-results') || '';
    const receivedSpf = headers.get('received-spf') || '';
    
    let result = { status: 'none', details: '' };

    if (type === 'spf') {
        // Check Received-SPF header first
        if (receivedSpf) {
            const spfMatch = receivedSpf.match(/^(pass|fail|softfail|neutral|none|temperror|permerror)/i);
            if (spfMatch) {
                result.status = spfMatch[1].toLowerCase();
                result.details = receivedSpf;
            }
        }
        // Also check authentication-results
        const spfAuthMatch = authResults.match(/spf=([^\s;]+)/i);
        if (spfAuthMatch && result.status === 'none') {
            result.status = spfAuthMatch[1].toLowerCase();
        }
    } else if (type === 'dkim') {
        const dkimMatch = authResults.match(/dkim=([^\s;]+)/i);
        if (dkimMatch) {
            result.status = dkimMatch[1].toLowerCase();
            result.details = authResults;
        }
    } else if (type === 'dmarc') {
        const dmarcMatch = authResults.match(/dmarc=([^\s;]+)/i);
        if (dmarcMatch) {
            result.status = dmarcMatch[1].toLowerCase();
            result.details = authResults;
        }
    }

    return result;
}

function extractReceivedHops(headersText: string): any[] {
    const receivedRegex = /^Received:\s*(.+?)(?=\r?\n(?![\s]))/gim;
    const hops: any[] = [];
    let match;

    while ((match = receivedRegex.exec(headersText)) !== null) {
        const hopText = match[1];
        
        // Extract IP addresses
        const ipMatch = hopText.match(/\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]/);
        const ip = ipMatch ? ipMatch[1] : '';
        
        // Extract timestamp
        const dateMatch = hopText.match(/;\s*(.+)$/);
        const timestamp = dateMatch ? dateMatch[1].trim() : '';
        
        // Extract server info
        const fromMatch = hopText.match(/from\s+([^\s]+)/i);
        const server = fromMatch ? fromMatch[1] : '';

        hops.push({
            server,
            ip,
            timestamp,
            rawText: hopText
        });
    }

    return hops.reverse(); // Reverse to show chronological order
}

function detectAnomalies(headers: Map<string, string>): string[] {
    const anomalies: string[] = [];

    const from = headers.get('from') || '';
    const returnPath = headers.get('return-path') || '';
    const replyTo = headers.get('reply-to') || '';

    // Check for mismatched From and Return-Path domains
    if (from && returnPath) {
        const fromDomain = extractDomain(from);
        const returnDomain = extractDomain(returnPath);
        if (fromDomain && returnDomain && fromDomain !== returnDomain) {
            anomalies.push(`From domain (${fromDomain}) differs from Return-Path domain (${returnDomain})`);
        }
    }

    // Check for suspicious Reply-To
    if (replyTo && from) {
        const fromDomain = extractDomain(from);
        const replyDomain = extractDomain(replyTo);
        if (fromDomain && replyDomain && fromDomain !== replyDomain) {
            anomalies.push(`Reply-To domain (${replyDomain}) differs from From domain (${fromDomain})`);
        }
    }

    // Check for missing Message-ID
    if (!headers.get('message-id')) {
        anomalies.push('Missing Message-ID header (suspicious)');
    }

    // Check for suspicious X-headers that might indicate spoofing
    const xMailer = headers.get('x-mailer') || '';
    if (xMailer && xMailer.includes('phpmailer')) {
        anomalies.push('Email sent via PHPMailer (common in phishing)');
    }

    // Check for date anomalies
    const dateHeader = headers.get('date');
    if (dateHeader) {
        const emailDate = new Date(dateHeader);
        const now = new Date();
        const daysDiff = Math.abs((now.getTime() - emailDate.getTime()) / (1000 * 60 * 60 * 24));
        if (daysDiff > 365) {
            anomalies.push('Email date is more than 1 year old or in the future');
        }
    }

    return anomalies;
}

function extractDomain(email: string): string {
    const match = email.match(/@([^\s>]+)/);
    return match ? match[1].toLowerCase() : '';
}

function calculateThreatScore(headers: Map<string, string>): number {
    let score = 0;

    // Base score starts at 0 (safe)
    
    // Check SPF
    const spfResult = extractAuthenticationResult(headers, 'spf');
    if (spfResult.status === 'fail' || spfResult.status === 'softfail') {
        score += 25;
    } else if (spfResult.status === 'none' || spfResult.status === 'neutral') {
        score += 10;
    }

    // Check DKIM
    const dkimResult = extractAuthenticationResult(headers, 'dkim');
    if (dkimResult.status === 'fail') {
        score += 20;
    } else if (dkimResult.status === 'none') {
        score += 10;
    }

    // Check DMARC
    const dmarcResult = extractAuthenticationResult(headers, 'dmarc');
    if (dmarcResult.status === 'fail') {
        score += 25;
    } else if (dmarcResult.status === 'none') {
        score += 15;
    }

    // Anomalies add to score
    const anomalies = detectAnomalies(headers);
    score += anomalies.length * 10;

    // Cap at 100
    return Math.min(score, 100);
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
