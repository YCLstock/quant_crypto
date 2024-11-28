// src/types/market.ts 

// 市場分析返回類型
export interface MarketAnalysis {
  timestamp: string;
  volatility_regime: string | null;
  volatility_percentile: number | null;
  volatility_zscore: number | null;
  trend_analysis: TrendAnalysis;
  regime_analysis: RegimeAnalysis;
  market_score: number;
  volatility_stats: {
    current: number;
    mean: number;
    std: number;
    max: number;
    min: number;
  };
}

// 趨勢分析類型
export interface TrendAnalysis {
  direction: 'Uptrend' | 'Downtrend' | 'Sideways';
  strength: number;
  duration: number;
  price_change_pct: number;
}

// 區間分析類型
export interface RegimeAnalysis {
  regime: 'Extremely High' | 'High' | 'Normal' | 'Low' | 'Extremely Low';
  zscore: number;
  percentile: number;
  description: string;
}

// 週期特徵類型
export interface RegimePeriodCharacteristics {
  mean_volatility: number;
  count: number;
  avg_returns: number;
  std_returns: number;
  period: {
    start: string;
    end: string;
  };
}

// 波動率區間類型
export interface VolatilityRegime {
  current_regime: {
    id: number;
    volatility: number;
    characteristics: RegimePeriodCharacteristics;
  };
  regime_statistics: Record<string, RegimePeriodCharacteristics>;
  transition_probabilities: number[][];
  regime_duration: Record<string, {
    mean: number;
    max: number;
    min: number;
    std: number;
  }>;
  stability_score: number;
}

// 波動率數據類型

export type Timeframe = '1h' | '4h' | '1d'
export type TradingPair = 'BTCUSDT' | 'ETHUSDT' | 'BNBUSDT'

export interface VolatilityData {
  timestamp: string;
  volatility: number;
  close_price: number;
}

export interface ChartData {
  timestamp: number;
  volatility: number;
  volatilityPoints: number;
  price?: number;
}

export interface TooltipData {
  payload: Array<{
    value: number;
    payload: ChartData;
  }>;
  active?: boolean;
  label?: string;
}