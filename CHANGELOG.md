# Big Eye changelog

## 9.0.0 - 2026-11-02

- Added the API Control Room tab with a governed catalog of threat-intelligence,
  email, URL, domain, network, and mailbox provider contracts.
- Added secret-presence status through `get-provider-catalog`; provider secrets
  and live responses are never exposed to the browser.
- Added explicit quota, data-handling, attribution, and legal-use guardrails for
  every cataloged provider.
- Added Supabase deployment configuration for the provider catalog function.
- Fixed the Python threat-intelligence manager so subset lookups preserve the
  correct provider-to-result mapping.

## 8.0.0 - 2026-11-02

- Added a Security Operations Command Center with six-engine scoring and response playbooks.
- Added privacy-preserving attachment triage with browser SHA-256 hashing and optional VirusTotal lookup.
- Added Sync & Audit Center for scan ledger, incident queue, watchlist, and provider quota visibility.
- Added `analyze-email-security` and `scan-attachment-hash` Supabase Edge Functions.
- Added idempotent Supabase v8 migration for `security_scans`, `security_incidents`, and `security_watchlist` with RLS.
- Removed embedded Supabase credentials; Vercel environment variables are now required for live mode.
- Added safe offline preview fallback so Vercel previews remain testable before backend configuration.
- Normalized the existing tabs through the same live/offline invocation layer and removed forced auth in preview mode.
