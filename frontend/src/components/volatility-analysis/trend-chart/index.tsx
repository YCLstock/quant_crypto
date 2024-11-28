// src/components/volatility-analysis/trend-chart/index.tsx
import { Chart } from './chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function TrendChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Volatility Trend</CardTitle>
      </CardHeader>
      <CardContent className="h-[600px]">
        <Chart />
      </CardContent>
    </Card>
  )
}