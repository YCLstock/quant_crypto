# backend/app/api/v1/market.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.historical.data_service import HistoricalDataService

router = APIRouter()

@router.get("/analysis/market")
async def get_market_analysis(
    symbol: str,
    timeframe: str,
    db: Session = Depends(get_db)
):
    service = HistoricalDataService(db)
    return await service.analyze_volatility(symbol, timeframe)

@router.get("/analysis/volatility/regimes")
async def get_volatility_regimes(
    symbol: str,
    timeframe: str,
    lookback_days: int = 30,
    db: Session = Depends(get_db)
):
    service = HistoricalDataService(db)
    return await service.analyze_volatility_regimes(symbol, timeframe, lookback_days)

@router.get("/analysis/volatility/history")
async def get_volatility_history(
    symbol: str,
    timeframe: str,
    lookback_days: int = 30,
    db: Session = Depends(get_db)
):
    service = HistoricalDataService(db)
    return await service.get_market_analysis(symbol, timeframe, lookback_days)