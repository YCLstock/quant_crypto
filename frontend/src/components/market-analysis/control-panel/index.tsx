// src/components/market-analysis/control-panel/index.tsx
import { PairSelector } from './pair-selector'
import { TimeframeSelector } from './timeframe-selector'
import { useMarketAnalysisStore } from '@/stores/market-analysis/store'
import { LoadingState } from '@/components/ui/loading-state'

export function ControlPanel() {
  const { isLoading, error } = useMarketAnalysisStore()

  return (
    <div className="relative rounded-lg border p-4">
      <div className="flex items-start gap-4">
        <PairSelector />
        <TimeframeSelector />
        
        {isLoading && (
          <div className="ml-4">
            <LoadingState 
              variant="inline" 
              size="sm" 
              message="Updating..." 
            />
          </div>
        )}
      </div>
      
      {error && (
        <div className="mt-2 text-sm text-red-500">
          {error}
        </div>
      )}
    </div>
  )
}