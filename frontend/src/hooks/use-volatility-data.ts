// src/hooks/use-volatility-data.ts
import { useQuery } from '@tanstack/react-query'
import { useMarketAnalysisStore } from '@/stores/market-analysis/store'
import { marketAnalysisApi } from '@/services/market-analysis/api'
import type { VolatilityData } from '@/types/market'

export function useVolatilityData() {
  const { selectedPair, selectedTimeframe } = useMarketAnalysisStore()

  return useQuery<VolatilityData[], Error>({  // 明確指定返回類型和錯誤類型
    queryKey: ['volatility-history', selectedPair, selectedTimeframe],
    queryFn: async () => {
      const response = await marketAnalysisApi.getVolatilityHistory(
        selectedPair,
        selectedTimeframe,
        30
      )
      
      return response.sort((a: VolatilityData, b: VolatilityData) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      )
    },
    refetchInterval: 60000,
    staleTime: 30000,
    select: (data: VolatilityData[]) => {  // 明確指定參數類型
      return data.map((item: VolatilityData) => ({  // 明確指定參數類型
        ...item,
        volatility: Number(item.volatility),
        close_price: Number(item.close_price),
        timestamp: new Date(item.timestamp).toISOString()
      }))
    }
  })
}