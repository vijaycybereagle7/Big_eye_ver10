import { SupabaseClient } from 'https://esm.sh/@supabase/supabase-js@2';

export interface APIQuota {
  name: string;
  dailyLimit?: number;
  monthlyLimit?: number;
}

export const API_QUOTAS: Record<string, APIQuota> = {
  google_safe_browsing: { name: 'Google Safe Browsing', dailyLimit: 10000 },
  phishtank: { name: 'PhishTank', dailyLimit: 5000 },
  ipqs: { name: 'IPQualityScore', monthlyLimit: 5000 },
  quick_email: { name: 'Quick Email Verification', monthlyLimit: 3000 },
  urlscan: { name: 'URLScan.io', dailyLimit: 100 }
};

export async function trackAPIUsage(
  supabase: SupabaseClient,
  apiName: string,
  incrementBy: number = 1
): Promise<boolean> {
  const quota = API_QUOTAS[apiName];
  if (!quota) return true;

  const today = new Date().toISOString().split('T')[0];
  const resetPeriod = quota.dailyLimit ? 'daily' : 'monthly';
  const limitTotal = quota.dailyLimit || quota.monthlyLimit || 0;

  try {
    // Check current usage
    const { data: existing, error: fetchError } = await supabase
      .from('api_usage_tracking')
      .select('request_count')
      .eq('api_name', apiName)
      .eq('date', today)
      .single();

    if (fetchError && fetchError.code !== 'PGRST116') {
      console.error('Error fetching API usage:', fetchError);
      return true; // Allow on error
    }

    const currentCount = existing?.request_count || 0;

    // Check if over quota
    if (currentCount >= limitTotal) {
      console.warn(`API quota exceeded for ${apiName}: ${currentCount}/${limitTotal}`);
      return false;
    }

    // Upsert usage
    const { error: upsertError } = await supabase
      .from('api_usage_tracking')
      .upsert({
        api_name: apiName,
        date: today,
        request_count: currentCount + incrementBy,
        reset_period: resetPeriod,
        limit_total: limitTotal,
        updated_at: new Date().toISOString()
      }, {
        onConflict: 'api_name,date',
        ignoreDuplicates: false
      });

    if (upsertError) {
      console.error('Error tracking API usage:', upsertError);
    }

    return true;
  } catch (error) {
    console.error('Exception in trackAPIUsage:', error);
    return true; // Allow on exception
  }
}
