// src/components/volatility-analysis/control-panel/index.tsx
import { PairSelector } from './pair-selector'
import { TimeframeSelector } from './timeframe-selector'
import { PriceToggle } from './price-toggle'
import { useVolatilityStore } from '@/stores/volatility-analysis/store'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

export function ControlPanel() {
  const { showPrice, toggleShowPrice } = useVolatilityStore()

  return (
    <div className="rounded-lg border p-4 bg-white shadow-sm">
      <div className="flex flex-wrap items-start gap-6">
        <PairSelector />
        <TimeframeSelector />
        <div className="flex items-center space-x-2">
          <Switch
            id="show-price"
            checked={showPrice}
            onCheckedChange={toggleShowPrice}
          />
          <Label htmlFor="show-price">Show Price</Label>
        </div>
      </div>
    </div>
  )
}