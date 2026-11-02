-- Migration: create_log_compression_tables
-- Created at: 1761724987

-- Create compressed logs table
CREATE TABLE IF NOT EXISTS public.user_analytics_compressed (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    compressed_data TEXT NOT NULL,
    compression_ratio DECIMAL(5,2),
    total_records INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Create archive table for old compressed logs
CREATE TABLE IF NOT EXISTS public.user_analytics_archive (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    compressed_data TEXT NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Enable RLS on both tables
ALTER TABLE public.user_analytics_compressed ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_analytics_archive ENABLE ROW LEVEL SECURITY;

-- Create policies for compressed logs
CREATE POLICY "Users view own compressed logs"
    ON public.user_analytics_compressed
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role full access to compressed logs"
    ON public.user_analytics_compressed
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Create policies for archive
CREATE POLICY "Users view own archived logs"
    ON public.user_analytics_archive
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role full access to archived logs"
    ON public.user_analytics_archive
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Create indexes for performance
CREATE INDEX idx_compressed_user_date ON public.user_analytics_compressed(user_id, date);
CREATE INDEX idx_compressed_date ON public.user_analytics_compressed(date);
CREATE INDEX idx_archive_user_date ON public.user_analytics_archive(user_id, date);
CREATE INDEX idx_archive_date ON public.user_analytics_archive(date);

-- Add comment
COMMENT ON TABLE public.user_analytics_compressed IS 'Stores compressed user analytics data per user per day';
COMMENT ON TABLE public.user_analytics_archive IS 'Archives compressed logs older than 30 days';;