import { useEffect, useState } from 'react';
import { invokeEdgeFunction } from '../lib/analysis';
import { Activity, AlertTriangle, TrendingUp } from 'lucide-react';

interface APIUsage {
  api_name: string;
  reset_period: string;
  limit_total: number;
  today_usage: number;
  history: Array<{ date: string; request_count: number }>;
}

export function AdminDashboard() {
  const [usageData, setUsageData] = useState<APIUsage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAPIUsage();
    // Refresh every 30 seconds
    const interval = setInterval(fetchAPIUsage, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAPIUsage = async () => {
    try {
      const { data, error: invokeError } = await invokeEdgeFunction('get-api-usage');
      if (invokeError) throw invokeError;
      const result = data?.data || data;
      setUsageData(result?.usage || []);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch API usage:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getProgressPercentage = (usage: number, limit: number) => {
    return Math.round((usage / limit) * 100);
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 95) return 'bg-red-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getBorderColor = (percentage: number) => {
    if (percentage >= 95) return 'border-red-500';
    if (percentage >= 80) return 'border-yellow-500';
    return 'border-gray-700';
  };

  const getTimeUntilReset = (resetPeriod: string) => {
    const now = new Date();
    if (resetPeriod === 'daily') {
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 0, 0, 0);
      const hours = Math.floor((tomorrow.getTime() - now.getTime()) / (1000 * 60 * 60));
      return `${hours}h until reset`;
    } else {
      const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
      const days = Math.ceil((nextMonth.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      return `${days}d until reset`;
    }
  };

  const highUsageAPIs = usageData.filter(api => getProgressPercentage(api.today_usage, api.limit_total) >= 80);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-2 text-gray-400">
          <Activity className="w-5 h-5 animate-spin" />
          <span>Loading API usage data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-400">Failed to load API usage</h3>
            <p className="text-sm text-red-300 mt-1">{error}</p>
            <p className="text-xs text-gray-400 mt-2">
              Note: Admin access is required to view this dashboard
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">API Quota Dashboard</h2>
          <p className="text-gray-400 mt-1">Monitor external API usage and limits</p>
        </div>
        <button
          onClick={fetchAPIUsage}
          className="px-4 py-2 bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-400 hover:bg-purple-500/30 transition-colors flex items-center gap-2"
        >
          <Activity className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Alert Banner */}
      {highUsageAPIs.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-yellow-400">High Usage Alert</h3>
              <p className="text-sm text-gray-300 mt-1">
                {highUsageAPIs.length} API{highUsageAPIs.length > 1 ? 's have' : ' has'} exceeded 80% of quota: {' '}
                {highUsageAPIs.map(api => api.api_name).join(', ')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* API Usage Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {usageData.map((api) => {
          const percentage = getProgressPercentage(api.today_usage, api.limit_total);
          const progressColor = getProgressColor(percentage);
          const borderColor = getBorderColor(percentage);

          return (
            <div
              key={api.api_name}
              className={`bg-gray-800/50 border ${borderColor} rounded-lg p-4 hover:bg-gray-800/70 transition-colors`}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-white">{api.api_name}</h3>
                  <p className="text-xs text-gray-400 mt-1">
                    {api.reset_period === 'daily' ? 'Daily' : 'Monthly'} Limit
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-white">{api.today_usage}</div>
                  <div className="text-xs text-gray-400">/ {api.limit_total}</div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="relative w-full h-2 bg-gray-700 rounded-full overflow-hidden mb-3">
                <div
                  className={`absolute left-0 top-0 h-full ${progressColor} transition-all duration-500`}
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">{percentage}% used</span>
                <span className="text-gray-500">{getTimeUntilReset(api.reset_period)}</span>
              </div>

              {/* 7-day trend indicator */}
              {api.history && api.history.length > 1 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <TrendingUp className="w-3 h-3" />
                    <span>Last 7 days: {api.history.length} data points</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {usageData.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No API usage data available yet</p>
          <p className="text-sm mt-1">Usage data will appear once external APIs are called</p>
        </div>
      )}
    </div>
  );
}
