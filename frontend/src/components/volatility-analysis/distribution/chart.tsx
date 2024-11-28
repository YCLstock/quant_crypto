// src/components/volatility-analysis/distribution/chart.tsx
import { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface DistributionChartProps {
  data: Array<{ volatility: number }>
}

export function Chart({ data }: DistributionChartProps) {
  const distributionData = useMemo(() => {
    const volatilities = data.map(d => d.volatility)
    const min = Math.min(...volatilities)
    const max = Math.max(...volatilities)
    const range = max - min
    const binCount = 10
    const binSize = range / binCount

    // 創建分布區間
    const bins = Array.from({ length: binCount }, (_, i) => ({
      start: min + i * binSize,
      end: min + (i + 1) * binSize,
      count: 0,
    }))

    // 計算每個區間的數量
    volatilities.forEach(v => {
      const binIndex = Math.min(
        Math.floor((v - min) / binSize),
        binCount - 1
      )
      bins[binIndex].count++
    })

    return bins.map(bin => ({
      range: `${bin.start.toFixed(1)}-${bin.end.toFixed(1)}`,
      count: bin.count,
    }))
  }, [data])

  return (
    <div className="h-[200px] w-full">
      <ResponsiveContainer>
        <BarChart data={distributionData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="range" 
            tick={{ fontSize: 12 }}
            interval={1}
            angle={-45}
            textAnchor="end"
          />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
