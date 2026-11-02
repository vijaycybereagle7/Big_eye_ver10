-- Migration: add_user_admin_column
-- Created at: 1761745096

-- Add is_admin column to users table if not exists
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;;