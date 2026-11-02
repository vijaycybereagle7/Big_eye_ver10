-- Migration: create_api_usage_tracking_table
-- Created at: 1761745105

-- Create API usage tracking table
CREATE TABLE IF NOT EXISTS public.api_usage_tracking (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_name TEXT NOT NULL,
  endpoint TEXT,
  request_count INTEGER DEFAULT 1,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  reset_period TEXT NOT NULL,
  limit_total INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique index for efficient querying
CREATE UNIQUE INDEX IF NOT EXISTS idx_api_usage_tracking 
ON public.api_usage_tracking(api_name, date);

-- Enable RLS
ALTER TABLE public.api_usage_tracking ENABLE ROW LEVEL SECURITY;

-- Policy: Admin users can view API usage
CREATE POLICY "Admins can view API usage"
ON public.api_usage_tracking FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.users 
    WHERE users.id = auth.uid() 
    AND users.is_admin = true
  )
);;