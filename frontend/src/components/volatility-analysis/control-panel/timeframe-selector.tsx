// src/components/volatility-analysis/control-panel/timeframe-selector.tsx
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/components/ui/select'
import { useMarketAnalysisStore } from '@/stores/market-analysis/store'
import type { Timeframe } from '@/types/market'

const TIMEFRAMES = [
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' },
] as const

export function TimeframeSelector() {
  const { selectedTimeframe, setSelectedTimeframe } = useMarketAnalysisStore()

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Timeframe</label>
      <Select
        value={selectedTimeframe}
        onValueChange={(value) => setSelectedTimeframe(value as Timeframe)}
      >
        <SelectTrigger className="w-[180px] bg-white">
          {TIMEFRAMES.find(t => t.value === selectedTimeframe)?.label || 'Select Timeframe'}
        </SelectTrigger>
        <SelectContent>
          {TIMEFRAMES.map((timeframe) => (
            <SelectItem key={timeframe.value} value={timeframe.value}>
              {timeframe.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
