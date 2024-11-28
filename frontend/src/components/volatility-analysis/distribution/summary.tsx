// src/components/volatility-analysis/distribution/summary.tsx
interface SummaryProps {
    data: Array<{ volatility: number }>
  }
  
  export function Summary({ data }: SummaryProps) {
    const getPercentile = (value: number, arr: number[]) => {
      const sorted = [...arr].sort((a, b) => a - b)
      const index = sorted.findIndex(v => v >= value)
      return (index / sorted.length) * 100
    }
  
    const volatilities = data.map(d => d.volatility)
    const current = volatilities[volatilities.length - 1]
    const percentile = getPercentile(current, volatilities)
  
    return (
      <div className="rounded-lg bg-gray-50 p-4">
        <p className="text-sm text-gray-600">
          Current volatility ({current.toFixed(2)}%) is in the
          <span className="mx-1 font-bold">
            {percentile.toFixed(1)}th
          </span>
          percentile of historical values
        </p>
      </div>
    )
  }