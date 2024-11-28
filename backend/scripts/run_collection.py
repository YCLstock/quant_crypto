# backend/scripts/run_collection.py
import asyncio
import signal
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))

from app.data_collectors.binance import DataCollectionTasks
from app.core.database import SessionLocal
from app.models.market import MarketData, TradingPair
from sqlalchemy import select, func, text

class DataCollectionController:
    def __init__(self):
        self.tasks: Optional[DataCollectionTasks] = None
        self.should_stop = False
        
    async def start(self, symbols: list[str]):
        """啟動數據收集"""
        self.tasks = DataCollectionTasks()
        
        # 註冊信號處理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"Starting data collection for symbols: {symbols}")
        print("Press Ctrl+C to stop...")
        
        try:
            await self.tasks.start_collection(symbols)
        except Exception as e:
            print(f"Error during collection: {e}")
        finally:
            if self.tasks:
                await self.tasks.stop_collection()
    
    def signal_handler(self, signum, frame):
        """處理停止信號"""
        print("\nReceived stop signal. Shutting down gracefully...")
        self.should_stop = True
        if self.tasks:
            asyncio.create_task(self.tasks.stop_collection())

    @staticmethod
    def check_data(hours: int = 1):
        """檢查最近收集的數據"""
        db = SessionLocal()
        try:
            # 使用 timedelta 來計算時間範圍
            time_threshold = datetime.now() - timedelta(hours=hours)
            
            # 修改查詢語句
            stmt = (
                select(
                    TradingPair.symbol,
                    func.count(MarketData.id).label('records'),
                    func.min(MarketData.close_price).label('min_price'),
                    func.max(MarketData.close_price).label('max_price'),
                    func.avg(MarketData.volume).label('avg_volume')
                )
                .join(MarketData.trading_pair)
                .where(MarketData.timestamp >= time_threshold)
                .group_by(TradingPair.symbol)
            )
            
            results = db.execute(stmt).fetchall()
            
            # 轉換為 DataFrame 顯示
            if results:
                df = pd.DataFrame(results)
                print(f"\nData collected in the last {hours} hours:")
                print(df.to_string(index=False))
            else:
                print(f"No data collected in the last {hours} hours")
                
            # 顯示最新記錄的時間
            latest_record = db.query(func.max(MarketData.timestamp)).scalar()
            if latest_record:
                print(f"\nLatest record time: {latest_record}")
            else:
                print("\nNo records found in the database")
                
        except Exception as e:
            print(f"Error checking data: {e}")
        finally:
            db.close()

async def main():
    controller = DataCollectionController()
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    # 啟動收集前檢查現有數據
    print("Checking existing data...")
    controller.check_data(hours=1)
    
    # 啟動數據收集
    await controller.start(symbols)

if __name__ == "__main__":
    asyncio.run(main())