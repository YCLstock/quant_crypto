// src/components/market-analysis/market-state/state-chart.tsx
// import { useMarketAnalysisStore } from '@/stores/market-analysis/store'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

export function StateChart() {
  // 這裡需要從API獲取狀態轉換歷史數據,暫時使用模擬數據
  const data = [
    { timestamp: '2024-01-01', score: 75 },
    { timestamp: '2024-01-02', score: 82 },
    { timestamp: '2024-01-03', score: 78 },
    { timestamp: '2024-01-04', score: 85 },
    { timestamp: '2024-01-05', score: 80 },
  ]

  return (
    <div className="h-[200px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <XAxis dataKey="timestamp" />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#8884d8"
            fill="#8884d8"
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}