# Big Eye remote Supabase deployment runbook

Project ref: `nlqqbxnifyyvibxboufb`

## Edge Functions

These v9 functions are already deployed:

- `analyze-email-security`
- `scan-attachment-hash`
- `get-provider-catalog`

Dashboard: https://supabase.com/dashboard/project/nlqqbxnifyyvibxboufb/functions

## Why `db push` stopped

The project already contains the older Big Eye tables and policies, but its
`supabase_migrations.schema_migrations` history does not contain the archived
migration versions. A normal `db push` therefore attempted to replay the old
`CREATE POLICY` statements and stopped at the first existing policy. This is a
safe stop; it did not apply the new v8 ledger migration.

## Recommended first-time repair

1. Open the SQL editor:

   https://supabase.com/dashboard/project/nlqqbxnifyyvibxboufb/sql/new

2. Review and execute the complete file:

   `supabase/migrations/20261102000000_big_eye_v8_enterprise_security.sql`

   This file creates only the v8 security ledger tables and policies. It does
   not store raw message content.

3. If future CLI migrations are required, reset/retrieve the database password
   from:

   https://supabase.com/dashboard/project/nlqqbxnifyyvibxboufb/settings/database

   Then run from this repository’s `big_eye_platform` directory:

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
