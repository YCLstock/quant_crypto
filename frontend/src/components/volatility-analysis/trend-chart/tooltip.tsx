// src/components/volatility-analysis/trend-chart/tooltip.tsx
import { TooltipProps } from 'recharts'
import { VolatilityData, ChartData } from '@/types/market'

type CustomTooltipProps = TooltipProps<number, string> & {
  active?: boolean;
  payload?: Array<{
    value: number;
    payload: ChartData;
  }>;
}

export function ChartTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  
  return (
    <div className="rounded-lg border bg-white p-3 shadow-lg">
      <p className="mb-1 text-sm font-medium text-gray-500">
        {new Date(data.timestamp).toLocaleString()}
      </p>
      <div className="space-y-1">
        <p className="text-sm font-medium text-blue-600">
          Volatility: {data.volatility?.toFixed(2)}%
        </p>
        <p className="text-sm font-medium text-gray-600">
          Points: {data.volatilityPoints?.toFixed(2)}
        </p>
        {data.price && (
          <p className="text-sm font-medium text-green-600">
            Price: ${data.price.toFixed(2)}
          </p>
        )}
      </div>
    </div>
  );
}
