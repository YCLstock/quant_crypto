// src/services/market-analysis/api.ts
import axios from 'axios'
import { MarketAnalysis, Timeframe, TradingPair } from '@/types/market'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const marketAnalysisApi = {
  async getAnalysis(
    symbol: TradingPair,
    timeframe: Timeframe
  ): Promise<MarketAnalysis> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/historical/market`,  // 已經正確
        {
          params: {
            symbol,
            timeframe
          }
        }
      )
      return response.data
    } catch (error) {
      console.error('Error fetching market analysis:', error)
      throw error
    }
  },

  async getVolatilityRegimes(
    symbol: TradingPair,
    timeframe: Timeframe,
    lookback_days: number = 30
  ) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/historical/volatility/regimes`,  // 已經正確
        {
          params: {
            symbol,
            timeframe,
            lookback_days
          }
        }
      )
      return response.data
    } catch (error) {
      console.error('Error fetching volatility regimes:', error)
      throw error
    }
  },

  async getVolatilityHistory(
    symbol: TradingPair,
    timeframe: Timeframe,
    lookback_days: number = 30
  ) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/historical/volatility/history`,  // 已經正確
        {
          params: {
            symbol,
            timeframe,
            lookback_days
          }
        }
      )
      return response.data
    } catch (error) {
      console.error('Error fetching volatility history:', error)
      throw error
    }
  },

  async getHistoricalSummary(
    symbol: TradingPair,
    timeframe: Timeframe,
    lookback_days: number = 30
  ) {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/historical/summary`,  // 已經正確
        {
          params: {
            symbol,
            timeframe,
            lookback_days
          }
        }
      )
      return response.data
    } catch (error) {
      console.error('Error fetching historical summary:', error)
      throw error
    }
  }
}