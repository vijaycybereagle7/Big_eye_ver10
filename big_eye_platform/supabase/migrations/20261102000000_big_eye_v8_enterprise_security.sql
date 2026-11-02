-- Big Eye v8 Enterprise Security Ledger
-- Privacy-first persistence for normalized scans, incidents, and indicators.
-- Raw email content is intentionally not stored by the v8 edge function.

CREATE TABLE IF NOT EXISTS public.security_scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  content_hash TEXT NOT NULL,
  input_type TEXT NOT NULL DEFAULT 'email' CHECK (input_type IN ('email', 'header', 'url', 'attachment-hash', 'bulk')),
  sender_domain TEXT,
  overall_score INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
  risk_level TEXT NOT NULL CHECK (risk_level IN ('safe', 'low', 'medium', 'high', 'critical')),
  verdict TEXT NOT NULL CHECK (verdict IN ('ALLOW', 'REVIEW', 'QUARANTINE', 'BLOCK')),
  confidence INTEGER CHECK (confidence BETWEEN 0 AND 100),
  finding_count INTEGER NOT NULL DEFAULT 0 CHECK (finding_count >= 0),
  engines JSONB NOT NULL DEFAULT '[]'::jsonb,
  result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_security_scans_user_created
  ON public.security_scans(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_scans_risk
  ON public.security_scans(user_id, risk_level, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_scans_content_hash
  ON public.security_scans(content_hash);

CREATE TABLE IF NOT EXISTS public.security_incidents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  scan_id UUID REFERENCES public.security_scans(id) ON DELETE SET NULL,
  severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'investigating', 'contained', 'resolved', 'false_positive')),
  assigned_to UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  resolution_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_security_incidents_user_status
  ON public.security_incidents(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_incidents_scan
  ON public.security_incidents(scan_id);

CREATE TABLE IF NOT EXISTS public.security_watchlist (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  indicator_type TEXT NOT NULL CHECK (indicator_type IN ('email', 'domain', 'ip', 'url', 'sha256')),
  indicator_value TEXT NOT NULL,
  label TEXT,
  severity TEXT NOT NULL DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  notes TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, indicator_type, indicator_value)
);

CREATE INDEX IF NOT EXISTS idx_security_watchlist_user_active
  ON public.security_watchlist(user_id, is_active, created_at DESC);

CREATE OR REPLACE FUNCTION public.big_eye_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_security_scans_updated_at ON public.security_scans;
CREATE TRIGGER trg_security_scans_updated_at
  BEFORE UPDATE ON public.security_scans
  FOR EACH ROW EXECUTE FUNCTION public.big_eye_set_updated_at();

DROP TRIGGER IF EXISTS trg_security_incidents_updated_at ON public.security_incidents;
CREATE TRIGGER trg_security_incidents_updated_at
  BEFORE UPDATE ON public.security_incidents
  FOR EACH ROW EXECUTE FUNCTION public.big_eye_set_updated_at();

DROP TRIGGER IF EXISTS trg_security_watchlist_updated_at ON public.security_watchlist;
CREATE TRIGGER trg_security_watchlist_updated_at
  BEFORE UPDATE ON public.security_watchlist
  FOR EACH ROW EXECUTE FUNCTION public.big_eye_set_updated_at();

ALTER TABLE public.security_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.security_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.security_watchlist ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own security scans" ON public.security_scans;
CREATE POLICY "Users can view own security scans"
  ON public.security_scans FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own security scans" ON public.security_scans;
CREATE POLICY "Users can create own security scans"
  ON public.security_scans FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own security scans" ON public.security_scans;
CREATE POLICY "Users can update own security scans"
  ON public.security_scans FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view own security incidents" ON public.security_incidents;
CREATE POLICY "Users can view own security incidents"
  ON public.security_incidents FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own security incidents" ON public.security_incidents;
CREATE POLICY "Users can create own security incidents"
  ON public.security_incidents FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own security incidents" ON public.security_incidents;
CREATE POLICY "Users can update own security incidents"
  ON public.security_incidents FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own security watchlist" ON public.security_watchlist;
CREATE POLICY "Users can manage own security watchlist"
  ON public.security_watchlist FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

COMMENT ON TABLE public.security_scans IS 'Normalized Big Eye v8 scan ledger; result_json excludes raw message content.';
COMMENT ON TABLE public.security_incidents IS 'Incident queue generated from high and critical security scans.';
COMMENT ON TABLE public.security_watchlist IS 'Per-user indicators for continuous review across scans.';
