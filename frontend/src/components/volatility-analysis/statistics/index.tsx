// src/components/volatility-analysis/statistics/index.tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { MetricsDisplay } from './metrics-display'
import { TrendIndicator } from './trend-indicator'
import { useVolatilityData } from '@/hooks/use-volatility-data'
import { LoadingState } from '@/components/ui/loading-state'
import { VolatilityData } from '@/types/market'
export function Statistics() {
  const { data, isLoading } = useVolatilityData()

  if (isLoading) {
    return <LoadingState />
  }

  // 計算統計數據
  const current = data?.[data.length - 1] ?? { volatility: 0, close_price: 0 }
  const volatilities = data?.map((d: VolatilityData) => d.volatility) ?? []
  const stats = {
    current: current.volatility,
    points: (current.volatility * current.close_price) / 100,
    mean: volatilities.reduce((a: number, b: number) => a + b, 0) / volatilities.length,
    max: Math.max(...volatilities),
    min: Math.min(...volatilities)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <MetricsDisplay stats={stats} />
          <TrendIndicator data={data} />
        </div>
      </CardContent>
    </Card>
  )
}