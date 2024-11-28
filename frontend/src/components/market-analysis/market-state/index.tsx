// src/components/market-analysis/market-state/index.tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useMarketData } from '@/hooks/use-market-data'
import { LoadingState } from '@/components/ui/loading-state'
import { ApiError, NoDataError } from '@/components/ui/api-error'
import { MarketScore } from './market-score'
import { StateIndicators } from './state-indicators'
import { TrendSummary } from './trend-summary'
import { useMarketAnalysisStore } from '@/stores/market-analysis/store'

export function MarketState() {
  const { selectedPair, selectedTimeframe } = useMarketAnalysisStore()
  const { 
    data: analysis, 
    isLoading, 
    isError, 
    error,
    refetch 
  } = useMarketData({
    symbol: selectedPair,
    timeframe: selectedTimeframe
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market State Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <LoadingState message="Loading market state..." />
        ) : isError ? (
          <ApiError error={error as Error} onRetry={refetch} />
        ) : !analysis ? (
          <NoDataError onRetry={refetch} />
        ) : (
          <div className="space-y-6">
            <MarketScore 
              score={analysis.market_score} 
              volatilityPercentile={analysis.volatility_percentile}
            />
            <StateIndicators 
              regime={analysis.regime_analysis}
              trend={analysis.trend_analysis}
              volatilityStats={analysis.volatility_stats}
            />
            <TrendSummary analysis={analysis} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}