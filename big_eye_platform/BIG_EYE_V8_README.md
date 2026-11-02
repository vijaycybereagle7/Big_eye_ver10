# Big Eye v8 Enterprise build

## Production surface

- **Frontend:** `big_eye_platform/big-eye` (Vite + React, Vercel-ready)
- **Live backend:** `big_eye_platform/supabase/functions`
- **Database sync:** `big_eye_platform/supabase/migrations/20261102000000_big_eye_v8_enterprise_security.sql`
- **Version:** see `../VERSION` (`8.0.0`)

## New operating tabs

1. **Command Center** — one-message six-engine analysis, weighted verdict,
   evidence, engine health, response playbook, local ledger, and JSON export.
2. **Malware Triage** — local SHA-256 hashing, dangerous extension/macro/
   double-extension detection, and optional VirusTotal hash-only lookup.
3. **Sync & Audit** — cloud scan ledger, incident queue, watchlist indicators,
   provider quota rows, and explicit offline/degraded/synchronized status.

## Safety and deployment behavior

- No Supabase URL or key is embedded in the frontend source.
- With no `VITE_SUPABASE_*` variables, the application runs a deterministic
  offline preview. It stores only local browser history and never claims live
  reputation data.
- With Supabase configured, the frontend invokes Edge Functions and the v8
  analysis function stores a content hash plus normalized result. Raw email
  content is not written to `security_scans`.
- Set `VITE_REQUIRE_AUTH=true` in production. Keep `VITE_ALLOW_OFFLINE_FALLBACK`
  enabled for previews and set it to `false` for strict live-only behavior.
- Provider secrets (`SUPABASE_SERVICE_ROLE_KEY`, `VIRUSTOTAL_API_KEY`,
  `ABUSEIPDB_API_KEY`, etc.) belong only in Supabase Edge Function secrets.

## Deploy

```bash
cd big_eye_platform
supabase link --project-ref <your-project-ref>
supabase db push
supabase functions deploy analyze-email-security
supabase functions deploy scan-attachment-hash
cd big-eye
npm install
npm run build
vercel --prod
```

Configure Vercel with the variables in `big_eye_platform/big-eye/.env.example`.
