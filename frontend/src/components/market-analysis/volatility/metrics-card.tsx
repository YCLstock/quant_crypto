// src/components/market-analysis/volatility/metrics-card.tsx

import { VolatilityRegime, VolatilityData } from '@/hooks/use-volatility'

interface MetricsCardProps {
  regime: VolatilityRegime['current_regime'] | null
  historicalData: VolatilityData[]
}

export function MetricsCard({ regime, historicalData }: MetricsCardProps) {
  // 確保有數據才進行計算
  const currentVolatility = historicalData?.length > 0 
    ? historicalData[historicalData.length - 1]?.volatility ?? 0 
    : 0;
    
  const previousVolatility = historicalData?.length > 1 
    ? historicalData[historicalData.length - 2]?.volatility ?? 0 
    : 0;
    
  // 安全計算百分比變化
  const dailyChange = previousVolatility !== 0 
    ? ((currentVolatility - previousVolatility) / previousVolatility) * 100 
    : 0;

  // 安全計算高低點
  const volatilities = historicalData?.map(d => d.volatility).filter(v => v !== undefined) ?? [];
  const thirtyDayHigh = volatilities.length > 0 ? Math.max(...volatilities) : 0;
  const thirtyDayLow = volatilities.length > 0 ? Math.min(...volatilities) : 0;

  // 安全格式化數字
  const formatNumber = (value: number) => value?.toFixed(2) ?? '0.00';

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="space-y-2">
        <h4 className="text-sm font-medium">Current</h4>
        <p className="text-2xl font-bold">{formatNumber(currentVolatility)}%</p>
      </div>
      
      <div className="space-y-2">
        <h4 className="text-sm font-medium">Daily Change</h4>
        <p className={`text-2xl font-bold ${
          dailyChange > 0 ? 'text-green-500' : 'text-red-500'
        }`}>
          {formatNumber(dailyChange)}%
        </p>
      </div>
      
      <div className="space-y-2">
        <h4 className="text-sm font-medium">30D High</h4>
        <p className="text-2xl font-bold">{formatNumber(thirtyDayHigh)}%</p>
      </div>
      
      <div className="space-y-2">
        <h4 className="text-sm font-medium">30D Low</h4>
        <p className="text-2xl font-bold">{formatNumber(thirtyDayLow)}%</p>
      </div>

      {regime && (
        <div className="col-span-2 mt-4 rounded-lg bg-gray-50 p-4">
          <h4 className="text-sm font-medium">Current Regime</h4>
          <p className="mt-1 text-lg font-semibold">
            Volatility Level: {formatNumber(regime?.volatility ?? 0)}%
          </p>
          <p className="mt-1 text-sm text-gray-600">
            Mean Return: {formatNumber(regime?.characteristics?.avg_returns ?? 0)}%
          </p>
        </div>
      )}
    </div>
  )
}