# backend/scripts/check_data.py
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select, func

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.market import MarketData, TradingPair, OrderBook

class DataChecker:
    def __init__(self):
        self.db = SessionLocal()
    
    def check_market_data(self, symbol: str = None, hours: int = 1):
        """檢查市場數據"""
        query = (
            select(
                TradingPair.symbol,
                MarketData.timestamp,
                MarketData.close_price,
                MarketData.volume,
                MarketData.high_price,
                MarketData.low_price
            )
            .join(MarketData.trading_pair)
            .where(MarketData.timestamp >= datetime.now() - timedelta(hours=hours))
        )
        
        if symbol:
            query = query.where(TradingPair.symbol == symbol)
            
        results = self.db.execute(query).fetchall()
        df = pd.DataFrame(results)
        
        if not df.empty:
            print("\nMarket Data Summary:")
            print(df.describe())
            
            # 繪製價格圖表
            try:
                import matplotlib.pyplot as plt
                plt.figure(figsize=(12, 6))
                df.plot(x='timestamp', y='close_price')
                plt.title(f"Price Movement - Last {hours} hours")
                plt.show()
            except ImportError:
                print("matplotlib not installed. Skipping chart generation.")
    
    def check_order_books(self, symbol: str, limit: int = 5):
        """檢查訂單簿數據"""
        query = (
            select(OrderBook)
            .join(OrderBook.trading_pair)
            .where(TradingPair.symbol == symbol)
            .order_by(OrderBook.timestamp.desc())
            .limit(limit)
        )
        
        results = self.db.execute(query).fetchall()
        
        print(f"\nLatest Order Book Data for {symbol}:")
        for ob in results:
            print(f"\nTimestamp: {ob.timestamp}")
            print("Top 5 Bids:")
            for bid in ob.bids[:5]:
                print(f"Price: {bid[0]}, Amount: {bid[1]}")
            print("\nTop 5 Asks:")
            for ask in ob.asks[:5]:
                print(f"Price: {ask[0]}, Amount: {ask[1]}")
    
    def check_data_quality(self):
        """檢查數據質量"""
        # 檢查數據間隔
        query = (
            select(
                TradingPair.symbol,
                func.avg(
                    func.extract('epoch', 
                        func.lead(MarketData.timestamp).over(
                            partition_by=MarketData.trading_pair_id,
                            order_by=MarketData.timestamp
                        ) - MarketData.timestamp
                    )
                ).label('avg_interval')
            )
            .join(MarketData.trading_pair)
            .group_by(TradingPair.symbol)
        )
        
        results = self.db.execute(query).fetchall()
        print("\nData Collection Intervals (seconds):")
        for symbol, interval in results:
            print(f"{symbol}: {interval:.2f}s")
    
    def close(self):
        self.db.close()

def main():
    checker = DataChecker()
    try:
        # 檢查特定交易對的數據
        symbol = "BTCUSDT"
        print(f"\nChecking data for {symbol}...")
        checker.check_market_data(symbol, hours=1)
        
        # 檢查訂單簿
        checker.check_order_books(symbol)
        
        # 檢查數據質量
        checker.check_data_quality()
        
    finally:
        checker.close()

if __name__ == "__main__":
    main()