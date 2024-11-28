#!/usr/bin/env python3

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from typing import Dict, List
import json

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.core.logging import logger
from app.models.historical import HistoricalMetrics
from app.models.market import TradingPair

class VolatilityDataChecker:
    def __init__(self):
        self.db = SessionLocal()
        self.findings = []
        
    def check_data(self, symbol: str, timeframe: str, days: int = 30):
        """執行全面數據檢查"""
        try:
            print(f"\nChecking volatility data for {symbol} {timeframe} last {days} days...")
            
            # 檢查重複數據
            self._check_duplicates(symbol, timeframe, days)
            
            # 檢查異常值
            self._check_anomalies(symbol, timeframe, days)
            
            # 檢查數據間隔
            self._check_data_gaps(symbol, timeframe, days)
            
            # 生成報告
            self._generate_report(symbol, timeframe)
            
        except Exception as e:
            logger.error(f"Error checking data: {e}")
            raise
        finally:
            self.db.close()
    
    def _check_duplicates(self, symbol: str, timeframe: str, days: int):
        """檢查重複數據"""
        query = text("""
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM historical_metrics hm
            JOIN trading_pairs tp ON hm.trading_pair_id = tp.id
            WHERE tp.symbol = :symbol 
            AND hm.timeframe = :timeframe
            AND timestamp >= NOW() - :days * INTERVAL '1 day'
            GROUP BY DATE(timestamp)
            HAVING COUNT(*) > 1
        """)
        
        results = self.db.execute(
            query, 
            {"symbol": symbol, "timeframe": timeframe, "days": days}
        ).fetchall()
        
        if results:
            self.findings.append({
                "type": "duplicates",
                "details": [
                    {"date": row.date.isoformat(), "count": row.count}
                    for row in results
                ]
            })
    
    def _check_anomalies(self, symbol: str, timeframe: str, days: int):
        """檢查異常值"""
        query = text("""
            SELECT 
                timestamp,
                volatility,
                volume
            FROM historical_metrics hm
            JOIN trading_pairs tp ON hm.trading_pair_id = tp.id
            WHERE tp.symbol = :symbol 
            AND hm.timeframe = :timeframe
            AND timestamp >= NOW() - :days * INTERVAL '1 day'
            AND (
                volatility = 0 
                OR volatility IS NULL
                OR volatility > 100
                OR volume = 0
                OR volume IS NULL
            )
        """)
        
        results = self.db.execute(
            query,
            {"symbol": symbol, "timeframe": timeframe, "days": days}
        ).fetchall()
        
        if results:
            self.findings.append({
                "type": "anomalies",
                "details": [
                    {
                        "timestamp": row.timestamp.isoformat(),
                        "volatility": row.volatility,
                        "volume": row.volume
                    }
                    for row in results
                ]
            })
    
    def _check_data_gaps(self, symbol: str, timeframe: str, days: int):
        """檢查數據間隔"""
        # 獲取預期的時間間隔(秒)
        interval_map = {"1h": 3600, "4h": 14400, "1d": 86400}
        expected_interval = interval_map.get(timeframe, 3600)
        
        query = text("""
            WITH timestamps AS (
                SELECT 
                    timestamp,
                    LEAD(timestamp) OVER (ORDER BY timestamp) as next_timestamp
                FROM historical_metrics hm
                JOIN trading_pairs tp ON hm.trading_pair_id = tp.id
                WHERE tp.symbol = :symbol 
                AND hm.timeframe = :timeframe
                AND timestamp >= NOW() - :days * INTERVAL '1 day'
            )
            SELECT 
                timestamp,
                next_timestamp,
                EXTRACT(EPOCH FROM (next_timestamp - timestamp)) as gap_seconds
            FROM timestamps
            WHERE next_timestamp IS NOT NULL
            AND EXTRACT(EPOCH FROM (next_timestamp - timestamp)) > :expected_interval
        """)
        
        results = self.db.execute(
            query,
            {
                "symbol": symbol, 
                "timeframe": timeframe, 
                "days": days,
                "expected_interval": expected_interval * 1.5  # 允許50%的誤差
            }
        ).fetchall()
        
        if results:
            self.findings.append({
                "type": "gaps",
                "details": [
                    {
                        "start": row.timestamp.isoformat(),
                        "end": row.next_timestamp.isoformat(),
                        "gap_hours": row.gap_seconds / 3600
                    }
                    for row in results
                ]
            })
    
    def _generate_report(self, symbol: str, timeframe: str):
        """生成檢查報告"""
        if not self.findings:
            print("No issues found! Data looks good.")
            return
            
        print("\nData Check Report")
        print("=" * 50)
        
        for finding in self.findings:
            print(f"\nIssue Type: {finding['type'].upper()}")
            print("-" * 30)
            
            if finding['type'] == 'duplicates':
                for detail in finding['details']:
                    print(f"Date: {detail['date']} - {detail['count']} records")
                    
            elif finding['type'] == 'anomalies':
                for detail in finding['details']:
                    print(
                        f"Timestamp: {detail['timestamp']} - "
                        f"Volatility: {detail['volatility']}, "
                        f"Volume: {detail['volume']}"
                    )
                    
            elif finding['type'] == 'gaps':
                for detail in finding['details']:
                    print(
                        f"Gap from {detail['start']} to {detail['end']} "
                        f"({detail['gap_hours']:.1f} hours)"
                    )
        
        # 保存報告到文件
        report_path = Path("data_check_reports")
        report_path.mkdir(exist_ok=True)
        
        filename = (
            f"volatility_check_{symbol}_{timeframe}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )
        
        with open(report_path / filename, 'w') as f:
            json.dump(
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": datetime.now().isoformat(),
                    "findings": self.findings
                },
                f,
                indent=2
            )

def main():
    checker = VolatilityDataChecker()
    
    # 檢查主要交易對
    symbols = ["BTCUSDT", "ETHUSDT"]
    timeframes = ["1h", "4h", "1d"]
    
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                checker.check_data(symbol, timeframe)
            except Exception as e:
                print(f"Error checking {symbol} {timeframe}: {e}")

if __name__ == "__main__":
    main()