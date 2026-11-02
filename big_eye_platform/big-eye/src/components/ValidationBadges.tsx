import { Shield, Fish, Zap, Search } from 'lucide-react';

interface ValidationBadgesProps {
  validated_by: string[];
  details?: Record<string, any>;
}

export function ValidationBadges({ validated_by, details }: ValidationBadgesProps) {
  if (!validated_by || validated_by.length === 0) {
    return null;
  }

  const getBadgeIcon = (source: string) => {
    if (source.toLowerCase().includes('google')) return <Shield className="w-4 h-4" />;
    if (source.toLowerCase().includes('phish')) return <Fish className="w-4 h-4" />;
    if (source.toLowerCase().includes('ipqs') || source.toLowerCase().includes('quality')) return <Zap className="w-4 h-4" />;
    if (source.toLowerCase().includes('url') || source.toLowerCase().includes('scan')) return <Search className="w-4 h-4" />;
    return <Shield className="w-4 h-4" />;
  };

  const getBadgeDetails = (source: string) => {
    if (!details) return null;
    
    const sourceLower = source.toLowerCase();
    if (sourceLower.includes('google') && details.google_safe_browsing) {
      return details.google_safe_browsing.types?.join(', ') || 'Threat detected';
    }
    if (sourceLower.includes('phish') && details.phishtank) {
      return details.phishtank.verified ? 'Verified phishing' : 'In database';
    }
    if (sourceLower.includes('ipqs') && details.ipqs) {
      return `Fraud score: ${details.ipqs.fraud_score}`;
    }
    return null;
  };

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      <div className="text-xs text-gray-400 w-full mb-1">Validated by:</div>
      {validated_by.map((source, index) => {
        const badgeDetails = getBadgeDetails(source);
        return (
          <div
            key={index}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-md text-red-400 text-xs font-medium hover:bg-red-500/20 transition-colors group relative"
            title={badgeDetails || source}
          >
            {getBadgeIcon(source)}
            <span>{source}</span>
            {badgeDetails && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                {badgeDetails}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
