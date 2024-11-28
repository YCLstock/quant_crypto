// src/components/market-analysis/volatility/index.tsx

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useVolatility } from '@/hooks/use-volatility'
import { LoadingState } from '@/components/ui/loading-state'
import { ApiError, NoDataError } from '@/components/ui/api-error'
import { TrendChart } from './trend-chart'
import { MetricsCard } from './metrics-card'
import { useMarketAnalysisStore } from '@/stores/market-analysis/store'

export function VolatilityAnalysis() {
  const { selectedPair, selectedTimeframe } = useMarketAnalysisStore()
  const {
    regimeData,
    historicalData,
    isLoading,
    isError,
    error,
    getCurrentRegime
  } = useVolatility({
    symbol: selectedPair,
    timeframe: selectedTimeframe,
    lookbackDays: 30
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Volatility Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <LoadingState message="Loading volatility data..." />
        ) : isError ? (
          <ApiError 
            error={error as Error} 
            onRetry={() => window.location.reload()}
          />
        ) : !regimeData || !historicalData ? (
          <NoDataError onRetry={() => window.location.reload()} />
        ) : (
          <div className="space-y-6">
            <TrendChart data={historicalData} />
            <MetricsCard 
              regime={getCurrentRegime()} 
              historicalData={historicalData}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}