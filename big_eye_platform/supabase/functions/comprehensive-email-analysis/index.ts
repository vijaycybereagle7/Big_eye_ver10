Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Max-Age': '86400',
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const { emailContent } = await req.json();

        if (!emailContent || typeof emailContent !== 'string') {
            throw new Error('Email content is required as a string');
        }
        if (emailContent.length > 1_000_000) {
            throw new Error('Email content exceeds the 1 MB safety limit');
        }

        const supabaseUrl = Deno.env.get('SUPABASE_URL');
        const anonKey = Deno.env.get('SUPABASE_ANON_KEY');
        const authHeader = req.headers.get('authorization') || '';

        if (!supabaseUrl || !anonKey) {
            throw new Error('Missing Supabase credentials');
        }

        // Parse email content to extract components
        const parsedEmail = parseEmailContent(emailContent);

        // Run all analyses in parallel for speed
        const [
            headerAnalysis,
            domainAnalysis,
            legitimacyAnalysis,
            blacklistAnalysis,
            ipAnalysis,
            phishingAnalysis,
            tempEmailAnalysis,
            domainAgeAnalysis,
            linkAnalysis
        ] = await Promise.allSettled([
            // 1. Email Header Analysis
            callEdgeFunction(supabaseUrl, anonKey, authHeader, 'analyze-email-header', {
                headers: parsedEmail.headers
            }),
            // 2. Domain Checker
            parsedEmail.senderDomain
                ? callEdgeFunction(supabaseUrl, anonKey, authHeader, 'check-domain', {
                    domain: parsedEmail.senderDomain
                })
                : Promise.resolve({ data: { error: true, message: 'Sender domain could not be parsed' } }),
            // 3. Email Legitimacy
            parsedEmail.senderEmail
                ? callEdgeFunction(supabaseUrl, anonKey, authHeader, 'check-email-legitimacy', {
                    email: parsedEmail.senderEmail
                })
                : Promise.resolve({ data: { error: true, message: 'Sender email could not be parsed' } }),
            // 4. Blacklist Scanner
            parsedEmail.senderEmail || parsedEmail.senderDomain
                ? callEdgeFunction(supabaseUrl, anonKey, authHeader, 'scan-blacklist', {
                    email: parsedEmail.senderEmail || undefined,
                    domain: parsedEmail.senderDomain || undefined
                })
                : Promise.resolve({ data: { error: true, message: 'No sender indicator was parsed' } }),
            // 5. IP Intelligence
            parsedEmail.senderIP
                ? callEdgeFunction(supabaseUrl, anonKey, authHeader, 'check-ip-reputation', {
                    ip: parsedEmail.senderIP
                })
                : Promise.resolve({ data: { error: true, message: 'No public sender IP was found in Received headers' } }),
            // 6. AI Phishing Detection
            callEdgeFunction(supabaseUrl, anonKey, authHeader, 'analyze-phishing-probability', {
                email: parsedEmail.senderEmail,
                subject: parsedEmail.subject,
                senderName: parsedEmail.senderName,
                headers: parsedEmail.headers,
                body: parsedEmail.body,
                domain: parsedEmail.senderDomain
            }),
            // 7. Temp Email Detector
            callEdgeFunction(supabaseUrl, anonKey, authHeader, 'detect-temp-email', {
                email: parsedEmail.senderEmail
            }),
            // 8. Domain Age Tracker
            callEdgeFunction(supabaseUrl, anonKey, authHeader, 'get-domain-age', {
                domain: parsedEmail.senderDomain
            }),
            // 9. Link Checker
            parsedEmail.links.length > 0
                ? callEdgeFunction(supabaseUrl, anonKey, authHeader, 'analyze-email-links', {
                    emailContent: parsedEmail.body
                })
                : Promise.resolve({ data: { totalLinks: 0, analysis: [], overallThreatScore: 0 } })
        ]);

        // Compile results
        const results = {
            emailHeaderAnalysis: getSettledValue(headerAnalysis),
            domainAnalysis: getSettledValue(domainAnalysis),
            legitimacyAnalysis: getSettledValue(legitimacyAnalysis),
            blacklistAnalysis: getSettledValue(blacklistAnalysis),
            ipAnalysis: getSettledValue(ipAnalysis),
            phishingAnalysis: getSettledValue(phishingAnalysis),
            tempEmailAnalysis: getSettledValue(tempEmailAnalysis),
            domainAgeAnalysis: getSettledValue(domainAgeAnalysis),
            linkAnalysis: getSettledValue(linkAnalysis)
        };

        // Generate comprehensive verdict
        const verdict = generateComprehensiveVerdict(results, parsedEmail);

        // Track analytics (non-blocking)
        trackAnalytics(req, 'All in One Analysis', 'comprehensive-email-analysis', {
            verdict: verdict.overallVerdict,
            confidenceScore: verdict.confidenceScore,
            toolsExecuted: verdict.toolsExecuted
        }).catch(err => console.warn('Analytics tracking failed:', err));

        const response = {
            parsedEmail: {
                senderEmail: parsedEmail.senderEmail,
                senderDomain: parsedEmail.senderDomain,
                senderName: parsedEmail.senderName,
                subject: parsedEmail.subject,
                linkCount: parsedEmail.links.length
            },
            individualAnalyses: results,
            comprehensiveVerdict: verdict
        };

        return new Response(JSON.stringify({ data: response }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Comprehensive analysis error:', error);

        const errorResponse = {
            error: {
                code: 'COMPREHENSIVE_ANALYSIS_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function parseEmailContent(emailContent: string): any {
    // Normalize CRLF so messages copied from Outlook/Gmail parse correctly.
    const normalized = emailContent.replace(/\r\n/g, '\n');
    const headerEndIndex = normalized.search(/\n\s*\n/);
    const headers = headerEndIndex > -1 ? normalized.substring(0, headerEndIndex) : normalized;
    const body = headerEndIndex > -1 ? normalized.substring(headerEndIndex).replace(/^\s+/, '') : '';

    // Extract From header
    const fromMatch = headers.match(/^From:\s*(.+?)$/mi);
    const fromValue = fromMatch ? fromMatch[1].trim() : '';
    
    // Extract email and name from From header
    let senderEmail = '';
    let senderName = '';
    
    const emailMatch = fromValue.match(/<(.+?)>/);
    if (emailMatch) {
        senderEmail = emailMatch[1].trim();
        senderName = fromValue.replace(emailMatch[0], '').replace(/['"]/g, '').trim();
    } else {
        senderEmail = fromValue;
    }

    const senderDomain = senderEmail.split('@')[1] || '';

    // Extract subject
    const subjectMatch = headers.match(/^Subject:\s*(.+?)$/mi);
    const subject = subjectMatch ? subjectMatch[1].trim() : '';

    // Extract the earliest public-looking IPv4 from Received headers.
    const receivedMatches = [...headers.matchAll(/Received:[^\n]*?\[(\d{1,3}(?:\.\d{1,3}){3})\]/gi)];
    const senderIP = receivedMatches.length > 0 ? receivedMatches[receivedMatches.length - 1][1] : null;

    // Extract all links from body
    const linkRegex = /https?:\/\/[^\s<>"]+/gi;
    const links = [...body.matchAll(linkRegex)].map(match => match[0]);

    return {
        headers,
        body,
        senderEmail,
        senderDomain,
        senderName,
        subject,
        senderIP,
        links
    };
}

async function callEdgeFunction(
    supabaseUrl: string,
    anonKey: string,
    authHeader: string,
    functionName: string,
    body: any
): Promise<any> {
    const response = await fetch(`${supabaseUrl}/functions/v1/${functionName}`, {
        method: 'POST',
        headers: {
            'Authorization': authHeader || `Bearer ${anonKey}`,
            'Content-Type': 'application/json',
            'apikey': anonKey
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error(`${functionName} failed: ${response.statusText}`);
    }

    return await response.json();
}

function getSettledValue(result: PromiseSettledResult<any>): any {
    if (result.status === 'fulfilled') {
        return result.value?.data || result.value;
    } else {
        return {
            error: true,
            message: result.reason?.message || 'Analysis failed'
        };
    }
}

function generateComprehensiveVerdict(results: any, parsedEmail: any): any {
    let totalScore = 0;
    let scoreCount = 0;
    const redFlags: string[] = [];
    const positiveIndicators: string[] = [];
    let toolsExecuted = 0;

    // Email Header Analysis
    if (results.emailHeaderAnalysis && !results.emailHeaderAnalysis.error) {
        toolsExecuted++;
        totalScore += results.emailHeaderAnalysis.threatScore || 0;
        scoreCount++;
        
        if (results.emailHeaderAnalysis.anomalies?.length > 0) {
            redFlags.push(`Email header anomalies detected: ${results.emailHeaderAnalysis.anomalies.length} issues`);
        }
        
        if (results.emailHeaderAnalysis.spf?.status === 'pass' && 
            results.emailHeaderAnalysis.dkim?.status === 'pass' && 
            results.emailHeaderAnalysis.dmarc?.status === 'pass') {
            positiveIndicators.push('Email authentication passed (SPF, DKIM, DMARC)');
        }
    }

    // Domain Analysis
    if (results.domainAnalysis && !results.domainAnalysis.error) {
        toolsExecuted++;
        totalScore += results.domainAnalysis.threatScore || 0;
        scoreCount++;
        
        if (results.domainAnalysis.riskLevel === 'high' || results.domainAnalysis.riskLevel === 'critical') {
            redFlags.push(`Domain reputation: ${results.domainAnalysis.riskLevel}`);
        }
    }

    // Email Legitimacy
    if (results.legitimacyAnalysis && !results.legitimacyAnalysis.error) {
        toolsExecuted++;
        totalScore += results.legitimacyAnalysis.threatScore || 0;
        scoreCount++;
        
        if (results.legitimacyAnalysis.disposable) {
            redFlags.push('Sender uses disposable/temporary email address');
        }
        
        if (results.legitimacyAnalysis.deliverable) {
            positiveIndicators.push('Sender email is deliverable');
        }
    }

    // Blacklist Analysis
    if (results.blacklistAnalysis && !results.blacklistAnalysis.error) {
        toolsExecuted++;
        totalScore += results.blacklistAnalysis.overallThreatScore || 0;
        scoreCount++;
        
        if (results.blacklistAnalysis.blacklisted) {
            redFlags.push('Sender IP is blacklisted for abuse');
        }
    }

    // IP Intelligence
    if (results.ipAnalysis && !results.ipAnalysis.error) {
        toolsExecuted++;
        totalScore += results.ipAnalysis.threatScore || 0;
        scoreCount++;
        
        if (results.ipAnalysis.whois?.isVPN || results.ipAnalysis.whois?.isTor) {
            redFlags.push('Sender using VPN/Tor (anonymization detected)');
        }
    }

    // AI Phishing Detection
    if (results.phishingAnalysis && !results.phishingAnalysis.error) {
        toolsExecuted++;
        totalScore += results.phishingAnalysis.phishingScore || 0;
        scoreCount++;
        
        if (results.phishingAnalysis.redFlags?.length > 0) {
            results.phishingAnalysis.redFlags.slice(0, 3).forEach((flag: string) => {
                redFlags.push(flag);
            });
        }
    }

    // Temp Email Detection
    if (results.tempEmailAnalysis && !results.tempEmailAnalysis.error) {
        toolsExecuted++;
        if (results.tempEmailAnalysis.isTemporary) {
            redFlags.push('Temporary email service detected');
        }
    }

    // Domain Age
    if (results.domainAgeAnalysis && !results.domainAgeAnalysis.error) {
        toolsExecuted++;
        totalScore += results.domainAgeAnalysis.threatScore || 0;
        scoreCount++;
        
        if (results.domainAgeAnalysis.ageInDays !== null && results.domainAgeAnalysis.ageInDays < 90) {
            redFlags.push(`Domain is very new: ${results.domainAgeAnalysis.ageDescription}`);
        } else if (results.domainAgeAnalysis.ageInDays > 365) {
            positiveIndicators.push(`Established domain: ${results.domainAgeAnalysis.ageDescription}`);
        }
    }

    // Link Analysis
    if (results.linkAnalysis && !results.linkAnalysis.error) {
        toolsExecuted++;
        totalScore += results.linkAnalysis.overallThreatScore || 0;
        scoreCount++;
        
        if (results.linkAnalysis.criticalLinksCount > 0) {
            redFlags.push(`${results.linkAnalysis.criticalLinksCount} malicious link(s) detected`);
        }
    }

    // Calculate overall score
    const averageScore = scoreCount > 0 ? totalScore / scoreCount : 0;
    const confidenceScore = Math.round(averageScore);

    // Determine overall verdict
    let overallVerdict = '';
    let recommendation = '';
    let riskLevel = '';

    if (confidenceScore >= 85 || redFlags.length >= 5) {
        overallVerdict = 'PHISHING';
        riskLevel = 'critical';
        recommendation = 'BLOCK - This email exhibits strong phishing characteristics. Do not interact, click links, or provide any information.';
    } else if (confidenceScore >= 70 || redFlags.length >= 3) {
        overallVerdict = 'HIGHLY SUSPICIOUS';
        riskLevel = 'high';
        recommendation = 'QUARANTINE - Multiple suspicious indicators detected. Exercise extreme caution and verify sender through alternative channels.';
    } else if (confidenceScore >= 50 || redFlags.length >= 2) {
        overallVerdict = 'SPAM';
        riskLevel = 'medium';
        recommendation = 'REVIEW - This email shows characteristics of spam or phishing. Verify legitimacy before taking any action.';
    } else if (confidenceScore >= 25 || redFlags.length >= 1) {
        overallVerdict = 'SUSPICIOUS';
        riskLevel = 'low';
        recommendation = 'CAUTION - Some concerns detected. Apply standard email security practices.';
    } else {
        overallVerdict = 'LEGITIMATE';
        riskLevel = 'safe';
        recommendation = 'ALLOW - Email appears legitimate based on comprehensive analysis. Standard precautions still apply.';
    }

    return {
        overallVerdict,
        confidenceScore,
        riskLevel,
        recommendation,
        toolsExecuted,
        totalToolsAvailable: 9,
        redFlags,
        positiveIndicators,
        summary: generateSummary(overallVerdict, confidenceScore, redFlags, positiveIndicators)
    };
}

function generateSummary(verdict: string, score: number, redFlags: string[], positiveIndicators: string[]): string {
    let summary = `Comprehensive analysis verdict: ${verdict} (Confidence: ${score}%).\n\n`;
    
    if (redFlags.length > 0) {
        summary += `Risk Factors Identified:\n`;
        redFlags.forEach(flag => {
            summary += `- ${flag}\n`;
        });
        summary += '\n';
    }
    
    if (positiveIndicators.length > 0) {
        summary += `Positive Indicators:\n`;
        positiveIndicators.forEach(indicator => {
            summary += `+ ${indicator}\n`;
        });
        summary += '\n';
    }
    
    return summary.trim();
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
