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
        const { emailContent } = await req.json();

        if (!emailContent) {
            throw new Error('Email content is required');
        }

        // Extract all URLs from email content using regex
        const urlRegex = /https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)/gi;
        const extractedUrls = emailContent.match(urlRegex) || [];

        if (extractedUrls.length === 0) {
            return new Response(JSON.stringify({ 
                data: {
                    message: 'No links found in email content',
                    linksFound: 0,
                    links: [],
                    overallThreatLevel: 'Safe',
                    overallScore: 0
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Analyze each extracted link
        const analyzedLinks = [];
        let totalThreatScore = 0;

        for (const url of extractedUrls) {
            try {
                const urlObj = new URL(url);
                const domain = urlObj.hostname;
                const protocol = urlObj.protocol;

                const linkAnalysis: any = {
                    url,
                    domain,
                    protocol,
                    threatScore: 0,
                    threatLevel: 'Unknown',
                    warnings: [],
                    suspiciousIndicators: []
                };

                // Check 1: Protocol
                if (protocol !== 'https:') {
                    linkAnalysis.warnings.push('Insecure HTTP connection');
                    linkAnalysis.threatScore += 15;
                }

                // Check 2: Suspicious patterns
                const suspiciousPatterns = [
                    { pattern: /login/i, description: 'Login keyword' },
                    { pattern: /verify/i, description: 'Verify keyword' },
                    { pattern: /secure/i, description: 'Secure keyword' },
                    { pattern: /account/i, description: 'Account keyword' },
                    { pattern: /update/i, description: 'Update keyword' },
                    { pattern: /confirm/i, description: 'Confirm keyword' },
                    { pattern: /urgent/i, description: 'Urgency keyword' },
                    { pattern: /suspended/i, description: 'Suspended keyword' },
                    { pattern: /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/, description: 'IP address instead of domain' },
                ];

                suspiciousPatterns.forEach(({ pattern, description }) => {
                    if (pattern.test(url)) {
                        linkAnalysis.suspiciousIndicators.push(description);
                    }
                });

                if (linkAnalysis.suspiciousIndicators.length > 2) {
                    linkAnalysis.warnings.push('Multiple suspicious keywords detected');
                    linkAnalysis.threatScore += 25;
                }

                // Check 3: URL shorteners
                const urlShorteners = [
                    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 
                    'is.gd', 'buff.ly', 'adf.ly', 'tiny.cc', 'rb.gy'
                ];

                if (urlShorteners.some(shortener => domain.includes(shortener))) {
                    linkAnalysis.warnings.push('Link shortener detected - destination hidden');
                    linkAnalysis.threatScore += 30;
                }

                // Check 4: Obfuscated URLs
                if (url.includes('%') || url.includes('@') || url.split('/').length > 6) {
                    linkAnalysis.warnings.push('URL appears obfuscated or overly complex');
                    linkAnalysis.threatScore += 20;
                }

                // Check 5: Homograph attack
                if (domain.includes('xn--')) {
                    linkAnalysis.warnings.push('Internationalized domain name - possible homograph attack');
                    linkAnalysis.threatScore += 35;
                }

                // Check 6: Mismatched domain
                const commonBrands = ['paypal', 'google', 'microsoft', 'amazon', 'apple', 'facebook', 'instagram'];
                const domainLower = domain.toLowerCase();
                const hasBrandName = commonBrands.some(brand => domainLower.includes(brand));
                const isOfficialDomain = commonBrands.some(brand => 
                    domainLower === `${brand}.com` || 
                    domainLower === `www.${brand}.com` ||
                    domainLower.endsWith(`.${brand}.com`)
                );

                if (hasBrandName && !isOfficialDomain) {
                    linkAnalysis.warnings.push('Domain impersonates a well-known brand');
                    linkAnalysis.threatScore += 40;
                }

                // Check 7: JavaScript detection in URL
                if (url.toLowerCase().includes('javascript:') || url.toLowerCase().includes('data:')) {
                    linkAnalysis.warnings.push('Malicious JavaScript or data URL detected');
                    linkAnalysis.threatScore += 50;
                }

                // Determine threat level
                if (linkAnalysis.threatScore >= 70) {
                    linkAnalysis.threatLevel = 'Critical';
                } else if (linkAnalysis.threatScore >= 50) {
                    linkAnalysis.threatLevel = 'High';
                } else if (linkAnalysis.threatScore >= 30) {
                    linkAnalysis.threatLevel = 'Medium';
                } else if (linkAnalysis.threatScore >= 10) {
                    linkAnalysis.threatLevel = 'Low';
                } else {
                    linkAnalysis.threatLevel = 'Safe';
                }

                totalThreatScore += linkAnalysis.threatScore;
                analyzedLinks.push(linkAnalysis);

            } catch (error) {
                analyzedLinks.push({
                    url,
                    error: 'Failed to parse URL',
                    threatLevel: 'Unknown',
                    threatScore: 0
                });
            }
        }

        // Calculate overall threat assessment
        const avgThreatScore = Math.round(totalThreatScore / analyzedLinks.length);
        let overallThreatLevel = 'Safe';
        let overallRecommendation = '';

        if (avgThreatScore >= 70) {
            overallThreatLevel = 'Critical';
            overallRecommendation = 'DO NOT interact with this email - likely phishing/scam';
        } else if (avgThreatScore >= 50) {
            overallThreatLevel = 'High';
            overallRecommendation = 'Delete this email immediately - multiple dangerous links detected';
        } else if (avgThreatScore >= 30) {
            overallThreatLevel = 'Medium';
            overallRecommendation = 'Exercise extreme caution - suspicious links present';
        } else if (avgThreatScore >= 10) {
            overallThreatLevel = 'Low';
            overallRecommendation = 'Verify sender before clicking any links';
        } else {
            overallThreatLevel = 'Safe';
            overallRecommendation = 'Email links appear legitimate';
        }

        const criticalLinks = analyzedLinks.filter(link => link.threatLevel === 'Critical').length;
        const highRiskLinks = analyzedLinks.filter(link => link.threatLevel === 'High').length;

        const results = {
            linksFound: extractedUrls.length,
            linksAnalyzed: analyzedLinks.length,
            overallThreatLevel,
            overallThreatScore: avgThreatScore,
            overallRecommendation,
            statistics: {
                criticalLinks,
                highRiskLinks,
                totalSuspicious: criticalLinks + highRiskLinks
            },
            links: analyzedLinks,
            timestamp: new Date().toISOString()
        };

        return new Response(JSON.stringify({ data: results }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Email link analysis error:', error);

        const errorResponse = {
            error: {
                code: 'EMAIL_LINK_ANALYSIS_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
