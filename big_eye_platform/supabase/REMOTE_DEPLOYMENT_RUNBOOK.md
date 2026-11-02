# Big Eye remote Supabase deployment runbook

Project ref: `nlqqbxnifyyvibxboufb`

Current status: the v8 ledger SQL has been executed successfully in the hosted
Supabase SQL Editor. The three cloud tables are reachable, and the deployed
Edge Functions have passed a live smoke test.

## Edge Functions

These v9 functions are already deployed:

- `analyze-email-security`
- `scan-attachment-hash`
- `get-provider-catalog`

Dashboard: https://supabase.com/dashboard/project/nlqqbxnifyyvibxboufb/functions

## Why the original `db push` stopped

The project already contains the older Big Eye tables and policies, but its
`supabase_migrations.schema_migrations` history does not contain the archived
migration versions. A normal `db push` therefore attempted to replay the old
`CREATE POLICY` statements and stopped at the first existing policy. This was a
safe stop. The v8 ledger migration was subsequently executed successfully in
the SQL Editor.

## Completed v8 schema deployment

The following tables are now present and queryable through PostgREST (subject
to their row-level security policies):

- `security_scans`
- `security_incidents`
- `security_watchlist`

The source migration remains at:

`supabase/migrations/20261102000000_big_eye_v8_enterprise_security.sql`

It creates only the v8 security ledger tables and policies and does not store
raw message content.

## Optional migration-history repair

Because the SQL was applied manually, the Supabase CLI migration ledger still
does not know that the archived local migration files were applied. This does
not affect the running application or the deployed functions. It only matters
if you later need to use `supabase db push` against this existing project.

If future CLI migrations are required, reset/retrieve the database password
from:

   https://supabase.com/dashboard/project/nlqqbxnifyyvibxboufb/settings/database

Then run from this repository’s `big_eye_platform` directory, after confirming
the legacy schema already exists:

```powershell
$env:SUPABASE_DB_PASSWORD = "<database-password>"
npx supabase link --project-ref nlqqbxnifyyvibxboufb
npx supabase migration repair --remote=nlqqbxnifyyvibxboufb --status applied `
  1761721737 1761724987 1761745085 1761745096 1761745102 1761745105 20261102000000
npx supabase db push --remote=nlqqbxnifyyvibxboufb --yes
Remove-Item Env:SUPABASE_DB_PASSWORD
```

Only mark the legacy versions as applied after confirming the pre-existing
tables/policies are present in the project. Never commit the password.

## Provider secrets

The provider catalog reports secret presence without exposing values. Configure
optional providers from `PROVIDER_SECRETS.example` using the Supabase dashboard
or `npx supabase secrets set`. Keep provider keys in Edge Function secrets,
never in Vite variables or GitHub.
