// src/components/volatility-analysis/control-panel/pair-selector.tsx
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/components/ui/select'
import { useMarketAnalysisStore } from '@/stores/market-analysis/store'
import type { TradingPair } from '@/types/market'

const TRADING_PAIRS = [
  { value: 'BTCUSDT', label: 'BTC/USDT' },
  { value: 'ETHUSDT', label: 'ETH/USDT' },
  { value: 'BNBUSDT', label: 'BNB/USDT' },
] as const

export function PairSelector() {
  const { selectedPair, setSelectedPair } = useMarketAnalysisStore()

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Trading Pair</label>
      <Select
        value={selectedPair}
        onValueChange={(value) => setSelectedPair(value as TradingPair)}
      >
        <SelectTrigger className="w-[180px] bg-white">
          {TRADING_PAIRS.find(p => p.value === selectedPair)?.label || 'Select Pair'}
        </SelectTrigger>
        <SelectContent>
          {TRADING_PAIRS.map((pair) => (
            <SelectItem key={pair.value} value={pair.value}>
              {pair.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
