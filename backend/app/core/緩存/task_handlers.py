# app/core/task_handlers.py

from typing import Dict, Any
import asyncio
from datetime import datetime, timedelta

from app.core.logging import logger
from app.services.historical.data_service import HistoricalDataService
from app.data_collectors.binance import DataCollectionTasks
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

class HistoricalDataHandler:
    """歷史數據收集任務處理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.service = HistoricalDataService(db)
    
    async def collect_historical_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """收集歷史數據"""
        try:
            symbol = payload['symbol']
            timeframe = payload['timeframe']
            start_time = datetime.fromisoformat(payload['start_time'])
            end_time = datetime.fromisoformat(payload.get('end_time', datetime.now().isoformat()))
            
            # 分批收集數據
            current_start = start_time
            total_records = 0
            
            while current_start < end_time:
                current_end = min(
                    current_start + timedelta(days=7),
                    end_time
                )
                
                # 收集一批數據
                records = await self.service.collect_historical_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=current_start,
                    end_time=current_end
                )
                
                total_records += len(records)
                current_start = current_end
                
                # 防止過快請求
                await asyncio.sleep(1)
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'total_records': total_records,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error collecting historical data: {e}")
            raise

class DataAnalysisHandler:
    """數據分析任務處理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.service = HistoricalDataService(db)
    
    async def analyze_market_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """執行市場數據分析"""
        try:
            symbol = payload['symbol']
            timeframe = payload['timeframe']
            
            # 執行分析
            analysis = await self.service.analyze_volatility(
                symbol=symbol,
                timeframe=timeframe
            )
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market data: {e}")
            raise

# 實例化處理器
def get_task_handlers():
    """獲取所有任務處理器"""
    db = SessionLocal()
    
    return {
        'collect_historical_data': HistoricalDataHandler(db).collect_historical_data,
        'analyze_market_data': DataAnalysisHandler(db).analyze_market_data,
        # 可以添加更多處理器
    }