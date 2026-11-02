# Big Eye v9 Enterprise build

## Production surface

- **Frontend:** `big_eye_platform/big-eye` (Vite + React, Vercel-ready)
- **Live backend:** `big_eye_platform/supabase/functions`
- **Database sync:** `big_eye_platform/supabase/migrations/20261102000000_big_eye_v8_enterprise_security.sql`
- **Provider secret names:** `big_eye_platform/supabase/PROVIDER_SECRETS.example`
- **Version:** see `../VERSION` (`9.0.0`)

## New operating tabs

1. **Command Center** — one-message six-engine analysis, weighted verdict,
   evidence, engine health, response playbook, local ledger, and JSON export.
2. **Malware Triage** — local SHA-256 hashing, dangerous extension/macro/
   double-extension detection, and optional VirusTotal hash-only lookup.
3. **Sync & Audit** — cloud scan ledger, incident queue, watchlist indicators,
   provider quota rows, and explicit offline/degraded/synchronized status.
4. **API Control Room** — provider catalog, configured/public state, wiring
   status, quota policy, data handling, and legal guardrails.

The catalog currently covers 26 documented provider contracts. “Cataloged” does
not mean “active”: a provider becomes live only after its secret is configured,
its response contract is tested, and its terms/data handling are approved.

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

## Vercel deployment: one Vite project from one GitHub repository

This repository intentionally contains the Vite frontend, Supabase source, and
archived research/backend material in one Git repository. Vercel must deploy
only the production Vite application; do not import the repository root as a
multi-service project.

On the Vercel import screen, choose **Import single project** beside:

`big_eye_platform/big-eye` → **Vite**

Use these project settings:

| Setting | Value |
| --- | --- |
| Root Directory | `big_eye_platform/big-eye` |
| Framework Preset | `Vite` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Required Vercel environment variables:

```text
VITE_SUPABASE_URL=https://nlqqbxnifyyvibxboufb.supabase.co
VITE_SUPABASE_ANON_KEY=<public-anon-key-from-Supabase-API-settings>
VITE_REQUIRE_AUTH=true
VITE_ALLOW_OFFLINE_FALLBACK=false
```

The anon key is safe for browser use; never add the Supabase service-role key
or provider API keys to Vercel. Provider secrets remain in Supabase Edge
Function secrets. After the first deployment, add the Vercel production URL to
Supabase Auth URL/redirect settings.

The Python folders, the unused Next.js shell, and Supabase Edge Functions are
not Vercel services for this deployment. Supabase functions remain deployed
from the Supabase dashboard/project.

## CLI deploy reference

```bash
cd big_eye_platform
supabase link --project-ref <your-project-ref>
supabase db push
supabase functions deploy analyze-email-security
supabase functions deploy scan-attachment-hash
supabase functions deploy get-provider-catalog
cd big-eye
npm install
npm run build
vercel --prod
```

Configure Vercel with the variables in `big_eye_platform/big-eye/.env.example`.
