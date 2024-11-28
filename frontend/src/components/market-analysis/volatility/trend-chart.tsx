// src/components/market-analysis/volatility/trend-chart.tsx

import { Line, LineChart, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface TrendChartProps {
  data: Array<{
    timestamp: string
    volatility: number
  }>
}

export function TrendChart({ data }: TrendChartProps) {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis 
            dataKey="timestamp"
            tickFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <YAxis 
            tickFormatter={(value) => `${value.toFixed(2)}%`}
          />
          <Tooltip
            labelFormatter={(label) => new Date(label).toLocaleString()}
            formatter={(value: number) => [`${value.toFixed(2)}%`, 'Volatility']}
          />
          <Line 
            type="monotone" 
            dataKey="volatility" 
            stroke="#8884d8" 
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}