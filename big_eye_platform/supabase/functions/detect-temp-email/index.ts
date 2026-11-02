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

        // Extract domain from email
        const domain = email.split('@')[1]?.toLowerCase();
        if (!domain) {
            throw new Error('Invalid email format');
        }

        // Check against known temporary email domains
        const isTemporary = TEMP_EMAIL_DOMAINS.has(domain);
        const isFreemail = FREE_EMAIL_PROVIDERS.has(domain);
        
        // Try external API for additional verification
        let externalCheck = null;
        try {
            const response = await fetch(`https://disposable.debounce.io/?email=${encodeURIComponent(email)}`, {
                headers: { 'Accept': 'application/json' },
                signal: AbortSignal.timeout(3000) // 3 second timeout
            });
            
            if (response.ok) {
                const data = await response.json();
                externalCheck = {
                    disposable: data.disposable === 'true' || data.disposable === true,
                    service: 'debounce.io'
                };
            }
        } catch (error) {
            console.warn('External temp email API failed:', error.message);
        }

        const result = {
            email,
            domain,
            isTemporary: isTemporary || (externalCheck?.disposable || false),
            isFreemail,
            confidence: calculateConfidence(isTemporary, externalCheck),
            sources: {
                localDatabase: isTemporary,
                externalAPI: externalCheck
            },
            recommendation: isTemporary || externalCheck?.disposable 
                ? 'Block or require additional verification' 
                : 'Accept',
            riskLevel: (isTemporary || externalCheck?.disposable) ? 'high' : (isFreemail ? 'medium' : 'low')
        };

        // Track analytics (non-blocking)
        trackAnalytics(req, 'Temporary Email Detector', 'temp-email-detection', {
            email,
            domain,
            isTemporary: result.isTemporary,
            confidence: result.confidence
        }).catch(err => console.warn('Analytics tracking failed:', err));

        return new Response(JSON.stringify({ data: result }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Temporary email detection error:', error);

        const errorResponse = {
            error: {
                code: 'TEMP_EMAIL_CHECK_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function calculateConfidence(localMatch: boolean, externalCheck: any): number {
    if (localMatch && externalCheck?.disposable) return 95;
    if (localMatch || externalCheck?.disposable) return 85;
    if (!localMatch && externalCheck && !externalCheck.disposable) return 90;
    return 70; // Default confidence when only local check available
}

// Comprehensive list of known temporary/disposable email domains
const TEMP_EMAIL_DOMAINS = new Set([
    // Popular temporary email services
    '10minutemail.com', '10minutemail.net', '20minutemail.com',
    'guerrillamail.com', 'guerrillamail.net', 'guerrillamail.org', 'guerrillamail.biz',
    'sharklasers.com', 'grr.la', 'guerrillamailblock.com',
    'mailinator.com', 'mailinator.net', 'mailinator2.com',
    'temp-mail.org', 'temp-mail.io', 'tempmail.com', 'tempmail.net',
    'throwaway.email', 'throwam.com',
    'maildrop.cc', 'mailnesia.com', 'mintemail.com',
    'yopmail.com', 'yopmail.fr', 'yopmail.net',
    'trashmail.com', 'trashmail.net',
    'getnada.com', 'getairmail.com',
    'fakeinbox.com', 'fakemail.net',
    'dispostable.com', 'mohmal.com',
    'emailondeck.com', 'emailsensei.com',
    '33mail.com', 'mytemp.email',
    'tmail.ws', 'tmailinator.com',
    'armyspy.com', 'cuvox.de', 'dayrep.com',
    'einrot.com', 'fleckens.hu', 'gustr.com',
    'jourrapide.com', 'rhyta.com', 'superrito.com',
    'teleworm.us', 'klzlk.com',
    
    // Additional disposable domains
    'anonbox.net', 'anonymbox.com', 'beefmilk.com',
    'binkmail.com', 'bobmail.info', 'boxformail.in',
    'breakthru.com', 'bugmenot.com', 'bumpymail.com',
    'centermail.com', 'chammy.info', 'chogmail.com',
    'choicemail1.com', 'clixser.com', 'cmail.net',
    'cmail.org', 'cmail.com', 'coldemail.info',
    'cool.fr.nf', 'correo.blogos.net', 'cosmorph.com',
    'courriel.fr.nf', 'courrieltemporaire.com', 'cubiclink.com',
    'curryworld.de', 'cust.in', 'dacoolest.com',
    'dandikmail.com', 'deadaddress.com', 'deadfake.cf',
    'despam.it', 'devnullmail.com', 'dfgh.net',
    'digitalsanctuary.com', 'discardmail.com', 'discardmail.de',
    'disposableaddress.com', 'disposableemailaddresses.com', 'disposableinbox.com',
    'dispose.it', 'discard.email', 'disposeamail.com', 'disposemail.com',
    'dodgeit.com', 'dodgit.com', 'dodgit.org',
    'donemail.ru', 'dontreg.com', 'dontsendmespam.de',
    'drdrb.net', 'dump-email.info', 'dumpmail.de',
    'e4ward.com', 'email60.com', 'emailgo.de',
    'emailias.com', 'emaillime.com', 'emailmiser.com',
    'emailresort.com', 'emailtemporario.com.br', 'emailto.de',
    'emailwarden.com', 'emailx.at.hm', 'emailxfer.com',
    'emeil.in', 'emeil.ir', 'emz.net',
    'enterto.com', 'ephemail.net', 'etranquil.com',
    'evopo.com', 'explodemail.com', 'express.net.ua',
    'eyepaste.com', 'ez.lv', 'ezfill.com',
    'f4k.es', 'fakemail.fr', 'fakemailz.com',
    'fastacura.com', 'fastchevy.com', 'fastchrysler.com',
    'fastkawasaki.com', 'fastmazda.com', 'fastmitsubishi.com',
    'filzmail.com', 'fizmail.com', 'fr33mail.info',
    'frapmail.com', 'front14.org', 'fux0ringduh.com',
    'garliclife.com', 'gehensiemirnichtaufdensack.de', 'get2mail.fr',
    'getonemail.com', 'getsimple.com', 'ghosttexter.de',
    'girlsundertheinfluence.com', 'gishpuppy.com', 'godmail.dk',
    'goemailgo.com', 'gotmail.net', 'gotmail.org',
    'great-host.in', 'greensloth.com', 'gsrv.co.uk',
    'h.mintemail.com', 'h8s.org', 'hacccc.com',
    'haltospam.com', 'harakirimail.com', 'hat-geld.de',
    'hatespam.org', 'hidemail.de', 'hidzz.com',
    'hmamail.com', 'hopemail.biz', 'ieatspam.eu',
    'ieatspam.info', 'ieh-mail.de', 'ihateyoualot.info',
    'iheartspam.org', 'imails.info', 'inboxclean.com',
    'inboxclean.org', 'incognitomail.com', 'incognitomail.net',
    'incognitomail.org', 'infocom.zp.ua', 'instant-mail.de',
    'instantemailaddress.com', 'ip6.li', 'ipoo.org',
    'irish2me.com', 'iwi.net', 'jetable.com',
    'jetable.fr.nf', 'jetable.net', 'jetable.org',
    'jnxjn.com', 'jourrapide.com', 'jsrsolutions.com',
    'kasmail.com', 'kaspop.com', 'keepmymail.com',
    'killmail.com', 'killmail.net', 'kir.ch.tc',
    'klassmaster.com', 'koszmail.pl', 'kurzepost.de',
    'lawlita.com', 'letthemeatspam.com', 'lhsdv.com',
    'lifebyfood.com', 'link2mail.net', 'litedrop.com',
    'lol.ovpn.to', 'lortemail.dk', 'lr78.com',
    'lroid.com', 'lukop.dk', 'm4ilweb.info',
    'maboard.com', 'mail-temporaire.fr', 'mail.by',
    'mail.mezimages.net', 'mail.zp.ua', 'mail1a.de',
    'mail21.cc', 'mail2rss.org', 'mail333.com',
    'mail4trash.com', 'mailbidon.com', 'mailbiz.biz',
    'mailblocks.com', 'mailbucket.org', 'mailcat.biz',
    'mailcatch.com', 'mailde.de', 'mailde.info',
    'maildx.com', 'maileater.com', 'mailed.in',
    'mailed.ro', 'maileimer.de', 'mailexpire.com',
    'mailfa.tk', 'mailforspam.com', 'mailfreeonline.com',
    'mailfs.com', 'mailimate.com', 'mailin8r.com',
    'mailinater.com', 'mailinator.co.uk', 'mailinator.com',
    'mailinator.gq', 'mailinator.info', 'mailinator.net',
    'mailinator.org', 'mailinator.us', 'mailinator2.com',
    'mailincubator.com', 'mailismagic.com', 'mailmate.com',
    'mailme.gq', 'mailme.ir', 'mailme.lv',
    'mailme24.com', 'mailmetrash.com', 'mailmoat.com',
    'mailms.com', 'mailnull.com', 'mailorg.org',
    'mailpick.biz', 'mailquack.com', 'mailrock.biz',
    'mailsac.com', 'mailscrap.com', 'mailseal.de',
    'mailshell.com', 'mailsiphon.com', 'mailslapping.com',
    'mailslite.com', 'mailtemp.info', 'mailtome.de',
    'mailtothis.com', 'mailtrash.net', 'mailtv.net',
    'mailtv.tv', 'mailzilla.com', 'mailzilla.org',
    'makemetheking.com', 'manybrain.com', 'mbx.cc',
    'mega.zik.dj', 'meinspamschutz.de', 'meltmail.com',
    'messagebeamer.de', 'mezimages.net', 'ministry-of-silly-walks.de',
    'mintemail.com', 'misterpinball.de', 'moncourrier.fr.nf',
    'monemail.fr.nf', 'monmail.fr.nf', 'monumentmail.com',
    'mt2009.com', 'mx0.wwwnew.eu', 'mycleaninbox.net',
    'myemailboxy.com', 'mymail-in.net', 'mymailoasis.com',
    'mynetstore.de', 'mypacks.net', 'mypartyclip.de',
    'myphantomemail.com', 'myspaceinc.com', 'myspaceinc.net',
    'myspaceinc.org', 'myspacepimpedup.com', 'myspamless.com',
    'mytrashmail.com', 'nabuma.com', 'neomailbox.com',
    'nepwk.com', 'nervmich.net', 'nervtmich.net',
    'netmails.com', 'netmails.net', 'netzidiot.de',
    'neverbox.com', 'no-spam.ws', 'noblepioneer.com',
    'nobugmail.com', 'noclickemail.com', 'nogmailspam.info',
    'nomail.xl.cx', 'nomail2me.com', 'nomorespamemails.com',
    'nospam.ze.tc', 'nospam4.us', 'nospamfor.us',
    'nospammail.net', 'notmailinator.com', 'nowhere.org',
    'nowmymail.com', 'nurfuerspam.de', 'nus.edu.sg',
    'nwldx.com', 'objectmail.com', 'obobbo.com',
    'odnorazovoe.ru', 'oneoffemail.com', 'onewaymail.com',
    'online.ms', 'oopi.org', 'opayq.com',
    'ordinaryamerican.net', 'otherinbox.com', 'ovpn.to',
    'owlpic.com', 'pancakemail.com', 'paplease.com',
    'pimpedupmyspace.com', 'pjjkp.com', 'plexolan.de',
    'poczta.onet.pl', 'politikerclub.de', 'poofy.org',
    'pookmail.com', 'privacy.net', 'privatdemail.net',
    'proxymail.eu', 'prtnx.com', 'putthisinyourspamdatabase.com',
    'qq.com', 'quickinbox.com', 'quickmail.nl',
    'rcpt.at', 'reallymymail.com', 'realtyalerts.ca',
    'recode.me', 'recursor.net', 'recyclemail.dk',
    'regbypass.com', 'regbypass.comsafe-mail.net', 'rejectmail.com',
    'rklips.com', 'rmqkr.net', 's0ny.net',
    'safe-mail.net', 'safersignup.de', 'safetymail.info',
    'safetypost.de', 'sandelf.de', 'saynotospams.com',
    'schafmail.de', 'schrott-email.de', 'secretemail.de',
    'secure-mail.biz', 'secure-mail.cc', 'selfdestructingmail.com',
    'sendspamhere.com', 'shieldemail.com', 'shiftmail.com',
    'shitmail.me', 'shitmail.org', 'shitware.nl',
    'shortmail.net', 'sibmail.com', 'skeefmail.com',
    'slaskpost.se', 'slopsbox.com', 'smellfear.com',
    'snakemail.com', 'sneakemail.com', 'sneakmail.de',
    'snkmail.com', 'sofimail.com', 'solvemail.info',
    'sogetthis.com', 'soodonims.com', 'spam.la',
    'spam.su', 'spam4.me', 'spamavert.com',
    'spambob.com', 'spambob.net', 'spambob.org',
    'spambog.com', 'spambog.de', 'spambog.net',
    'spambog.ru', 'spambox.info', 'spambox.irishspringrealty.com',
    'spambox.us', 'spamcannon.com', 'spamcannon.net',
    'spamcero.com', 'spamcon.org', 'spamcorptastic.com',
    'spamcowboy.com', 'spamcowboy.net', 'spamcowboy.org',
    'spamday.com', 'spamex.com', 'spamfree.eu',
    'spamfree24.com', 'spamfree24.de', 'spamfree24.eu',
    'spamfree24.info', 'spamfree24.net', 'spamfree24.org',
    'spamgoes.in', 'spamgourmet.com', 'spamgourmet.net',
    'spamgourmet.org', 'spamherelots.com', 'spamhereplease.com',
    'spamhole.com', 'spamify.com', 'spaminator.de',
    'spamkill.info', 'spaml.com', 'spaml.de',
    'spammotel.com', 'spamobox.com', 'spamoff.de',
    'spamslicer.com', 'spamspot.com', 'spamstack.net',
    'spamthis.co.uk', 'spamthisplease.com', 'spamtrail.com',
    'speed.1s.fr', 'spoofmail.de', 'stuffmail.de',
    'super-auswahl.de', 'supergreatmail.com', 'supermailer.jp',
    'superrito.com', 'superstachel.de', 'suremail.info',
    'talkinator.com', 'teewars.org', 'teleworm.com',
    'temp-mail.com', 'temp-mail.de', 'temp-mail.org',
    'tempail.com', 'tempalias.com', 'tempe-mail.com',
    'tempemail.biz', 'tempemail.com', 'tempemail.net',
    'tempinbox.co.uk', 'tempinbox.com', 'tempmail.eu',
    'tempmail.it', 'tempmail2.com', 'tempmaildemo.com',
    'tempmailer.com', 'tempmailer.de', 'tempomail.fr',
    'temporarily.de', 'temporarioemail.com.br', 'temporaryemail.net',
    'temporaryemail.us', 'temporaryforwarding.com', 'temporaryinbox.com',
    'temporarymailaddress.com', 'thanksnospam.info', 'thankyou2010.com',
    'thc.st', 'thelimestones.com', 'thisisnotmyrealemail.com',
    'thismail.net', 'throwawayemailaddress.com', 'tilien.com',
    'tittbit.in', 'tmail.com', 'toomail.biz',
    'topranklist.de', 'tradermail.info', 'trash-amil.com',
    'trash-mail.at', 'trash-mail.com', 'trash-mail.de',
    'trash2009.com', 'trashemail.de', 'trashmail.at',
    'trashmail.com', 'trashmail.de', 'trashmail.me',
    'trashmail.net', 'trashmail.org', 'trashmail.ws',
    'trashmailer.com', 'trashymail.com', 'trashymail.net',
    'trialmail.de', 'trillianpro.com', 'twinmail.de',
    'tyldd.com', 'uggsrock.com', 'umail.net',
    'uroid.com', 'us.af', 'venompen.com',
    'veryrealemail.com', 'viditag.com', 'viewcastmedia.com',
    'viewcastmedia.net', 'viewcastmedia.org', 'vubby.com',
    'wasteland.rfc822.org', 'webemail.me', 'webm4il.info',
    'wegwerf-email-addressen.de', 'wegwerf-email-adressen.de', 'wegwerf-email.de',
    'wegwerf-email.net', 'wegwerf-emails.de', 'wegwerfadresse.de',
    'wegwerfemail.com', 'wegwerfemail.de', 'wegwerfemail.net',
    'wegwerfemail.org', 'wegwerfemailadresse.com', 'wegwerfmail.de',
    'wegwerfmail.info', 'wegwerfmail.net', 'wegwerfmail.org',
    'wetrainbayarea.com', 'wetrainbayarea.org', 'wh4f.org',
    'whatiaas.com', 'whatpaas.com', 'whyspam.me',
    'wilemail.com', 'willhackforfood.biz', 'willselfdestruct.com',
    'winemaven.info', 'wronghead.com', 'www.e4ward.com',
    'www.gishpuppy.com', 'www.mailinator.com', 'wwwnew.eu',
    'x.ip6.li', 'xagloo.com', 'xemaps.com',
    'xents.com', 'xmaily.com', 'xoxy.net',
    'yep.it', 'yogamaven.com', 'yopmail.com',
    'yopmail.fr', 'yopmail.net', 'ypmail.webarnak.fr.eu.org',
    'yuurok.com', 'z1p.biz', 'za.com',
    'zehnminuten.de', 'zehnminutenmail.de', 'zippymail.info',
    'zoaxe.com', 'zoemail.com', 'zoemail.net',
    'zoemail.org'
]);

// Known free email providers (not disposable, but useful to flag)
const FREE_EMAIL_PROVIDERS = new Set([
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
    'icloud.com', 'mail.com', 'zoho.com', 'protonmail.com', 'yandex.com',
    'gmx.com', 'mail.ru', 'inbox.com', 'live.com', 'msn.com',
    'yahoo.co.uk', 'yahoo.fr', 'yahoo.de', 'yahoo.es', 'yahoo.it',
    'googlemail.com', 'me.com', 'mac.com', 'qq.com', '163.com',
    '126.com', 'sina.com', 'sohu.com', 'yeah.net'
]);

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
