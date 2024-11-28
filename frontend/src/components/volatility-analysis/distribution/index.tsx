// src/components/volatility-analysis/distribution/index.tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Chart } from './chart'
import { Summary } from './summary'
import { useVolatilityData } from '@/hooks/use-volatility-data'
import { LoadingState } from '@/components/ui/loading-state'

export function Distribution() {
  const { data, isLoading } = useVolatilityData()

  if (isLoading) {
    return <LoadingState />
  }

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>Distribution Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <Chart data={data} />
          <Summary data={data} />
        </div>
      </CardContent>
    </Card>
  )
}