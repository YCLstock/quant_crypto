// src/components/market-analysis/market-state/trend-summary.tsx
import { MarketAnalysis } from '@/types/market'

interface TrendSummaryProps {
  analysis: MarketAnalysis
}

export function TrendSummary({ analysis }: TrendSummaryProps) {
  const { trend_analysis: trend, regime_analysis: regime, volatility_stats: stats } = analysis

  return (
    <div className="rounded-lg border p-4">
      <h4 className="mb-2 font-medium">Market Summary</h4>
      <div className="space-y-2 text-sm">
        <p>
          Market is currently in a{' '}
          <span className="font-medium">{trend.direction}</span> with{' '}
          <span className="font-medium">{trend.strength.toFixed(1)}%</span> strength
          and has maintained this trend for{' '}
          <span className="font-medium">{trend.duration}</span> periods.
        </p>
        <p>
          Volatility is{' '}
          <span className="font-medium">{regime.regime.toLowerCase()}</span>{' '}
          at the{' '}
          <span className="font-medium">{regime.percentile.toFixed(1)}th</span>{' '}
          percentile
          {stats && (
            <> (current: {stats.current.toFixed(2)}%, avg: {stats.mean.toFixed(2)}%)</>
          )}
        </p>
        <p>
          Price change over trend duration:{' '}
          <span className={`font-medium ${
            trend.price_change_pct >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {trend.price_change_pct.toFixed(1)}%
          </span>
        </p>
      </div>
    </div>
  )
}