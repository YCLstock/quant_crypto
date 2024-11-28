// src/hooks/use-market-data.ts
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/axios-instance'
import type { MarketAnalysis, Timeframe, TradingPair } from '@/types/market'

interface UseMarketDataProps {
  symbol: TradingPair
  timeframe: Timeframe
  enabled?: boolean
}

interface UseMarketDataReturn {
  data: MarketAnalysis | null
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => Promise<void>
  prefetchNextTimeframe: () => Promise<void>
}

export function useMarketData({
  symbol,
  timeframe,
  enabled = true
}: UseMarketDataProps): UseMarketDataReturn {
  const queryClient = useQueryClient()
  const queryKey = ['marketData', symbol, timeframe]

  const { data, isLoading, isError, error, refetch: queryRefetch } = useQuery({
    queryKey,
    queryFn: async () => {
      try {
        const response = await apiClient.get<MarketAnalysis>(
          '/api/v1/historical/market',
          {
            params: { symbol, timeframe }
          }
        )
        return response.data ?? null
      } catch (error) {
        console.error('Error fetching market data:', error)
        return null
      }
    },
    enabled,
    gcTime: 1000 * 60 * 5,
    staleTime: 1000 * 60,
    retry: 2,
    refetchInterval: 1000 * 30,
  })

  const prefetchNextTimeframe = async () => {
    const timeframes: Timeframe[] = ['1h', '4h', '1d']
    const currentIndex = timeframes.indexOf(timeframe)
    if (currentIndex < timeframes.length - 1) {
      const nextTimeframe = timeframes[currentIndex + 1]
      await queryClient.prefetchQuery({
        queryKey: ['marketData', symbol, nextTimeframe],
        queryFn: async () => {
          try {
            const response = await apiClient.get<MarketAnalysis>(
              '/api/v1/historical/market',
              {
                params: { symbol, timeframe: nextTimeframe }
              }
            )
            return response.data ?? null
          } catch (error) {
            console.error('Error prefetching market data:', error)
            return null
          }
        },
        staleTime: 1000 * 60
      })
    }
  }

  const refetch = async () => {
    await queryRefetch()
  }

  return {
    data: data ?? null,
    isLoading,
    isError,
    error: error as Error | null,
    refetch,
    prefetchNextTimeframe
  }
}