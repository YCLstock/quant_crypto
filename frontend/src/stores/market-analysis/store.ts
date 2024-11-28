// src/stores/market-analysis/store.ts
import { create } from 'zustand'
import { MarketAnalysis, Timeframe, TradingPair } from '@/types/market'
import { marketAnalysisApi } from '@/services/market-analysis/api'

interface MarketAnalysisState {
  selectedPair: TradingPair
  selectedTimeframe: Timeframe
  analysis: MarketAnalysis | null
  isLoading: boolean
  error: string | null
  
  setSelectedPair: (pair: TradingPair) => void
  setSelectedTimeframe: (timeframe: Timeframe) => void
  fetchAnalysis: () => Promise<void>
}

export const useMarketAnalysisStore = create<MarketAnalysisState>((set, get) => ({
  selectedPair: 'BTCUSDT',
  selectedTimeframe: '1h',
  analysis: null,
  isLoading: false,
  error: null,

  setSelectedPair: (pair) => {
    set({ selectedPair: pair })
    get().fetchAnalysis()
  },

  setSelectedTimeframe: (timeframe) => {
    set({ selectedTimeframe: timeframe })
    get().fetchAnalysis()
  },

  fetchAnalysis: async () => {
    const { selectedPair, selectedTimeframe } = get()
    
    try {
      set({ isLoading: true, error: null })
      
      const analysis = await marketAnalysisApi.getAnalysis(
        selectedPair,
        selectedTimeframe
      )
      
      set({ analysis, isLoading: false })
    } catch (error) {
      set({ 
        error: 'Failed to fetch market analysis',
        isLoading: false 
      })
    }
  }
}))