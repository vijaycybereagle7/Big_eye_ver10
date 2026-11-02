interface ReputationGaugeProps {
  score: number; // 0-100
  size?: number;
  label?: string;
}

export function ReputationGauge({ score, size = 120, label = "Reputation Score" }: ReputationGaugeProps) {
  // Clamp score between 0-100
  const clampedScore = Math.max(0, Math.min(100, score));
  
  // Color-coded based on risk (inverse - higher score = safer)
  const getRiskColor = (score: number) => {
    if (score >= 76) return { color: '#10b981', label: 'Safe' }; // Green
    if (score >= 51) return { color: '#eab308', label: 'Low Risk' }; // Yellow
    if (score >= 26) return { color: '#f97316', label: 'Medium Risk' }; // Orange
    return { color: '#ef4444', label: 'High Risk' }; // Red
  };

  const { color, label: riskLabel } = getRiskColor(clampedScore);
  
  // Calculate SVG circle properties
  const strokeWidth = 10;
  const radius = (size / 2) - (strokeWidth / 2);
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#374151"
            strokeWidth={strokeWidth}
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-2xl font-bold" style={{ color }}>{clampedScore}</div>
          <div className="text-xs text-gray-400">{riskLabel}</div>
        </div>
      </div>
      <div className="text-sm font-medium text-gray-300">{label}</div>
    </div>
  );
}
