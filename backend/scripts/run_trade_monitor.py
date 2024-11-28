# backend/scripts/run_trade_monitor.py

import asyncio
import sys
from pathlib import Path
import signal
import argparse
from datetime import datetime
from typing import List, Optional

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.trade_monitor import LargeTradeMonitor
from app.core.logging import logger

class TradeMonitorController:
    def __init__(self):
        self.db = SessionLocal()
        self.monitor: Optional[LargeTradeMonitor] = None
        self.should_stop = False
    
    def signal_handler(self, signum, frame):
        """處理停止信號"""
        logger.info("\nReceived stop signal. Shutting down gracefully...")
        self.should_stop = True
        if self.monitor:
            asyncio.create_task(self.monitor.stop_monitoring())
    
    async def start_monitoring(self, symbols: List[str], alert_thresholds: dict = None):
        """啟動交易監控"""
        try:
            # 註冊信號處理
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            # 初始化監控器
            self.monitor = LargeTradeMonitor(self.db)
            
            # 如果提供了閾值，則更新
            if alert_thresholds:
                self.monitor.thresholds.update(alert_thresholds)
            
            logger.info(f"Starting trade monitor for symbols: {symbols}")
            logger.info("Alert thresholds:")
            for symbol, threshold in self.monitor.thresholds.items():
                if symbol in symbols:
                    logger.info(f"  {symbol}: volume >= {threshold['volume']}, "
                              f"impact >= {threshold['impact']}%")
            
            # 啟動監控
            await self.monitor.start_monitoring(symbols)
            
        except Exception as e:
            logger.error(f"Error in trade monitor: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理資源"""
        try:
            if hasattr(self, 'db') and self.db:
                self.db.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def print_status(self):
        """顯示監控狀態"""
        if not self.monitor:
            return
        
        alerts = self.monitor.get_recent_alerts(minutes=60)
        summary = self.monitor.get_alert_summary()
        
        logger.info("\nMonitoring Status:")
        logger.info(f"Total alerts in the last hour: {len(alerts)}")
        
        if summary:
            logger.info("\nAlert Summary by Symbol:")
            for symbol, stats in summary.items():
                logger.info(f"\n{symbol}:")
                logger.info(f"  Total alerts: {stats['count']}")
                logger.info(f"  Total volume: {stats['total_volume']:.2f}")
                logger.info(f"  Average impact: {stats['avg_impact']:.2f}%")
                logger.info(f"  Maximum impact: {stats['max_impact']:.2f}%")
        
        if alerts:
            logger.info("\nRecent Alerts:")
            for alert in alerts[-5:]:  # 只顯示最後5個告警
                logger.info(
                    f"[{alert.timestamp.strftime('%H:%M:%S')}] {alert.symbol}: "
                    f"{alert.volume:.2f} {alert.side} @ {alert.price:.2f} "
                    f"(Impact: {alert.impact:.2f}%)"
                )

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='Crypto trade monitor')
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['BTCUSDT', 'ETHUSDT'],
        help='Trading symbols to monitor'
    )
    parser.add_argument(
        '--btc-threshold',
        type=float,
        default=10.0,
        help='BTC trade volume threshold'
    )
    parser.add_argument(
        '--eth-threshold',
        type=float,
        default=100.0,
        help='ETH trade volume threshold'
    )
    parser.add_argument(
        '--impact-threshold',
        type=float,
        default=0.5,
        help='Price impact threshold (percentage)'
    )
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    # 準備閾值設置
    alert_thresholds = {
        'BTCUSDT': {
            'volume': args.btc_threshold,
            'impact': args.impact_threshold
        },
        'ETHUSDT': {
            'volume': args.eth_threshold,
            'impact': args.impact_threshold
        }
    }
    
    controller = TradeMonitorController()
    try:
        await controller.start_monitoring(args.symbols, alert_thresholds)
        
    except KeyboardInterrupt:
        logger.info("Stopping trade monitor...")
        if controller.monitor:
            controller.print_status()
    except Exception as e:
        logger.error(f"Error in trade monitor: {e}")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)