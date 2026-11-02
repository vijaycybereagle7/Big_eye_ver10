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
        const { url } = await req.json();

        if (!url) {
            throw new Error('URL is required');
        }

        // Extract domain from URL
        const urlObj = new URL(url);
        const domain = urlObj.hostname;
        const protocol = urlObj.protocol;

        // Results object
        const results: any = {
            url,
            domain,
            protocol,
            checks: {},
            threatScore: 0,
            threatLevel: 'Unknown',
            warnings: [],
            timestamp: new Date().toISOString()
        };

        // Check 1: Protocol validation
        if (protocol !== 'https:') {
            results.warnings.push('URL does not use HTTPS - potential security risk');
            results.threatScore += 15;
        }
        results.checks.protocol = protocol === 'https:' ? 'Secure (HTTPS)' : 'Insecure (HTTP)';

        // Check 2: Suspicious patterns in URL
        const suspiciousPatterns = [
            /login/i, /verify/i, /secure/i, /account/i, /update/i, 
            /confirm/i, /banking/i, /paypal/i, /ebay/i, /amazon/i,
            /-/g, // excessive hyphens
            /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/, // IP address
        ];

        const foundPatterns: string[] = [];
        suspiciousPatterns.forEach(pattern => {
            if (pattern.test(url)) {
                foundPatterns.push(pattern.toString());
            }
        });

        if (foundPatterns.length > 2) {
            results.warnings.push('URL contains multiple suspicious patterns');
            results.threatScore += 20;
        }

        results.checks.suspiciousPatterns = foundPatterns.length > 0 
            ? `Found ${foundPatterns.length} suspicious patterns` 
            : 'No suspicious patterns detected';

        // Check 3: URL shortener detection
        const urlShorteners = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 
            'is.gd', 'buff.ly', 'adf.ly', 'tiny.cc', 'rb.gy'
        ];

        const isShortened = urlShorteners.some(shortener => domain.includes(shortener));
        if (isShortened) {
            results.warnings.push('URL uses a link shortening service - destination hidden');
            results.threatScore += 25;
        }
        results.checks.urlShortener = isShortened ? 'Yes - destination hidden' : 'No';

        // Check 4: Domain age check (using RDAP API)
        try {
            const rdapResponse = await fetch(`https://rdap.org/domain/${domain}`, {
                headers: { 'Accept': 'application/json' }
            });

            if (rdapResponse.ok) {
                const rdapData = await rdapResponse.json();
                const events = rdapData.events || [];
                const registrationEvent = events.find((e: any) => e.eventAction === 'registration');
                
                if (registrationEvent) {
                    const regDate = new Date(registrationEvent.eventDate);
                    const ageInDays = Math.floor((Date.now() - regDate.getTime()) / (1000 * 60 * 60 * 24));
                    const ageInYears = (ageInDays / 365).toFixed(1);
                    
                    results.checks.domainAge = `${ageInYears} years old`;
                    
                    if (ageInDays < 30) {
                        results.warnings.push('Domain is very new - high risk indicator');
                        results.threatScore += 40;
                    } else if (ageInDays < 90) {
                        results.warnings.push('Domain is relatively new - medium risk');
                        results.threatScore += 20;
                    }
                } else {
                    results.checks.domainAge = 'Unknown';
                }
            } else {
                results.checks.domainAge = 'Unable to verify';
            }
        } catch (error) {
            results.checks.domainAge = 'Error checking domain age';
        }

        // Check 5: SSL Certificate check
        try {
            const sslResponse = await fetch(`https://api.ssllabs.com/api/v3/analyze?host=${domain}&fromCache=on&maxAge=24`, {
                headers: { 'Accept': 'application/json' }
            });

            if (sslResponse.ok) {
                const sslData = await sslResponse.json();
                const grade = sslData.endpoints?.[0]?.grade || 'Unknown';
                results.checks.sslCertificate = `Grade ${grade}`;
                
                if (grade === 'F' || grade === 'T') {
                    results.warnings.push('Poor SSL certificate rating');
                    results.threatScore += 30;
                }
            } else {
                results.checks.sslCertificate = 'Unable to verify';
            }
        } catch (error) {
            results.checks.sslCertificate = 'No SSL certificate';
            results.threatScore += 20;
        }

        // Check 6: Homograph attack detection (IDN/Punycode)
        if (domain.includes('xn--')) {
            results.warnings.push('Domain uses Internationalized Domain Name (IDN) - potential homograph attack');
            results.threatScore += 35;
        }
        results.checks.homographAttack = domain.includes('xn--') ? 'Detected (IDN)' : 'None';

        // Check 7: Check for known phishing indicators
        const phishingKeywords = [
            'verify-account', 'secure-login', 'update-billing', 
            'confirm-identity', 'suspended-account', 'unusual-activity'
        ];

        const hasPhishingKeywords = phishingKeywords.some(keyword => 
            url.toLowerCase().includes(keyword)
        );

        if (hasPhishingKeywords) {
            results.warnings.push('URL contains common phishing keywords');
            results.threatScore += 30;
        }
        results.checks.phishingKeywords = hasPhishingKeywords ? 'Detected' : 'None';

        // Calculate threat level based on score
        if (results.threatScore >= 70) {
            results.threatLevel = 'Critical';
            results.recommendation = 'DO NOT visit this link - high probability of phishing/scam';
        } else if (results.threatScore >= 50) {
            results.threatLevel = 'High';
            results.recommendation = 'Exercise extreme caution - multiple red flags detected';
        } else if (results.threatScore >= 30) {
            results.threatLevel = 'Medium';
            results.recommendation = 'Proceed with caution - some suspicious indicators present';
        } else if (results.threatScore >= 10) {
            results.threatLevel = 'Low';
            results.recommendation = 'Link appears relatively safe but verify sender';
        } else {
            results.threatLevel = 'Safe';
            results.recommendation = 'Link appears legitimate';
        }

        return new Response(JSON.stringify({ data: results }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Link reputation check error:', error);

        const errorResponse = {
            error: {
                code: 'LINK_CHECK_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});
