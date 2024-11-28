# app/api/v1/historical.py
import math
from datetime import datetime,timedelta,timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.core.database import get_db
from app.schemas.historical import (
    HistoricalKlineResponse,
    HistoricalMetricsResponse,
    HistoricalAnalysisResponse,
)
from app.services.historical.data_service import HistoricalDataService

router = APIRouter(prefix="/historical", tags=["historical"])

@router.get("/klines", response_model=List[HistoricalKlineResponse])
def get_historical_klines(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTCUSDT)"),
    timeframe: str = Query(..., description="Timeframe (e.g., 1h, 4h, 1d)"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(100, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """獲取歷史K線數據"""
    try:
        logger.info(f"Fetching klines for {symbol} {timeframe}")
        service = HistoricalDataService(db)
        klines = service.get_historical_klines(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return klines
    except Exception as e:
        logger.error(f"Error fetching klines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=List[HistoricalMetricsResponse])
def get_historical_metrics(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    metrics: List[str] = Query(['volatility', 'rsi', 'ma']),
    db: Session = Depends(get_db)
):
    """獲取歷史技術指標數據"""
    try:
        logger.info(f"Fetching metrics for {symbol} {timeframe}")
        service = HistoricalDataService(db)
        metrics_data = service.get_historical_metrics(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            metrics=metrics
        )
        return metrics_data
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def safe_float(value: float) -> float:
    """安全處理浮點數"""
    try:
        if value is None or math.isnan(value) or math.isinf(value):
            return 0.0
        if abs(value) > 1e308:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0

@router.get("/market", response_model=HistoricalAnalysisResponse)
def get_market_analysis(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    db: Session = Depends(get_db)
):
    """獲取市場分析數據"""
    try:
        logger.info(f"Analyzing market data for {symbol} {timeframe}")
        service = HistoricalDataService(db)
        result = service.analyze_volatility(
            symbol=symbol,
            timeframe=timeframe
        )

        if not result:
            logger.warning(f"No analysis data available for {symbol} {timeframe}")
            raise HTTPException(status_code=404, detail="No data available")
        
        # 確保時區是UTC
        if isinstance(result.get("timestamp"), datetime):
            result["timestamp"] = result["timestamp"].replace(tzinfo=timezone.utc)
        
        # 安全處理數值
        if result.get("volatility_percentile"):
            result["volatility_percentile"] = safe_float(result["volatility_percentile"])
        if result.get("volatility_zscore"):
            result["volatility_zscore"] = safe_float(result["volatility_zscore"])
        if result.get("market_score"):
            result["market_score"] = safe_float(result["market_score"])
            
        # 處理嵌套對象
        if result.get("trend_analysis"):
            result["trend_analysis"]["strength"] = safe_float(result["trend_analysis"]["strength"])
            result["trend_analysis"]["price_change_pct"] = safe_float(result["trend_analysis"]["price_change_pct"])
            
        if result.get("regime_analysis"):
            result["regime_analysis"]["zscore"] = safe_float(result["regime_analysis"]["zscore"])
            result["regime_analysis"]["percentile"] = safe_float(result["regime_analysis"]["percentile"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in market analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/volatility/regimes")
async def get_volatility_regimes(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query(..., description="Timeframe"), 
    lookback_days: int = Query(30, description="Look back days"),
    db: Session = Depends(get_db)
):
    """波動率區間分析端點"""
    try:
        service = HistoricalDataService(db)
        start_time = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
        result = service.analyze_volatility(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="No data available")
        
        # 安全處理數據
        regime_data = {
            'current_regime': {
                'regime': result.get('regime_analysis', {}).get('regime'),
                'volatility': safe_float(
                    result.get('volatility_stats', {}).get('current')
                ),
                'zscore': safe_float(
                    result.get('regime_analysis', {}).get('zscore')
                )
            },
            'volatility_stats': {
                k: safe_float(v) 
                for k, v in result.get('volatility_stats', {}).items()
            },
            'market_regime': result.get('market_regime'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return regime_data
        
    except Exception as e:
        logger.error(f"Error analyzing volatility regimes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/volatility/history")
async def get_volatility_history(
   symbol: str = Query(..., description="Trading pair symbol"),
   timeframe: str = Query(..., description="Timeframe"),
   lookback_days: int = Query(30, description="Look back days"),
   db: Session = Depends(get_db)
):
   """歷史波動率數據端點"""
   try:
       service = HistoricalDataService(db)
       
       # 使用正確的方法名稱
       metrics = service._get_historical_data(
           symbol=symbol,
           timeframe=timeframe,
           start_time=datetime.now() - timedelta(days=lookback_days)
       )
       
       # 安全處理浮點數，過濾無效值
       def safe_float(value):
           try:
               # 檢查是否為 None、NaN 或 Infinity
               if value is None or math.isnan(value) or math.isinf(value):
                   return 0.0
               # 確保在合理範圍內
               if abs(value) > 1e308:  # Python float 最大值
                   return 0.0
               return float(value)
           except (TypeError, ValueError):
               return 0.0

       # 轉換為前端需要的格式，同時處理無效值
       volatility_history = [
           {
               "timestamp": metric.timestamp.isoformat(),
               "volatility": safe_float(metric.volatility)
           }
           for metric in metrics
           if metric and hasattr(metric, 'timestamp') 
       ]
       
       if not volatility_history:
           raise HTTPException(status_code=404, detail="No data available")
           
       return volatility_history
       
   except Exception as e:
       logger.error(f"Error getting volatility history: {e}")
       raise HTTPException(status_code=500, detail=str(e))