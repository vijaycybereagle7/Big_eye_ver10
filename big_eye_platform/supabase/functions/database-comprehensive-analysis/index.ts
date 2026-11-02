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
        const { 
            analysis_type, 
            emails = [], 
            domains = [], 
            ip_addresses = [], 
            urls = [],
            options = {}
        } = await req.json();

        if (!analysis_type) {
            throw new Error('Analysis type is required');
        }

        if (!['comprehensive', 'email_security', 'phishing_analysis', 'threat_intelligence'].includes(analysis_type)) {
            throw new Error('Invalid analysis type. Must be one of: comprehensive, email_security, phishing_analysis, threat_intelligence');
        }

        // Check total items limit
        const totalItems = emails.length + domains.length + ip_addresses.length + urls.length;
        if (totalItems > 100) {
            throw new Error('Maximum 100 items allowed per bulk analysis');
        }

        // Perform comprehensive analysis using Big Eye Security Database
        const analysisResults = await performComprehensiveAnalysisBigEyeDB(analysis_type, {
            emails,
            domains,
            ip_addresses,
            urls
        }, options);

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Big Eye Database Analysis', 'comprehensive-analysis', {
            analysis_type,
            total_items: totalItems,
            threats_found: analysisResults.threats_found,
            analysis_duration: analysisResults.analysis_duration
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: analysisResults }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Database comprehensive analysis error:', error);

        const errorResponse = {
            error: {
                code: 'DATABASE_COMPREHENSIVE_ANALYSIS_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function performComprehensiveAnalysisBigEyeDB(analysisType: string, data: any, options: any) {
    const startTime = Date.now();
    
    let results = {
        analysis_type: analysisType,
        timestamp: new Date().toISOString(),
        total_items: 0,
        summary: {
            threats_found: 0,
            high_risk_items: 0,
            medium_risk_items: 0,
            low_risk_items: 0,
            clean_items: 0
        },
        detailed_results: {
            emails: [],
            domains: [],
            ip_addresses: [],
            urls: []
        },
        recommendations: [],
        threat_intelligence_summary: {},
        threats_found: 0,
        analysis_duration: 0
    };

    // Analyze emails
    if (data.emails && data.emails.length > 0) {
        for (const email of data.emails) {
            const emailAnalysis = await analyzeEmailWithBigEyeDB(email);
            results.detailed_results.emails.push(emailAnalysis);
            results.total_items++;
            updateThreatSummary(results, emailAnalysis);
        }
    }

    // Analyze domains
    if (data.domains && data.domains.length > 0) {
        for (const domain of data.domains) {
            const domainAnalysis = await analyzeDomainWithBigEyeDB(domain);
            results.detailed_results.domains.push(domainAnalysis);
            results.total_items++;
            updateThreatSummary(results, domainAnalysis);
        }
    }

    // Analyze IP addresses
    if (data.ip_addresses && data.ip_addresses.length > 0) {
        for (const ip of data.ip_addresses) {
            const ipAnalysis = await analyzeIPWithBigEyeDB(ip);
            results.detailed_results.ip_addresses.push(ipAnalysis);
            results.total_items++;
            updateThreatSummary(results, ipAnalysis);
        }
    }

    // Analyze URLs
    if (data.urls && data.urls.length > 0) {
        for (const url of data.urls) {
            const urlAnalysis = await analyzeURLWithBigEyeDB(url);
            results.detailed_results.urls.push(urlAnalysis);
            results.total_items++;
            updateThreatSummary(results, urlAnalysis);
        }
    }

    // Generate threat intelligence summary
    results.threat_intelligence_summary = generateThreatIntelligenceSummary(results.detailed_results);
    
    // Generate recommendations
    results.recommendations = generateComprehensiveRecommendations(results);
    
    // Calculate analysis duration
    results.analysis_duration = Date.now() - startTime;
    results.threats_found = results.summary.threats_found;

    return results;
}

async function analyzeEmailWithBigEyeDB(email: string) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValidFormat = emailRegex.test(email);
    const domain = email.split('@')[1]?.toLowerCase() || '';
    
    const threats = [];
    let riskLevel = 'low';
    
    // Check for disposable email
    const disposableDomains = ['10minutemail.com', 'guerrillamail.com', 'mailinator.com'];
    if (disposableDomains.includes(domain)) {
        threats.push({
            type: 'disposable_email',
            severity: 'medium',
            description: 'Disposable email address detected',
            source: 'Big Eye Security Database'
        });
        riskLevel = 'medium';
    }
    
    // Check for suspicious patterns
    if (email.includes('+') && email.includes('test')) {
        threats.push({
            type: 'test_email',
            severity: 'low',
            description: 'Test email address pattern detected',
            source: 'Big Eye Security Database'
        });
    }
    
    return {
        item: email,
        type: 'email',
        is_valid: isValidFormat,
        risk_level: riskLevel,
        threats: threats,
        confidence_score: threats.length === 0 ? 0.9 : 0.6,
        analysis_timestamp: new Date().toISOString()
    };
}

