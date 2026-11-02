-- Migration: enhance_scans_table_reputation
-- Created at: 1761745102

-- Enhance scans table with reputation scoring
ALTER TABLE public.scans
ADD COLUMN IF NOT EXISTS reputation_score INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS threat_types TEXT[] DEFAULT NULL,
ADD COLUMN IF NOT EXISTS validated_by TEXT[] DEFAULT NULL;;