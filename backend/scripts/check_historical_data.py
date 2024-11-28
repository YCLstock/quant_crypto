# backend/scripts/check_historical_data.py

import asyncio
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import select, func
from app.core.database import SessionLocal
from app.models.historical import HistoricalMetrics
from app.models.market import TradingPair
from app.core.logging import logger

class HistoricalDataChecker:
    def __init__(self):
        self.db = SessionLocal()
    
    async def check_data_integrity(self, symbol: str, timeframe: str, days: int = 30):
        """檢查歷史數據完整性"""
        try:
            # 獲取交易對ID
            trading_pair = self.db.query(TradingPair).filter_by(
                symbol=symbol,
                is_active=1
            ).first()
            
            if not trading_pair:
                logger.error(f"Trading pair not found: {symbol}")
                return
            
            # 設置時間範圍
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 查詢數據
            query = select(HistoricalMetrics).where(
                HistoricalMetrics.trading_pair_id == trading_pair.id,
                HistoricalMetrics.timeframe == timeframe,
                HistoricalMetrics.timestamp.between(start_time, end_time)
            )
            
            results = self.db.execute(query).scalars().all()
            
            if not results:
                logger.error(f"No data found for {symbol} {timeframe}")
                return
            
            # 轉換為DataFrame進行分析
            df = pd.DataFrame([{
                'timestamp': r.timestamp,
                'open_price': r.open_price,
                'high_price': r.high_price,
                'low_price': r.low_price,
                'close_price': r.close_price,
                'volume': r.volume,
                'volatility': r.volatility
            } for r in results])
            
            # 檢查並打印結果
            self._print_check_results(df, symbol, timeframe)
            
            # 返回檢查結果
            return self._generate_check_report(df)
            
        except Exception as e:
            logger.error(f"Error checking data integrity: {e}")
            raise
        finally:
            self.db.close()
    
    def _print_check_results(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """打印檢查結果"""
        print(f"\nData Integrity Check for {symbol} {timeframe}")
        print("=" * 50)
        
        # 基本統計
        print("\nBasic Statistics:")
        print(f"Total Records: {len(df)}")
        print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # 缺失值檢查
        missing_values = df.isnull().sum()
        if missing_values.any():
            print("\nMissing Values:")
            print(missing_values[missing_values > 0])
        
        # 異常值檢查
        print("\nPrice Range Check:")
        print(f"Lowest Price: {df['low_price'].min():.2f}")
        print(f"Highest Price: {df['high_price'].max():.2f}")
        
        # 波動率檢查
        print("\nVolatility Check:")
        print(f"Mean Volatility: {df['volatility'].mean():.2f}%")
        print(f"Max Volatility: {df['volatility'].max():.2f}%")
        
        # 數據間隔檢查
        time_diffs = df['timestamp'].diff()
        expected_interval = self._get_expected_interval(timeframe)
        irregular_intervals = time_diffs[time_diffs != expected_interval]
        
        if not irregular_intervals.empty:
            print("\nIrregular Time Intervals Found:")
            for idx, diff in irregular_intervals.items():
                print(f"At {df['timestamp'][idx]}: {diff}")
    
    def _generate_check_report(self, df: pd.DataFrame) -> dict:
        """生成檢查報告"""
        return {
            'total_records': len(df),
            'date_range': {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat()
            },
            'missing_values': df.isnull().sum().to_dict(),
            'price_stats': {
                'min': float(df['low_price'].min()),
                'max': float(df['high_price'].max()),
                'mean': float(df['close_price'].mean())
            },
            'volatility_stats': {
                'mean': float(df['volatility'].mean()),
                'max': float(df['volatility'].max()),
                'current': float(df['volatility'].iloc[-1])
            },
            'data_quality': {
                'has_gaps': bool(df['timestamp'].diff().nunique() > 1),
                'is_complete': bool(len(df) >= self._get_expected_records(df['timestamp'].min(), df['timestamp'].max())),
                'has_missing_values': bool(df.isnull().any().any())
            }
        }
    
    def _get_expected_interval(self, timeframe: str) -> timedelta:
        """獲取預期的數據間隔"""
        value = int(timeframe[:-1])
        unit = timeframe[-1]
        
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
    
    def _get_expected_records(self, start: datetime, end: datetime) -> int:
        """計算預期的記錄數量"""
        time_diff = end - start
        return int(time_diff.total_seconds() / self._get_expected_interval(timeframe).total_seconds())

async def main():
    checker = HistoricalDataChecker()
    symbols = ['BTCUSDT', 'ETHUSDT']
    timeframes = ['1h', '4h', '1d']
    
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                await checker.check_data_integrity(symbol, timeframe)
            except Exception as e:
                print(f"Error checking {symbol} {timeframe}: {e}")

if __name__ == "__main__":
    asyncio.run(main())