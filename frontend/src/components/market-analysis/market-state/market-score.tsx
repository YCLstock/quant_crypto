// src/components/market-analysis/market-state/market-score.tsx
interface MarketScoreProps {
  score: number;
  volatilityPercentile?: number | null;
}

export function MarketScore({ score, volatilityPercentile }: MarketScoreProps) {
  // 根據分數確定顏色
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-blue-500'
    if (score >= 40) return 'text-yellow-500'
    return 'text-red-500'
  }

  // 根據分數提供評估
  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Strong'
    if (score >= 60) return 'Moderate'
    if (score >= 40) return 'Neutral'
    return 'Weak'
  }

  return (
    <div className="text-center">
      <h3 className="text-lg font-medium text-muted-foreground">Market Score</h3>
      <p className={`text-4xl font-bold ${getScoreColor(score)}`}>
        {score.toFixed(1)}
      </p>
      <p className="mt-1 text-sm text-muted-foreground">
        {getScoreLabel(score)}
        {volatilityPercentile && (
          <span className="ml-2">
            (Vol: {volatilityPercentile.toFixed(1)}th percentile)
          </span>
        )}
      </p>
    </div>
  )
}