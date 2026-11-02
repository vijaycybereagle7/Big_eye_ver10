const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 200, headers: corsHeaders });

  try {
    const { hash, filename, mimeType, size } = await req.json();
    if (typeof hash !== 'string' || !/^[a-f0-9]{64}$/i.test(hash)) throw new Error('A SHA-256 hash is required');

    const apiKey = Deno.env.get('VIRUSTOTAL_API_KEY');
    if (!apiKey) {
      return json({
        status: 'not-configured',
        message: 'No file bytes were uploaded. Configure VIRUSTOTAL_API_KEY to enable hash-only reputation lookups.',
        hash,
        filename,
        mimeType,
        size,
      });
    }

    const response = await fetch(`https://www.virustotal.com/api/v3/files/${hash}`, {
      headers: { 'x-apikey': apiKey, Accept: 'application/json' },
      signal: AbortSignal.timeout(8000),
    });
    if (response.status === 404) {
      return json({ status: 'unknown', message: 'Hash is not present in the configured VirusTotal corpus. Do not treat unknown as clean.', hash, filename });
    }
    if (!response.ok) throw new Error(`VirusTotal returned ${response.status}`);

    const body = await response.json();
    const stats = body.data?.attributes?.last_analysis_stats || {};
    const positives = Number(stats.malicious || 0) + Number(stats.suspicious || 0);
    return json({
      status: positives > 0 ? 'detections' : 'clean-in-provider',
      message: positives > 0 ? 'One or more engines reported this hash.' : 'No provider detections were returned; continue with organizational controls.',
      positives,
      total: Object.values(stats).reduce((sum: number, value: unknown) => sum + Number(value || 0), 0),
      stats,
      hash,
      filename,
    });
  } catch (error: any) {
    return json({ status: 'unavailable', message: error.message || 'Hash lookup failed' }, 400);
  }
});

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify({ data }), { status, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
}