async function analyzeDomainWithBigEyeDB(domain: string) {
    const threats = [];
    let riskLevel = 'low';
    
    // Deterministic naming indicators. External reputation is intentionally
    // not fabricated when a provider is not configured.
    if (domain.includes('phishing') || domain.includes('malware')) {
        threats.push({
            type: 'suspicious_domain',
            severity: 'high',
            description: 'Domain with suspicious naming pattern',
            source: 'Big Eye Security Database'
        });
        riskLevel = 'high';
    }
    
    const suspiciousTLDs = ['.tk', '.ml', '.ga', '.cf'];
    const hasSuspiciousTLD = suspiciousTLDs.some(tld => domain.endsWith(tld));
    if (hasSuspiciousTLD) {
        threats.push({
            type: 'suspicious_tld',
            severity: 'medium',
            description: 'Domain uses potentially suspicious TLD',
            source: 'Big Eye Security Database'
        });
        if (riskLevel !== 'high') riskLevel = 'medium';
    }
    
    return {
        item: domain,
        type: 'domain',
        is_valid: domain.includes('.'),
        risk_level: riskLevel,
        threats: threats,
        confidence_score: threats.length === 0 ? 0.8 : 0.5,
        analysis_timestamp: new Date().toISOString()
    };
}

async function analyzeIPWithBigEyeDB(ip: string) {
    const threats = [];
    let riskLevel = 'low';
    
    // Deterministic network classification. A private address is not a
    // blacklist hit; it is only unusual in an internet-delivered indicator.
    const parts = ip.split('.').map(Number);
    const isValidIPv4 = parts.length === 4 && parts.every(part => Number.isInteger(part) && part >= 0 && part <= 255);
    if (isValidIPv4 && (ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.16.'))) {
        threats.push({
            type: 'private_ip',
            severity: 'low',
            description: 'Private IP address (internal network)',
            source: 'Big Eye Security Database'
        });
    } else if (isValidIPv4 && ip.startsWith('127.')) {
        threats.push({
            type: 'localhost',
            severity: 'low',
            description: 'Localhost IP address',
            source: 'Big Eye Security Database'
        });
    } else if (isValidIPv4 && (ip === '0.0.0.0' || ip.startsWith('255.'))) {
        threats.push({
            type: 'reserved_ip',
            severity: 'medium',
            description: 'Reserved IPv4 address is not a routable public indicator',
            source: 'Big Eye Security Database'
        });
        riskLevel = 'medium';
    } else if (!isValidIPv4) {
        riskLevel = 'high';
    }
    
    return {
        item: ip,
        type: 'ip_address',
        is_valid: isValidIPv4,
        risk_level: riskLevel,
        threats: threats,
        confidence_score: threats.length === 0 ? 0.85 : 0.4,
        analysis_timestamp: new Date().toISOString()
    };
}

async function analyzeURLWithBigEyeDB(url: string) {
    const threats = [];
    let riskLevel = 'low';
    
    // Mock URL security analysis
    if (url.includes('http://') && !url.includes('localhost')) {
        threats.push({
            type: 'insecure_protocol',
            severity: 'medium',
            description: 'URL uses insecure HTTP protocol',
            source: 'Big Eye Security Database'
        });
        riskLevel = 'medium';
    }
    
    // Check for suspicious patterns
    if (url.includes('login') && url.includes('.tk')) {
        threats.push({
            type: 'suspicious_url',
            severity: 'high',
            description: 'Suspicious login URL pattern',
            source: 'Big Eye Security Database'
        });
        riskLevel = 'high';
    }
    
    return {
        item: url,
        type: 'url',
        is_valid: url.startsWith('http://') || url.startsWith('https://'),
        risk_level: riskLevel,
        threats: threats,
        confidence_score: threats.length === 0 ? 0.9 : 0.5,
        analysis_timestamp: new Date().toISOString()
    };
}

function updateThreatSummary(results: any, analysis: any) {
    if (analysis.threats && analysis.threats.length > 0) {
        results.summary.threats_found++;
        
        const highSeverityThreats = analysis.threats.filter((t: any) => t.severity === 'high').length;
        const mediumSeverityThreats = analysis.threats.filter((t: any) => t.severity === 'medium').length;
        const lowSeverityThreats = analysis.threats.filter((t: any) => t.severity === 'low').length;
        
        if (highSeverityThreats > 0) {
            results.summary.high_risk_items++;
        } else if (mediumSeverityThreats > 0) {
            results.summary.medium_risk_items++;
        } else if (lowSeverityThreats > 0) {
            results.summary.low_risk_items++;
        }
    } else {
        results.summary.clean_items++;
    }
}

function generateThreatIntelligenceSummary(detailedResults: any) {
    const summary = {
        total_indicators: 0,
        threat_categories: {},
        geographic_distribution: {},
        top_threat_types: [],
        confidence_distribution: {}
    };

    // Count all indicators
    summary.total_indicators = detailedResults.emails.length + 
                              detailedResults.domains.length + 
                              detailedResults.ip_addresses.length + 
                              detailedResults.urls.length;

    // Aggregate threat categories
    const allThreats = [
        ...detailedResults.emails.flatMap((e: any) => e.threats),
        ...detailedResults.domains.flatMap((d: any) => d.threats),
        ...detailedResults.ip_addresses.flatMap((i: any) => i.threats),
        ...detailedResults.urls.flatMap((u: any) => u.threats)
    ];

    allThreats.forEach((threat: any) => {
        const category = threat.type;
        summary.threat_categories[category] = (summary.threat_categories[category] || 0) + 1;
    });

    // Get top threat types
    summary.top_threat_types = Object.entries(summary.threat_categories)
        .sort(([,a], [,b]) => (b as number) - (a as number))
        .slice(0, 5)
        .map(([type]) => type);

    return summary;
}

function generateComprehensiveRecommendations(results: any): string[] {
    const recommendations = [];

    // High-level recommendations based on analysis
    if (results.summary.high_risk_items > 0) {
        recommendations.push(`Found ${results.summary.high_risk_items} high-risk items. Immediate attention recommended.`);
    }

    if (results.summary.threats_found > results.total_items * 0.3) {
        recommendations.push('High percentage of items contain threats. Consider implementing stricter security measures.');
    }

    // Specific recommendations based on threat types
    const allThreats = [
        ...results.detailed_results.emails.flatMap((e: any) => e.threats),
        ...results.detailed_results.domains.flatMap((d: any) => d.threats),
        ...results.detailed_results.ip_addresses.flatMap((i: any) => i.threats),
        ...results.detailed_results.urls.flatMap((u: any) => u.threats)
    ];

    const threatTypes = allThreats.map((t: any) => t.type);
    
    if (threatTypes.includes('disposable_email')) {
        recommendations.push('Block disposable email addresses in your email validation system.');
    }

    if (threatTypes.includes('blacklisted')) {
        recommendations.push('Implement IP blacklist checking to prevent malicious actors.');
    }

    if (threatTypes.includes('phishing')) {
        recommendations.push('Enhanced phishing detection and user education recommended.');
    }

    if (recommendations.length === 0) {
        recommendations.push('All items passed security analysis. No immediate action required.');
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
