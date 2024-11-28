// src/components/volatility-analysis/trend-chart/chart.tsx
import { useMemo } from 'react'
import {
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  TooltipProps
} from 'recharts'
import { useVolatilityData } from '@/hooks/use-volatility-data'
import { useVolatilityStore } from '@/stores/volatility-analysis/store'
import { LoadingState } from '@/components/ui/loading-state'
import { ChartTooltip } from './tooltip'
import type { VolatilityData, ChartData } from '@/types/market'

export function Chart() {
  const { data, isLoading } = useVolatilityData()
  const showPrice = useVolatilityStore(state => state.showPrice)

  const chartData: ChartData[] = useMemo(() => {
    if (!data) return []
    return data.map((item: VolatilityData) => ({
      timestamp: new Date(item.timestamp).getTime(),
      volatility: item.volatility,
      volatilityPoints: item.volatility * item.close_price / 100,
      price: showPrice ? item.close_price : undefined
    }))
  }, [data, showPrice])

  if (isLoading) {
    return <LoadingState />
  }

  return (
    <div className="h-[500px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart 
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="volatilityFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#82ca9d" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(time) => new Date(time).toLocaleDateString()}
            padding={{ left: 30, right: 30 }}
          />
          <YAxis 
            yAxisId="volatility"
            orientation="left"
            tickFormatter={(value) => `${value.toFixed(2)}%`}
            label={{ 
              value: 'Volatility (%)', 
              angle: -90, 
              position: 'insideLeft',
              style: { textAnchor: 'middle' }
            }}
          />
          {showPrice && (
            <YAxis
              yAxisId="price"
              orientation="right"
              domain={['auto', 'auto']}
              label={{ 
                value: 'Price ($)', 
                angle: 90, 
                position: 'insideRight',
                style: { textAnchor: 'middle' }
              }}
            />
          )}
          <Tooltip content={(props) => <ChartTooltip {...props} />} />
          <Area
            yAxisId="volatility"
            type="monotone"
            dataKey="volatility"
            stroke="#8884d8"
            fill="url(#volatilityFill)"
            strokeWidth={2}
          />
          {showPrice && (
            <Area
              yAxisId="price"
              type="monotone"
              dataKey="price"
              stroke="#82ca9d"
              fill="url(#priceFill)"
              strokeWidth={2}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}