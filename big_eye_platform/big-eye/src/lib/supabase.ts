import { createClient } from '@supabase/supabase-js';

/** Configure Supabase through Vercel/Vite environment variables. */
const viteEnv = (import.meta.env || {}) as ImportMetaEnv;
export const supabaseUrl = viteEnv.VITE_SUPABASE_URL?.trim() || '';
export const supabaseAnonKey = viteEnv.VITE_SUPABASE_ANON_KEY?.trim() || '';
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

// Keep the client constructible for offline previews. Calls are guarded by
// isSupabaseConfigured in the analysis service, so this URL is never queried.
export const supabase = createClient(
  supabaseUrl || 'https://offline-preview.invalid',
  supabaseAnonKey || 'offline-preview-anon-key',
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  },
);
