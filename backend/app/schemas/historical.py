# app/schemas/historical.py
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class HistoricalKlineResponse(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: datetime
    quote_volume: float
    trades: int
    taker_buy_base: float
    taker_buy_quote: float

    class Config:
        from_attributes = True

class HistoricalMetricsResponse(BaseModel):
    timestamp: datetime
    volatility: Optional[float] = None
    volatility_short: Optional[float] = None
    volatility_medium: Optional[float] = None
    volatility_long: Optional[float] = None
    ma7: Optional[float] = None
    ma25: Optional[float] = None
    ma99: Optional[float] = None
    rsi: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
    returns: Optional[float] = None
    log_returns: Optional[float] = None
    realized_volatility: Optional[float] = None
    price_momentum: Optional[float] = None
    volume_momentum: Optional[float] = None

    class Config:
        from_attributes = True

class TrendAnalysisResponse(BaseModel):
    direction: str
    strength: float
    duration: int
    price_change_pct: float

class RegimeAnalysisResponse(BaseModel):
    regime: str
    zscore: float
    percentile: float
    description: str

class HistoricalAnalysisResponse(BaseModel):
    timestamp: datetime
    volatility_regime: Optional[str] = None
    volatility_percentile: Optional[float] = None
    volatility_zscore: Optional[float] = None
    trend_analysis: Optional[TrendAnalysisResponse] = None
    regime_analysis: Optional[RegimeAnalysisResponse] = None
    market_score: Optional[float] = None
    analysis_details: Optional[Dict] = None

    class Config:
        from_attributes = True