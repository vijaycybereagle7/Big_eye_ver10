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
        const { email } = await req.json();

        if (!email || typeof email !== 'string') {
            throw new Error('Email address is required');
        }

        // Basic syntax validation
        const syntaxValid = validateEmailSyntax(email);
        if (!syntaxValid) {
            return new Response(JSON.stringify({
                data: {
                    email,
                    syntaxValid: false,
                    deliverable: false,
                    disposable: false,
                    riskLevel: 'high',
                    recommendation: 'Invalid email format',
                    threatScore: 90
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        // Extract domain
        const domain = email.split('@')[1]?.toLowerCase();

        // Check if it's a disposable email
        const isDisposable = await checkDisposable(email);

        // Check DNS/MX records
        const hasMX = await checkMXRecords(domain);

        // Get API key for advanced validation (optional)
        const apiKey = Deno.env.get('EMAIL_VALIDATION_API_KEY');

        let externalValidation = null;

        if (apiKey) {
            // If API key is available, use external validation service
            try {
                externalValidation = await performExternalValidation(email, apiKey);
            } catch (error) {
                console.warn('External validation failed:', error.message);
            }
        }

        const result = {
            email,
            syntaxValid: true,
            hasMXRecord: hasMX,
            disposable: isDisposable,
            deliverable: hasMX && !isDisposable,
            riskLevel: calculateEmailRiskLevel(hasMX, isDisposable),
            threatScore: calculateEmailThreatScore(hasMX, isDisposable),
            recommendation: getEmailRecommendation(hasMX, isDisposable),
            externalValidation: externalValidation || {
                available: false,
                message: 'Configure EMAIL_VALIDATION_API_KEY for advanced validation'
            },
            checks: {
                syntax: true,
                mx: hasMX,
                disposable: isDisposable,
                roleBasedGuess: isRoleBased(email)
            }
        };

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Email Legitimacy Checker', 'email-legitimacy-check', {
            email,
            disposable: isDisposable,
            deliverable: result.deliverable,
            riskLevel: result.riskLevel
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Email legitimacy check error:', error);

        const errorResponse = {
            error: {
                code: 'EMAIL_LEGITIMACY_CHECK_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function validateEmailSyntax(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

async function checkDisposable(email: string): Promise<boolean> {
    // Extract domain
    const domain = email.split('@')[1]?.toLowerCase();
    if (!domain) return false;

    // Check local database first (most reliable)
    if (DISPOSABLE_DOMAINS.has(domain)) {
        return true;
    }

    // Try external API as additional check
    try {
        const response = await fetch(`https://disposable.debounce.io/?email=${encodeURIComponent(email)}`, {
            headers: { 'Accept': 'application/json' },
            signal: AbortSignal.timeout(3000)
        });

        if (response.ok) {
            const data = await response.json();
            return data.disposable === 'true' || data.disposable === true;
        }

        return false;
    } catch (error) {
        console.warn('Disposable API check failed, using local database only:', error.message);
        return false;
    }
}

// Comprehensive list of disposable/temporary email domains
const DISPOSABLE_DOMAINS = new Set([
    // Popular temporary email services
    '10minutemail.com', '10minutemail.net', '20minutemail.com', '30minutemail.com',
    'guerrillamail.com', 'guerrillamail.net', 'guerrillamail.org', 'guerrillamail.biz',
    'sharklasers.com', 'grr.la', 'guerrillamailblock.com',
    'mailinator.com', 'mailinator.net', 'mailinator2.com', 'mailinator3.com',
    'temp-mail.org', 'temp-mail.io', 'temp-mail.de', 'tempmail.com', 'tempmail.net', 'tempmail.us',
    'throwaway.email', 'throwawaymail.com', 'trashmail.com', 'trashmail.net',
    'yopmail.com', 'yopmail.net', 'yopmail.fr',
    'maildrop.cc', 'maildrop.com',
    'getnada.com', 'nada.email',
    'mohmal.com', 'mohmal.in', 'mohmal.tech',
    'dispostable.com', 'fakeinbox.com', 'fakeinbox.net', 'fakemail.net',
    'disposablemail.com', 'disposable-email.com', 'disposableemail.com',
    'burnermail.io', 'burner.email',
    'mintemail.com', 'mintemail.net',
    'emailondeck.com', 'emailondeck.net',
    'mytemp.email', 'mytempmail.com', 'tempinbox.com',
    'incognitomail.com', 'incognitomail.net',
    'spamgourmet.com', 'spambox.us', 'spambox.info',
    'mailcatch.com', 'mailnesia.com', 'mailnesia.net',
    'mailpoof.com', 'mailforspam.com',
    'getairmail.com', 'airmail.com',
    'crazymailing.com', 'spamfree24.org', 'spamfree24.com',
    'anonbox.net', 'anonymbox.com',
    'deadaddress.com', 'deadfake.com',
    'inbox.lv', 'inboxbear.com',
    'emltmp.com', 'emlhub.com', 'emlpro.com',
    'guerillamail.de', 'pokemail.net',
    'proton.me', 'mail.tm', 'mail.gw',
    'minute-mail.com', 'mintemailnow.com',
    'spamcowboy.com', 'spamcowboy.net',
    'guerrillamailblock.com', 'spam4.me',
    'tempemail.com', 'tempmailaddress.com',
    'tempmail.ninja', 'tempmail.de',
    'temporaryemail.net', 'temporaryemail.us',
    'disposableinbox.com', 'disposable.com',
    'fakeemailgenerator.com', 'fakemailgenerator.com',
    'trbvm.com', 'haltospam.com', 'spambox.irishspringrealty.com',
    'bobmail.info', 'koszmail.pl', 'dingbone.com',
    'dropmail.me', 'fastmail.fm', 'spamgourmet.org',
    'mailexpire.com', 'mailhz.me', 'mailmoat.com',
    'mailmedo.com', 'mailme.ir', 'mailme.lv',
    'mailslite.com', 'mailslite.net', 'mailsac.com',
    'mailsnag.com', 'mailin8r.com', 'mailzi.ru',
    'no-spam.ws', 'nomail.xl.cx', 'nomail2me.com',
    'nospam.ze.tc', 'nospamfor.us', 'nospam4.us',
    'nowmymail.com', 'objectmail.com', 'obobbo.com',
    'oneoffemail.com', 'onewaymail.com', 'opentrash.com',
    'orangotango.ml', 'owlpic.com', 'rppkn.com',
    'pookmail.com', 'proxymail.eu', 'putthisinyourspamdatabase.com',
    'quickinbox.com', 'rcpt.at', 'reallymymail.com',
    'recursor.net', 'rtrtr.com', 'safaat.com',
    'safetymail.info', 'safetypost.de', 'sandelf.de',
    'saynotospams.com', 'selfdestructingmail.com', 'sendspamhere.com',
    'shortmail.net', 'sibmail.com', 'skeefmail.com',
    'slaskpost.se', 'slippery.email', 'smashmail.de',
    'snakemail.com', 'sneakemail.com', 'sofimail.com',
    'sofort-mail.de', 'sogetthis.com', 'soodonims.com',
    'spam.la', 'spam.su', 'spamail.de',
    'spamarrest.com', 'spambob.com', 'spambob.net',
    'spambog.com', 'spambog.de', 'spambog.ru',
    'spamcannon.com', 'spamcannon.net', 'spamcon.org',
    'spamcorptastic.com', 'spamday.com', 'spamex.com',
    'spamfree.eu', 'spamfree24.de', 'spamfree24.eu',
    'spamfree24.info', 'spamfree24.net', 'spamfree24.org',
    'spamgoes.in', 'spamherelots.com', 'spamhereplease.com',
    'spamhole.com', 'spamify.com', 'spaminator.de',
    'spamkill.info', 'spaml.com', 'spaml.de',
    'spammotel.com', 'spamobox.com', 'spamoff.de',
    'spamslicer.com', 'spamstack.net', 'spamthis.co.uk',
    'spamthisplease.com', 'spamtrail.com', 'speed.1s.fr',
    'supergreatmail.com', 'supermailer.jp', 'suremail.info',
    'talkinator.com', 'teewars.org', 'teleosaurs.xyz',
    'teleworm.com', 'teleworm.us', 'temp-email.com',
    'temp-mail.com', 'tempalias.com', 'tempemail.biz',
    'tempemail.co.za', 'tempemail.net', 'tempemailaddress.com',
    'tempemails.net', 'tempinbox.co.uk', 'tempinbox.org',
    'tempmail.co', 'tempmail.it', 'tempmail2.com',
    'tempmailaddress.com', 'tempmails.net', 'tempsky.com',
    'thankyou2010.com', 'thecloudindex.com', 'thisisnotmyrealemail.com',
    'throam.com', 'throwam.com', 'tilien.com',
    'tittbit.in', 'tmail.ws', 'tmailinator.com',
    'toiea.com', 'tradermail.info', 'trash-amil.com',
    'trash-mail.at', 'trash-mail.com', 'trash-mail.de',
    'trash2009.com', 'trashemail.de', 'trashemailaddress.com',
    'trashmail.at', 'trashmail.de', 'trashmail.me',
    'trashmail.org', 'trashmail.ws', 'trashmailer.com',
    'trashymail.com', 'trashymail.net', 'trbvn.com',
    'trialmail.de', 'trillianpro.com', 'twinmail.de',
    'tyldd.com', 'uggsrock.com', 'umail.net',
    'upliftnow.com', 'uplipht.com', 'uroid.com',
    'us.af', 'venompen.com', 'veryrealemail.com',
    'viditag.com', 'viewcastmedia.com', 'viewcastmedia.net',
    'viewcastmedia.org', 'vomoto.com', 'vpn.st',
    'vsimcard.com', 'vubby.com', 'wasteland.rfc822.org',
    'webemail.me', 'webm4il.info', 'wegwerfadresse.de',
    'wegwerfemail.com', 'wegwerfemail.de', 'wegwerfmail.de',
    'wegwerfmail.net', 'wegwerfmail.org', 'wh4f.org',
    'whatiaas.com', 'whatpaas.com', 'whyspam.me',
    'willselfdestruct.com', 'winemaven.info', 'wmail.cf',
    'xagloo.com', 'xemaps.com', 'xents.com',
    'xmaily.com', 'xoxy.net', 'yapped.net',
    'yanet.me', 'yaqp.com', 'yroid.com',
    'zippymail.info', 'zoemail.com', 'zoemail.net',
    'zoemail.org', 'zomg.info', 'mailtemp.net'
]);

async function checkMXRecords(domain: string): Promise<boolean> {
    try {
        // Use Cloudflare DNS-over-HTTPS
        const response = await fetch(`https://cloudflare-dns.com/dns-query?name=${domain}&type=MX`, {
            headers: { 'Accept': 'application/dns-json' },
            signal: AbortSignal.timeout(5000)
        });

        if (response.ok) {
            const data = await response.json();
            return data.Answer && data.Answer.length > 0;
        }

        return false;
    } catch (error) {
        console.warn('MX check failed:', error.message);
        return false;
    }
}

function isRoleBased(email: string): boolean {
    const roleBased = [
        'admin', 'administrator', 'info', 'support', 'sales',
        'contact', 'webmaster', 'hostmaster', 'postmaster',
        'noreply', 'no-reply', 'help', 'service', 'team'
    ];

    const localPart = email.split('@')[0]?.toLowerCase();
    return roleBased.includes(localPart);
}

async function performExternalValidation(email: string, apiKey: string): Promise<any> {
    // This is a placeholder for external API validation
    // Users can configure their preferred email validation service
    // Examples: hunter.io, zerobounce.net, isitarealemail.com
    
    // Example implementation for isitarealemail.com:
    try {
        const response = await fetch('https://isitarealemail.com/api/email/validate', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email }),
            signal: AbortSignal.timeout(5000)
        });

        if (response.ok) {
            const data = await response.json();
            return {
                available: true,
                valid: data.status === 'valid',
                smtp: data.smtp_check,
                details: data
            };
        }

        throw new Error('API validation failed');
    } catch (error) {
        throw new Error(`External validation error: ${error.message}`);
    }
}

function calculateEmailRiskLevel(hasMX: boolean, isDisposable: boolean): string {
    if (isDisposable) return 'high';
    if (!hasMX) return 'medium';
    return 'low';
}

function calculateEmailThreatScore(hasMX: boolean, isDisposable: boolean): number {
    let score = 0;
    
    if (isDisposable) score += 60;
    if (!hasMX) score += 40;
    
    return Math.min(score, 100);
}

function getEmailRecommendation(hasMX: boolean, isDisposable: boolean): string {
    if (isDisposable) {
        return 'Block or require additional verification - disposable email detected';
    }
    if (!hasMX) {
        return 'Email domain has no MX records - likely invalid';
    }
    return 'Email appears valid and deliverable';
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
