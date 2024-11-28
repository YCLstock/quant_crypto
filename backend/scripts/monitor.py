# backend/scripts/monitor.py
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import time
import os

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.market import MarketData, TradingPair

class DataMonitor:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_latest_data(self):
        """獲取最新數據"""
        query = (
            self.db.query(
                TradingPair.symbol,
                MarketData.close_price,
                MarketData.volume,
                MarketData.price_change_percent,
                MarketData.timestamp,
                MarketData.high_price,
                MarketData.low_price
            )
            .join(MarketData.trading_pair)
            .order_by(MarketData.timestamp.desc())
            .limit(10)
        )
        return query.all()
    
    def clear_screen(self):
        """清除屏幕"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_price_color(self, price, change):
        """格式化價格顯示"""
        if change >= 0:
            return f"\033[92m{price:10.2f}\033[0m"  # 綠色
        return f"\033[91m{price:10.2f}\033[0m"  # 紅色
    
    def display_data(self):
        """顯示數據"""
        try:
            while True:
                self.clear_screen()
                data = self.get_latest_data()
                
                # 顯示標題
                print("\n=== Real-time Market Data Monitor ===")
                print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                print("=" * 80)
                
                # 顯示表頭
                print(f"{'Symbol':<10} {'Price':>10} {'24h High':>10} {'24h Low':>10} "
                      f"{'Volume':>15} {'Change %':>10} {'Time':>20}")
                print("-" * 80)
                
                # 顯示數據
                for record in data:
                    price_str = self.format_price_color(
                        record.close_price, 
                        record.price_change_percent
                    )
                    change_str = self.format_price_color(
                        record.price_change_percent, 
                        record.price_change_percent
                    )
                    
                    print(
                        f"{record.symbol:<10} {price_str} "
                        f"{record.high_price:10.2f} {record.low_price:10.2f} "
                        f"{record.volume:15.2f} {change_str} "
                        f"{record.timestamp.strftime('%H:%M:%S'):>20}"
                    )
                
                print("\nPress Ctrl+C to exit")
                time.sleep(1)  # 每秒更新一次
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        finally:
            self.db.close()
    
    def show_summary(self):
        """顯示數據摘要"""
        data = self.get_latest_data()
        if not data:
            print("No data available")
            return
            
        df = pd.DataFrame([{
            'symbol': record.symbol,
            'price': record.close_price,
            'volume': record.volume,
            'change': record.price_change_percent
        } for record in data])
        
        print("\nMarket Summary:")
        print(df.describe())
        
    def __del__(self):
        try:
            self.db.close()
        except:
            pass

def main():
    print("Starting market data monitor...")
    monitor = DataMonitor()
    try:
        monitor.display_data()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()