# backend/scripts/test_historical.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.data_collectors.binance.historical_collector import HistoricalDataCollector
from app.services.historical.data_service import HistoricalDataService

def test_historical_data():
    db = SessionLocal()
    try:
        # 1. 收集歷史數據
        print("Collecting historical data...")
        collector = HistoricalDataCollector(db)
        
        # 收集BTCUSDT的1小時和4小時K線數據
        for timeframe in ['1h', '4h']:
            data = collector.collect_historical_data(
                symbol="BTCUSDT",
                timeframe=timeframe,
                start_time=datetime.now() - timedelta(days=30)  # 獲取30天數據
            )
            print(f"Collected {len(data)} {timeframe} klines for BTCUSDT")
        
        collector.close()

        # 2. 分析數據
        print("\nAnalyzing data...")
        service = HistoricalDataService(db)
        
        # 分析1小時數據
        analysis_1h = service.analyze_volatility(
            symbol="BTCUSDT",
            timeframe="1h",
            start_time=datetime.now() - timedelta(days=30)
        )
        
        print("\n1h Analysis Results:")
        print(f"Market Regime: {analysis_1h['market_regime']}")
        print(f"Market Score: {analysis_1h['market_score']}")
        print(f"Volatility Regime: {analysis_1h['regime_analysis']['regime']}")
        print(f"Trend Direction: {analysis_1h['trend_analysis']['direction']}")
        
        # 獲取最近的市場分析結果
        recent_analysis = service.get_market_analysis(
            symbol="BTCUSDT",
            timeframe="1h",
            limit=5
        )
        
        print("\nRecent Market Analysis:")
        for analysis in recent_analysis:
            print(f"Time: {analysis['timestamp']}")
            print(f"Regime: {analysis['market_regime']}")
            print(f"Score: {analysis['market_score']}")
            print("---")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_historical_data()