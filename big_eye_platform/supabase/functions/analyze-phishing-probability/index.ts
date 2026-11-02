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
        const { email, subject, senderName, headers, body, domain } = await req.json();

        // Analyze multiple signals
        const analysis = {
            emailAnalysis: email ? analyzeEmailAddress(email) : null,
            subjectAnalysis: subject ? analyzeSubject(subject) : null,
            senderAnalysis: senderName ? analyzeSender(senderName, email) : null,
            headerAnalysis: headers ? analyzeHeaders(headers) : null,
            contentAnalysis: body ? analyzeContent(body) : null,
            domainAnalysis: domain ? analyzeDomain(domain) : null,
            
            // Overall phishing probability
            phishingScore: 0,
            confidence: 0,
            riskLevel: 'unknown',
            reasoning: [],
            redFlags: [],
            recommendation: ''
        };

        // Calculate composite score
        const scoreResult = calculateCompositeScore(analysis);
        analysis.phishingScore = scoreResult.score;
        analysis.confidence = scoreResult.confidence;
        analysis.riskLevel = getThreatLevel(scoreResult.score);
        analysis.reasoning = scoreResult.reasoning;
        analysis.redFlags = scoreResult.redFlags;
        analysis.recommendation = getRecommendation(scoreResult.score);

        // Track analytics (non-blocking)
        trackAnalytics(req, 'AI Phishing Detection', 'phishing-probability-analysis', {
            phishingScore: analysis.phishingScore,
            confidence: analysis.confidence,
            riskLevel: analysis.riskLevel,
            redFlagCount: analysis.redFlags.length
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: analysis }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Phishing analysis error:', error);

        const errorResponse = {
            error: {
                code: 'PHISHING_ANALYSIS_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function analyzeEmailAddress(email: string): any {
    const domain = email.split('@')[1]?.toLowerCase();
    const localPart = email.split('@')[0]?.toLowerCase();

    const suspiciousPatterns = [
        /noreply/i, /no-reply/i, /donotreply/i, /alert/i, /security/i,
        /verify/i, /confirm/i, /update/i, /billing/i, /payment/i,
        /support/i, /admin/i, /service/i, /account/i, /info/i
    ];

    const hasSuspiciousLocalPart = suspiciousPatterns.some(pattern =>
        pattern.test(localPart)
    );

    const hasNumbersAtEnd = /\d{3,}$/.test(localPart);
    const hasRandomChars = /[a-z]{2,}\d+[a-z]{2,}/i.test(localPart);

    return {
        email,
        domain,
        localPart,
        suspiciousLocalPart: hasSuspiciousLocalPart,
        hasNumbersAtEnd,
        hasRandomChars,
        threatScore: (hasSuspiciousLocalPart ? 15 : 0) + 
                     (hasNumbersAtEnd ? 10 : 0) + 
                     (hasRandomChars ? 15 : 0)
    };
}

function analyzeSubject(subject: string): any {
    const urgencyKeywords = [
        'urgent', 'immediate', 'action required', 'verify', 'confirm',
        'suspended', 'locked', 'expired', 'update required', 'security alert',
        'unusual activity', 'unauthorized', 'blocked', 'limited time',
        'act now', 'within 24 hours', 'final notice', 'last chance'
    ];

    const moneyKeywords = [
        'refund', 'payment', 'invoice', 'transaction', 'billing',
        'prize', 'winner', 'claim', 'reward', 'free', 'bonus',
        'credit', 'debit', 'account', 'bank', 'paypal', 'transfer'
    ];

    const subjectLower = subject.toLowerCase();
    
    const hasUrgency = urgencyKeywords.some(kw => subjectLower.includes(kw));
    const hasMoneyTheme = moneyKeywords.some(kw => subjectLower.includes(kw));
    const hasAllCaps = subject === subject.toUpperCase() && subject.length > 10;
    const hasExcessivePunctuation = (subject.match(/!+/g) || []).length > 1;

    return {
        subject,
        hasUrgency,
        hasMoneyTheme,
        hasAllCaps,
        hasExcessivePunctuation,
        threatScore: (hasUrgency ? 20 : 0) + 
                     (hasMoneyTheme ? 15 : 0) + 
                     (hasAllCaps ? 10 : 0) + 
                     (hasExcessivePunctuation ? 10 : 0)
    };
}

function analyzeSender(senderName: string, email: string): any {
    const nameLower = senderName.toLowerCase();
    const domain = email ? email.split('@')[1]?.toLowerCase() : '';

    const brandsToCheck = [
        'paypal', 'amazon', 'microsoft', 'google', 'apple',
        'facebook', 'bank', 'wells fargo', 'chase', 'citibank',
        'netflix', 'spotify', 'ebay', 'fedex', 'ups', 'dhl'
    ];

    const impersonatesBrand = brandsToCheck.some(brand =>
        nameLower.includes(brand) && domain && !domain.includes(brand)
    );

    const hasGenericName = /^(support|admin|service|team|info|security|account)$/i.test(nameLower);

    return {
        senderName,
        impersonatesBrand,
        hasGenericName,
        brandMatch: brandsToCheck.find(brand => nameLower.includes(brand)) || null,
        threatScore: (impersonatesBrand ? 40 : 0) + (hasGenericName ? 10 : 0)
    };
}

function analyzeHeaders(headers: string): any {
    // Basic header validation
    const hasFrom = /^From:/mi.test(headers);
    const hasMessageId = /^Message-ID:/mi.test(headers);
    const hasDate = /^Date:/mi.test(headers);
    const hasReceived = /^Received:/mi.test(headers);

    const missingHeaders = [];
    if (!hasFrom) missingHeaders.push('From');
    if (!hasMessageId) missingHeaders.push('Message-ID');
    if (!hasDate) missingHeaders.push('Date');
    if (!hasReceived) missingHeaders.push('Received');

    // Check for authentication
    const hasSPF = /spf=pass/i.test(headers);
    const hasDKIM = /dkim=pass/i.test(headers);
    const hasDMARC = /dmarc=pass/i.test(headers);

    return {
        missingHeaders,
        hasSPF,
        hasDKIM,
        hasDMARC,
        threatScore: (missingHeaders.length * 10) +
                     (!hasSPF ? 15 : 0) +
                     (!hasDKIM ? 15 : 0) +
                     (!hasDMARC ? 20 : 0)
    };
}

function analyzeContent(body: string): any {
    const bodyLower = body.toLowerCase();

    const phishingPhrases = [
        'click here', 'click below', 'verify your account', 'confirm your identity',
        'update your information', 'unusual activity', 'suspended your account',
        'verify within', 'claim your', 'you have won', 'urgent action',
        'reset your password', 'confirm your password', 'billing problem'
    ];

    const hasPhishingPhrases = phishingPhrases.filter(phrase =>
        bodyLower.includes(phrase)
    );

    // Check for links
    const linkCount = (body.match(/https?:\/\//g) || []).length;
    const hasMultipleLinks = linkCount > 3;

    // Check for URL shorteners
    const shortenerDomains = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly'];
    const hasShorteners = shortenerDomains.some(domain => bodyLower.includes(domain));

    // Check for form inputs (phishing pages often have forms)
    const hasFormTags = /<form/i.test(body) || /<input/i.test(body);

    return {
        phishingPhrases: hasPhishingPhrases,
        linkCount,
        hasMultipleLinks,
        hasShorteners,
        hasFormTags,
        threatScore: (hasPhishingPhrases.length * 10) +
                     (hasMultipleLinks ? 15 : 0) +
                     (hasShorteners ? 20 : 0) +
                     (hasFormTags ? 25 : 0)
    };
}

function analyzeDomain(domain: string): any {
    // Check for look-alike domains
    const legitimateDomains = [
        'paypal.com', 'amazon.com', 'microsoft.com', 'google.com',
        'apple.com', 'facebook.com', 'netflix.com', 'ebay.com'
    ];

    const domainLower = domain.toLowerCase();
    const looksLikeLegitimate = legitimateDomains.some(legit => {
        // Check for typosquatting
        const similarity = calculateSimilarity(domainLower, legit);
        return similarity > 0.7 && domainLower !== legit;
    });

    const hasHyphen = domain.includes('-');
    const hasNumbers = /\d/.test(domain);
    const isLongDomain = domain.length > 20;

    return {
        domain,
        looksLikeLegitimate,
        hasHyphen,
        hasNumbers,
        isLongDomain,
        threatScore: (looksLikeLegitimate ? 35 : 0) +
                     (hasHyphen ? 10 : 0) +
                     (hasNumbers ? 10 : 0) +
                     (isLongDomain ? 10 : 0)
    };
}

function calculateSimilarity(str1: string, str2: string): number {
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;
    
    if (longer.length === 0) return 1.0;
    
    const editDistance = levenshteinDistance(longer, shorter);
    return (longer.length - editDistance) / longer.length;
}

function levenshteinDistance(str1: string, str2: string): number {
    const matrix: number[][] = [];

    for (let i = 0; i <= str2.length; i++) {
        matrix[i] = [i];
    }

    for (let j = 0; j <= str1.length; j++) {
        matrix[0][j] = j;
    }

    for (let i = 1; i <= str2.length; i++) {
        for (let j = 1; j <= str1.length; j++) {
            if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j] + 1
                );
            }
        }
    }

    return matrix[str2.length][str1.length];
}

function calculateCompositeScore(analysis: any): any {
    const scores: number[] = [];
    const reasoning: string[] = [];
    const redFlags: string[] = [];

    // Email analysis
    if (analysis.emailAnalysis) {
        scores.push(analysis.emailAnalysis.threatScore);
        if (analysis.emailAnalysis.suspiciousLocalPart) {
            redFlags.push('Suspicious email address pattern detected');
        }
    }

    // Subject analysis
    if (analysis.subjectAnalysis) {
        scores.push(analysis.subjectAnalysis.threatScore);
        if (analysis.subjectAnalysis.hasUrgency) {
            redFlags.push('Subject line uses urgency tactics');
        }
        if (analysis.subjectAnalysis.hasMoneyTheme) {
            redFlags.push('Subject mentions financial/payment topics');
        }
    }

    // Sender analysis
    if (analysis.senderAnalysis) {
        scores.push(analysis.senderAnalysis.threatScore);
        if (analysis.senderAnalysis.impersonatesBrand) {
            redFlags.push(`Sender appears to impersonate ${analysis.senderAnalysis.brandMatch}`);
        }
    }

    // Header analysis
    if (analysis.headerAnalysis) {
        scores.push(analysis.headerAnalysis.threatScore);
        if (!analysis.headerAnalysis.hasSPF || !analysis.headerAnalysis.hasDKIM || !analysis.headerAnalysis.hasDMARC) {
            redFlags.push('Email authentication (SPF/DKIM/DMARC) incomplete or failed');
        }
    }

    // Content analysis
    if (analysis.contentAnalysis) {
        scores.push(analysis.contentAnalysis.threatScore);
        if (analysis.contentAnalysis.hasShorteners) {
            redFlags.push('Email contains URL shorteners (common in phishing)');
        }
        if (analysis.contentAnalysis.phishingPhrases.length > 0) {
            redFlags.push(`Contains phishing phrases: ${analysis.contentAnalysis.phishingPhrases.slice(0, 3).join(', ')}`);
        }
    }

    // Domain analysis
    if (analysis.domainAnalysis) {
        scores.push(analysis.domainAnalysis.threatScore);
        if (analysis.domainAnalysis.looksLikeLegitimate) {
            redFlags.push('Domain resembles a legitimate brand (possible typosquatting)');
        }
    }

    // Calculate weighted average
    const totalScore = scores.reduce((a, b) => a + b, 0);
    const averageScore = scores.length > 0 ? totalScore / scores.length : 0;
    const finalScore = Math.min(Math.round(averageScore * 1.2), 100); // Apply multiplier for sensitivity

    // Generate reasoning
    if (finalScore >= 75) {
        reasoning.push('HIGH CONFIDENCE phishing attempt detected based on multiple red flags');
    } else if (finalScore >= 50) {
        reasoning.push('MODERATE CONFIDENCE phishing indicators present');
    } else if (finalScore >= 25) {
        reasoning.push('LOW CONFIDENCE phishing - some suspicious elements detected');
    } else {
        reasoning.push('Email appears legitimate with minimal risk indicators');
    }

    reasoning.push(`Analysis based on ${scores.length} signal sources`);

    return {
        score: finalScore,
        confidence: Math.min(scores.length * 15, 95), // Confidence based on data availability
        reasoning,
        redFlags
    };
}

function getThreatLevel(score: number): string {
    if (score >= 85) return 'critical';
    if (score >= 75) return 'high';
    if (score >= 50) return 'medium';
    if (score >= 25) return 'low';
    return 'safe';
}

function getRecommendation(score: number): string {
    if (score >= 85) {
        return 'BLOCK - Strong indicators of phishing. Do not interact with this email.';
    } else if (score >= 75) {
        return 'QUARANTINE - Multiple phishing indicators detected. Review with caution.';
    } else if (score >= 50) {
        return 'REVIEW - Some suspicious elements present. Verify sender before taking action.';
    } else if (score >= 25) {
        return 'CAUTION - Minor concerns detected. Exercise normal email safety practices.';
    }
    return 'ALLOW - Email appears legitimate. Standard precautions apply.';
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
