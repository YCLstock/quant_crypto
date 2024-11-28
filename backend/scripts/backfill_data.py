#!/usr/bin/env python3

import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from tqdm import tqdm
from sqlalchemy import text
import logging

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.logging import logger
from app.models.market import TradingPair
from app.data_collectors.binance.historical_collector import HistoricalDataCollector

class DataBackfillTool:
    def __init__(self):
        self.db = SessionLocal()
        self.collector = HistoricalDataCollector(self.db)
        self.progress_bars: Dict[str, tqdm] = {}

    async def backfill_data(
        self,
        symbols: List[str],
        timeframes: Optional[List[str]] = None,
        days: int = 30,
        clean_old_data: bool = False
    ):
        """執行數據回填"""
        try:
            if not timeframes:
                timeframes = ['1h', '4h', '1d']

            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 清理舊數據（如果需要）
            if clean_old_data:
                await self._clean_old_data(symbols, timeframes, start_time)
            
            total_tasks = len(symbols) * len(timeframes)
            main_progress = tqdm(
                total=total_tasks,
                desc="Overall Progress",
                position=0
            )

            for symbol in symbols:
                logger.info(f"Starting backfill for {symbol}")
                
                for timeframe in timeframes:
                    try:
                        main_progress.set_description(
                            f"Processing {symbol} {timeframe}"
                        )
                        
                        # 檢查是否有重複數據
                        existing_data = await self._check_existing_data(
                            symbol, 
                            timeframe, 
                            start_time,
                            end_time
                        )
                        
                        if existing_data:
                            logger.info(
                                f"Data already exists for {symbol} {timeframe} "
                                f"from {existing_data['first_date']} to {existing_data['last_date']}"
                            )
                            main_progress.update(1)
                            continue
                        
                        # 收集數據
                        collected_data = await self._collect_symbol_data(
                            symbol=symbol,
                            timeframe=timeframe,
                            start_time=start_time,
                            end_time=end_time
                        )
                        
                        if collected_data:
                            logger.info(
                                f"Successfully collected {len(collected_data)} "
                                f"{timeframe} records for {symbol}"
                            )
                        
                        main_progress.update(1)
                        
                    except Exception as e:
                        logger.error(
                            f"Error collecting {timeframe} data for {symbol}: {e}"
                        )
                    
                    await asyncio.sleep(1)
            
            main_progress.close()
            logger.info("Backfill completed successfully")
            
        except Exception as e:
            logger.error(f"Error during backfill: {e}")
            raise
        finally:
            self.db.close()

    async def _clean_old_data(
        self,
        symbols: List[str],
        timeframes: List[str],
        start_time: datetime
    ):
        """清理指定時間範圍之前的舊數據"""
        try:
            for symbol in symbols:
                trading_pair = self.db.query(TradingPair).filter_by(
                    symbol=symbol,
                    is_active=1
                ).first()
                
                if not trading_pair:
                    continue
                
                for timeframe in timeframes:
                    delete_query = text("""
                        DELETE FROM historical_metrics
                        WHERE trading_pair_id = :pair_id
                        AND timeframe = :timeframe
                        AND timestamp < :start_time
                    """)
                    
                    result = self.db.execute(
                        delete_query,
                        {
                            "pair_id": trading_pair.id,
                            "timeframe": timeframe,
                            "start_time": start_time
                        }
                    )
                    
                    self.db.commit()
                    
                    logger.info(
                        f"Cleaned {result.rowcount} old records for "
                        f"{symbol} {timeframe}"
                    )
                    
        except Exception as e:
            logger.error(f"Error cleaning old data: {e}")
            self.db.rollback()

    async def _collect_symbol_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """改進的數據收集方法"""
        try:
            # 調整收集時間
            adjusted_start = self._adjust_collection_time(start_time, timeframe)
            adjusted_end = self._adjust_collection_time(end_time, timeframe, False)
            
            data = self.collector.collect_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_time=adjusted_start,
                end_time=adjusted_end
            )
            
            # 驗證數據完整性
            if data:
                expected_count = self._calculate_expected_records(
                    timeframe,
                    adjusted_start,
                    adjusted_end
                )
                completeness = len(data) / expected_count
                logger.info(
                    f"Data completeness for {symbol} {timeframe}: "
                    f"{completeness:.1%}"
                )
            
            return data
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol} {timeframe}: {e}")
            return []
        
    async def _check_existing_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[Dict]:
        """檢查指定時間範圍內是否已有數據"""
        try:
            trading_pair = self.db.query(TradingPair).filter_by(
                symbol=symbol,
                is_active=1
            ).first()
            
            if not trading_pair:
                return None
            
            query = text("""
                SELECT 
                    MIN(timestamp) as first_date,
                    MAX(timestamp) as last_date,
                    COUNT(*) as record_count
                FROM historical_metrics
                WHERE trading_pair_id = :pair_id
                AND timeframe = :timeframe
                AND timestamp BETWEEN :start_time AND :end_time
            """)
            
            result = self.db.execute(
                query,
                {
                    "pair_id": trading_pair.id,
                    "timeframe": timeframe,
                    "start_time": start_time,
                    "end_time": end_time
                }
            ).fetchone()
            
            if not result or not result.record_count:
                return None
            
            # 檢查數據是否完整
            expected_count = self._calculate_expected_records(
                timeframe,
                start_time,
                end_time
            )
            
            if result.record_count >= expected_count * 0.95:  # 允許5%的誤差
                return {
                    'first_date': result.first_date,
                    'last_date': result.last_date,
                    'record_count': result.record_count
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing data: {e}")
            return None

    def _calculate_expected_records(
        self,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """計算指定時間範圍內應該有的記錄數"""
        time_diff = end_time - start_time
        hours = time_diff.total_seconds() / 3600
        
        if timeframe == '1h':
            return int(hours)
        elif timeframe == '4h':
            return int(hours / 4)
        elif timeframe == '1d':
            return int(hours / 24)
        
        return 0
    
    def _adjust_collection_time(
        self,
        dt: datetime,
        timeframe: str,
        is_start: bool = True
    ) -> datetime:
        """調整數據收集時間以確保完整性"""
        if timeframe == '1d':
            # 對於日線，使用UTC 00:00
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            if not is_start:
                dt += timedelta(days=1)
        elif timeframe == '4h':
            # 對於4小時線，調整到4小時的整數倍
            hour = (dt.hour // 4) * 4
            dt = dt.replace(hour=hour, minute=0, second=0, microsecond=0)
            if not is_start:
                dt += timedelta(hours=4)
        elif timeframe == '1h':
            # 對於小時線，調整到整點
            dt = dt.replace(minute=0, second=0, microsecond=0)
            if not is_start:
                dt += timedelta(hours=1)
        return dt


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    symbols = ['BTCUSDT', 'ETHUSDT']
    
    tool = DataBackfillTool()
    
    try:
        await tool.backfill_data(
            symbols=symbols,
            timeframes=['1h', '4h', '1d'],
            days=365,
            clean_old_data=True  # 添加此參數來清理舊數據
        )
    except KeyboardInterrupt:
        logger.info("Backfill interrupted by user")
    except Exception as e:
        logger.error(f"Backfill failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())