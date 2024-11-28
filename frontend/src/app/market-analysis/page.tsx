// src/app/market-analysis/page.tsx
'use client'

import { useEffect } from 'react'
import { ErrorBoundary } from '@/components/ui/error-boundary'
import { ControlPanel } from '@/components/market-analysis/control-panel'
import { MarketState } from '@/components/market-analysis/market-state'
import { VolatilityAnalysis } from '@/components/market-analysis/volatility'
import { useMarketAnalysisStore } from '@/stores/market-analysis/store'

export default function MarketAnalysisPage() {
  // 初始化 store
  const initializeStore = useMarketAnalysisStore(state => state.fetchAnalysis)

  useEffect(() => {
    // 客戶端初始化
    initializeStore()
  }, [initializeStore])

  return (
    <div className="container mx-auto p-6">
      <h1 className="mb-6 text-3xl font-bold">Market Analysis</h1>
      
      <ErrorBoundary fallback={
        <div className="p-4 text-red-500">
          Something went wrong loading the analysis dashboard.
        </div>
      }>
        <div className="space-y-6">
          <ControlPanel />
          
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ErrorBoundary fallback={
              <div className="p-4 text-red-500">
                Error loading market state data.
              </div>
            }>
              <MarketState />
            </ErrorBoundary>
            
            <ErrorBoundary fallback={
              <div className="p-4 text-red-500">
                Error loading volatility analysis.
              </div>
            }>
              <VolatilityAnalysis />
            </ErrorBoundary>
          </div>
        </div>
      </ErrorBoundary>
    </div>
  )
}