// src/components/market-analysis/market-state/state-indicators.tsx
import { RegimeAnalysis, TrendAnalysis } from '@/types/market'
import { ArrowUp, ArrowDown, ArrowRight, AlertTriangle } from 'lucide-react'

interface StateIndicatorsProps {
  regime: RegimeAnalysis;
  trend: TrendAnalysis;
  volatilityStats?: {
    current: number;
    mean: number;
  };
}

export function StateIndicators({ regime, trend, volatilityStats }: StateIndicatorsProps) {
  // 根據regime確定狀態圖標和顏色
  const getRegimeIcon = (regime: string) => {
    switch (regime) {
      case 'Extremely High':
      case 'High':
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      case 'Low':
      case 'Extremely Low':
        return <AlertTriangle className="h-5 w-5 text-blue-500" />
      default:
        return <AlertTriangle className="h-5 w-5 text-green-500" />
    }
  }

  // 根據trend確定趨勢圖標
  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'Uptrend':
        return <ArrowUp className="h-5 w-5 text-green-500" />
      case 'Downtrend':
        return <ArrowDown className="h-5 w-5 text-red-500" />
      default:
        return <ArrowRight className="h-5 w-5 text-yellow-500" />
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="flex items-center gap-2 rounded-lg border p-4">
        {getRegimeIcon(regime.regime)}
        <div>
          <p className="text-sm font-medium">Volatility Regime</p>
          <p className="text-lg font-bold">{regime.regime}</p>
          <p className="text-xs text-muted-foreground">
            {volatilityStats && (
              <>Current: {volatilityStats.current.toFixed(2)}% <br/></>
            )}
            {regime.percentile.toFixed(1)}th percentile
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-lg border p-4">
        {getTrendIcon(trend.direction)}
        <div>
          <p className="text-sm font-medium">Trend Direction</p>
          <p className="text-lg font-bold">{trend.direction}</p>
          <p className="text-xs text-muted-foreground">
            Strength: {trend.strength.toFixed(1)}%<br/>
            Duration: {trend.duration} periods
          </p>
        </div>
      </div>
    </div>
  )
}