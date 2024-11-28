// src/components/volatility-analysis/statistics/metrics-display.tsx
interface MetricsDisplayProps {
    stats: {
      current: number
      points: number
      mean: number
      max: number
      min: number
    }
  }
  
  export function MetricsDisplay({ stats }: MetricsDisplayProps) {
    return (
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <p className="text-sm text-gray-500">Current Volatility</p>
          <p className="text-2xl font-bold">{stats.current.toFixed(2)}%</p>
          <p className="text-sm text-gray-500">
            ({stats.points.toFixed(2)} points)
          </p>
        </div>
        <div className="space-y-2">
          <div>
            <p className="text-sm text-gray-500">Average</p>
            <p className="text-lg font-semibold">{stats.mean.toFixed(2)}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Range</p>
            <p className="text-lg font-semibold">
              {stats.min.toFixed(2)}% - {stats.max.toFixed(2)}%
            </p>
          </div>
        </div>
      </div>
    )
  }
  