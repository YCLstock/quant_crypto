// src/app/volatility-analysis/page.tsx
'use client'

import { useEffect } from 'react'
import { ErrorBoundary } from '@/components/ui/error-boundary'
import { ControlPanel } from '@/components/volatility-analysis/control-panel'
import { TrendChart } from '@/components/volatility-analysis/trend-chart'
import { Statistics } from '@/components/volatility-analysis/statistics'
import { Distribution } from '@/components/volatility-analysis/distribution'
import { useMarketAnalysisStore } from '@/stores/market-analysis/store'

export default function VolatilityAnalysisPage() {
  const initializeStore = useMarketAnalysisStore(state => state.fetchAnalysis)

  useEffect(() => {
    initializeStore()
  }, [initializeStore])

  return (
    <div className="container mx-auto p-6">
      <h1 className="mb-6 text-3xl font-bold">Volatility Analysis</h1>
      
      <div className="space-y-6">
        <ErrorBoundary>
          <ControlPanel />
        </ErrorBoundary>

        <div className="grid gap-6">
          <ErrorBoundary>
            <TrendChart />
          </ErrorBoundary>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <ErrorBoundary>
              <Statistics />
            </ErrorBoundary>
            <ErrorBoundary>
              <Distribution />
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </div>
  )
}