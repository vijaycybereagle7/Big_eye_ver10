-- Migration: enable_rls_and_security_policies
-- Created at: 1761721737

-- Step 1: Enable Row Level Security on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_cache ENABLE ROW LEVEL SECURITY;

-- Step 2: Create security policies for users table
CREATE POLICY "Users can view own profile" ON public.users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.users
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Step 3: Create security policies for scans table
CREATE POLICY "Users can view own scans" ON public.scans
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own scans" ON public.scans
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scans" ON public.scans
  FOR UPDATE USING (auth.uid() = user_id);

-- Step 4: Create security policies for api_cache table (public read, service role write)
CREATE POLICY "Public can read api cache" ON public.api_cache
  FOR SELECT USING (true);

CREATE POLICY "Service role can manage cache" ON public.api_cache
  FOR ALL USING (true);

-- Step 5: Add new columns to users table for advanced tracking
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS ip_address INET;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS device_info JSONB;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS device_name VARCHAR(255);
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS location VARCHAR(255);
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS password_strength INTEGER;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS browser VARCHAR(255);
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS os VARCHAR(255);

-- Step 6: Create user_analytics table for comprehensive usage tracking
CREATE TABLE IF NOT EXISTS public.user_analytics (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  tool_name VARCHAR(255) NOT NULL,
  analysis_type VARCHAR(255),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  success BOOLEAN DEFAULT true,
  additional_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on user_analytics table
ALTER TABLE public.user_analytics ENABLE ROW LEVEL SECURITY;

-- Create security policies for user_analytics
CREATE POLICY "Users can view own analytics" ON public.user_analytics
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analytics" ON public.user_analytics
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Step 7: Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_user_analytics_user_id ON public.user_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_analytics_tool_name ON public.user_analytics(tool_name);
CREATE INDEX IF NOT EXISTS idx_user_analytics_timestamp ON public.user_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON public.scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_tool_type ON public.scans(tool_type);
CREATE INDEX IF NOT EXISTS idx_api_cache_expires_at ON public.api_cache(expires_at);;