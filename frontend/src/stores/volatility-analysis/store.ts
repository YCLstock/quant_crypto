// src/stores/volatility-analysis/store.ts
import { create } from 'zustand'

interface VolatilityState {
  showPrice: boolean;
  toggleShowPrice: () => void;
}

export const useVolatilityStore = create<VolatilityState>((set) => ({
  showPrice: false,
  toggleShowPrice: () => set((state) => ({ showPrice: !state.showPrice })),
}))