// src/hooks/use-volatility.ts
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/axios-instance'
import type { Timeframe, TradingPair } from '@/types/market'

// 定義週期特徵接口
interface RegimePeriodCharacteristics {
  mean_volatility: number;
  count: number;
  avg_returns: number;
  std_returns: number;
  period: {
    start: string;
    end: string;
  };
}

// 定義持續時間統計接口
interface RegimeDurationStats {
  mean: number;
  max: number;
  min: number;
  std: number;
}

export interface VolatilityRegime {
  current_regime: {
    id: number;
    volatility: number;
    characteristics: RegimePeriodCharacteristics;
  };
  regime_statistics: Record<string, RegimePeriodCharacteristics>;
  transition_probabilities: number[][];
  regime_duration: Record<string, RegimeDurationStats>;
  stability_score: number;
}

export interface VolatilityData {
  timestamp: string;
  volatility: number;
}

interface UseVolatilityProps {
  symbol: TradingPair;
  timeframe: Timeframe;
  lookbackDays?: number;
}

interface UseVolatilityReturn {
  regimeData: VolatilityRegime | null;
  historicalData: VolatilityData[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  getCurrentRegime: () => VolatilityRegime['current_regime'] | null;
  getStabilityScore: () => number;
  getTransitionProbability: (fromRegime: number, toRegime: number) => number;
}

export function useVolatility({
  symbol,
  timeframe,
  lookbackDays = 30
}: UseVolatilityProps): UseVolatilityReturn {
  // 波動率區間查詢
  const regimeQuery = useQuery({
    queryKey: ['volatilityRegimes', symbol, timeframe, lookbackDays],
    queryFn: async () => {
      try {
        const response = await apiClient.get<VolatilityRegime>(
          '/api/v1/historical/volatility/regimes',
          {
            params: {
              symbol,
              timeframe,
              lookback_days: lookbackDays
            }
          }
        );
        return response.data;
      } catch (error) {
        console.error('Error fetching regime data:', error);
        return null;
      }
    },
    staleTime: 1000 * 60 * 5,  // 5分鐘後數據過期
    gcTime: 1000 * 60 * 30,    // 30分鐘後清理快取
  });

  // 歷史數據查詢
  const historicalQuery = useQuery({
    queryKey: ['volatilityHistory', symbol, timeframe, lookbackDays],
    queryFn: async () => {
      try {
        const response = await apiClient.get<VolatilityData[]>(
          '/api/v1/historical/volatility/history',
          {
            params: {
              symbol,
              timeframe,
              lookback_days: lookbackDays
            }
          }
        );
        return response.data || [];
      } catch (error) {
        console.error('Error fetching historical data:', error);
        return [];
      }
    },
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 30,
  });
  
  // 整合所有查詢數據和輔助方法
  return {
    regimeData: regimeQuery.data ?? null,
    historicalData: historicalQuery.data ?? [],
    isLoading: regimeQuery.isLoading || historicalQuery.isLoading,
    isError: regimeQuery.isError || historicalQuery.isError,
    error: (regimeQuery.error || historicalQuery.error) as Error | null,
    getCurrentRegime: () => regimeQuery.data?.current_regime ?? null,
    getStabilityScore: () => regimeQuery.data?.stability_score ?? 0,
    getTransitionProbability: (fromRegime: number, toRegime: number) =>
      regimeQuery.data?.transition_probabilities[fromRegime]?.[toRegime] ?? 0,
  };
}