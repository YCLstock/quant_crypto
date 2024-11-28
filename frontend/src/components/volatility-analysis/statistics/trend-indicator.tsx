// src/components/volatility-analysis/statistics/trend-indicator.tsx
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface TrendIndicatorProps {
  data: Array<{ volatility: number; timestamp: string }>
}

export function TrendIndicator({ data }: TrendIndicatorProps) {
  const getTrend = () => {
    if (data.length < 2) return 'neutral'
    const recent = data.slice(-5)
    const first = recent[0].volatility
    const last = recent[recent.length - 1].volatility
    const change = ((last - first) / first) * 100

    if (change > 5) return 'up'
    if (change < -5) return 'down'
    return 'neutral'
  }

  const trend = getTrend()

  return (
    <div className="mt-4 rounded-lg bg-gray-50 p-4">
      <h4 className="mb-2 text-sm font-medium">Trend Analysis</h4>
      <div className="flex items-center gap-2">
        {trend === 'up' && (
          <>
            <TrendingUp className="h-5 w-5 text-green-500" />
            <span className="text-green-600">Increasing Volatility</span>
          </>
        )}
        {trend === 'down' && (
          <>
            <TrendingDown className="h-5 w-5 text-red-500" />
            <span className="text-red-600">Decreasing Volatility</span>
          </>
        )}
        {trend === 'neutral' && (
          <>
            <Minus className="h-5 w-5 text-yellow-500" />
            <span className="text-yellow-600">Stable Volatility</span>
          </>
        )}
      </div>
    </div>
  )
}