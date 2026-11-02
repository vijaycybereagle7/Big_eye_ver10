# Big Eye changelog

## 8.0.0 - 2026-11-02

- Added a Security Operations Command Center with six-engine scoring and response playbooks.
- Added privacy-preserving attachment triage with browser SHA-256 hashing and optional VirusTotal lookup.
- Added Sync & Audit Center for scan ledger, incident queue, watchlist, and provider quota visibility.
- Added `analyze-email-security` and `scan-attachment-hash` Supabase Edge Functions.
- Added idempotent Supabase v8 migration for `security_scans`, `security_incidents`, and `security_watchlist` with RLS.
- Removed embedded Supabase credentials; Vercel environment variables are now required for live mode.
- Added safe offline preview fallback so Vercel previews remain testable before backend configuration.
- Normalized the existing tabs through the same live/offline invocation layer and removed forced auth in preview mode.
