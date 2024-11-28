// src/components/volatility-analysis/control-panel/price-toggle.tsx
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { useVolatilityStore } from '@/stores/volatility-analysis/store'

export function PriceToggle() {
  const { showPrice, toggleShowPrice } = useVolatilityStore()

  return (
    <div className="flex items-center space-x-2">
      <Switch
        id="show-price"
        checked={showPrice}
        onCheckedChange={toggleShowPrice}
      />
      <Label htmlFor="show-price">Show Price</Label>
    </div>
  )
}
