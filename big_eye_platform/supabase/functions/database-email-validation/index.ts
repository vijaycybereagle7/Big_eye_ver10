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
        const { email, verify_syntax = true, verify_mx_record = true, check_disposable = true } = await req.json();

        if (!email) {
            throw new Error('Email address is required');
        }

        // Email validation logic using Big Eye Security Database
        const validation = await validateEmailWithBigEyeDB(email, verify_syntax, verify_mx_record, check_disposable);

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Big Eye Database Analysis', 'email-validation', {
            email,
            isValid: validation.is_valid,
            confidence: validation.confidence_score,
            threats: validation.threats?.length || 0
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: validation }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Database email validation error:', error);

        const errorResponse = {
            error: {
                code: 'DATABASE_EMAIL_VALIDATION_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function validateEmailWithBigEyeDB(email: string, verifySyntax: boolean, verifyMxRecord: boolean, checkDisposable: boolean) {
    // Mock validation using Big Eye Security Database logic
    // In production, this would call the actual Big Eye Security Database API
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValidFormat = emailRegex.test(email);
    
    if (!isValidFormat && verifySyntax) {
        return {
            is_valid: false,
            email: email,
            validation_details: {
                syntax_valid: false,
                domain_valid: false,
                mx_record_valid: false,
                disposable: false,
                reputation_score: 0
            },
            confidence_score: 0,
            threats: [],
            recommendations: ['Invalid email format', 'Please check the email address syntax']
        };
    }

    // Extract domain from email
    const domain = email.split('@')[1]?.toLowerCase() || '';
    
    // Mock domain validation
    const domainValid = domain.length > 0 && domain.includes('.');
    
    // Mock MX record check
    const mxRecordValid = domainValid; // Simplified for demo
    
    // Mock disposable email check
    const disposableDomains = ['10minutemail.com', 'guerrillamail.com', 'mailinator.com', 'tempmail.com'];
    const isDisposable = disposableDomains.includes(domain);
    
    // Mock threat detection
    const threats = [];
    if (isDisposable) {
        threats.push({
            type: 'disposable_email',
            severity: 'medium',
            description: 'Disposable email address detected',
            source: 'Big Eye Security Database'
        });
    }
    
    // Calculate reputation score (0-100)
    let reputationScore = 100;
    if (!isValidFormat) reputationScore -= 50;
    if (!domainValid) reputationScore -= 30;
    if (!mxRecordValid) reputationScore -= 20;
    if (isDisposable) reputationScore -= 40;
    
    // Calculate overall confidence
    const confidenceScore = reputationScore / 100;
    
    return {
        is_valid: reputationScore >= 70,
        email: email,
        validation_details: {
            syntax_valid: isValidFormat,
            domain_valid: domainValid,
            mx_record_valid: mxRecordValid,
            disposable: isDisposable,
            reputation_score: reputationScore
        },
        confidence_score: confidenceScore,
        threats: threats,
        recommendations: generateRecommendations(isValidFormat, domainValid, mxRecordValid, isDisposable, reputationScore)
    };
}

function generateRecommendations(syntaxValid: boolean, domainValid: boolean, mxRecordValid: boolean, isDisposable: boolean, reputationScore: number): string[] {
    const recommendations = [];
    
    if (!syntaxValid) {
        recommendations.push('Fix email syntax - check for missing @ symbol or invalid characters');
    }
    
    if (!domainValid) {
        recommendations.push('Domain appears invalid - verify the domain name');
    }
    
    if (!mxRecordValid) {
        recommendations.push('Domain MX records not found - email may not be deliverable');
    }
    
    if (isDisposable) {
        recommendations.push('Avoid disposable email addresses for important communications');
    }
    
    if (reputationScore < 50) {
        recommendations.push('Low reputation score detected - verify sender authenticity');
    }
    
    if (recommendations.length === 0) {
        recommendations.push('Email validation passed successfully');
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