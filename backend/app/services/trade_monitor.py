# backend/app/services/trade_monitor.py

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.market import MarketData, OrderBook, TradingPair
from app.core.config import settings

@dataclass
class TradeAlert:
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    side: str  # 'buy' or 'sell'
    impact: float  # 價格影響百分比
    description: str

class LargeTradeMonitor:
    def __init__(self, db: Session):
        self.db = db
        self.alerts: List[TradeAlert] = []
        self.thresholds = {
            'BTCUSDT': {
                'volume': 10.0,  # BTC
                'impact': 0.5    # 0.5%
            },
            'ETHUSDT': {
                'volume': 100.0,  # ETH
                'impact': 0.5     # 0.5%
            }
        }
        self.running = True
    
    async def start_monitoring(self, symbols: List[str]):
        """啟動大額交易監控"""
        logger.info(f"Starting large trade monitoring for symbols: {symbols}")
        
        try:
            # 檢查數據可用性
            available_symbols = await self._check_data_availability(symbols)
            if not available_symbols:
                logger.error("No symbols have available data. Please ensure data collection is running.")
                return
            
            while self.running:
                for symbol in available_symbols:
                    await self._monitor_symbol(symbol)
                await asyncio.sleep(1)  # 每秒檢查一次
                
        except Exception as e:
            logger.error(f"Error in trade monitoring: {e}")
            raise
    
    async def stop_monitoring(self):
        """停止監控"""
        self.running = False
    
    async def _check_data_availability(self, symbols: List[str]) -> List[str]:
        """檢查哪些交易對有可用數據"""
        available_symbols = []
        for symbol in symbols:
            try:
                # 檢查是否有深度數據
                depth_data = self._get_latest_depth(symbol)
                if not depth_data:
                    logger.warning(f"No depth data found for {symbol}")
                    continue
                    
                # 檢查是否有最近的交易數據
                recent_trades = self._get_recent_trades(symbol)
                if not recent_trades:
                    logger.warning(f"No recent trade data found for {symbol}")
                    continue
                    
                available_symbols.append(symbol)
                
            except Exception as e:
                logger.error(f"Error checking data availability for {symbol}: {e}")
                
        return available_symbols
    
    async def _monitor_symbol(self, symbol: str):
        """監控單個交易對"""
        try:
            # 獲取最新深度數據
            depth = self._get_latest_depth(symbol)
            if not depth:
                return
                
            # 獲取最近的交易數據
            trades = self._get_recent_trades(symbol)
            if not trades:
                return
            
            # 分析大額交易
            threshold = self.thresholds.get(symbol, {'volume': 1.0, 'impact': 0.5})
            for trade in trades:
                if trade.volume >= threshold['volume']:
                    # 計算價格影響
                    impact = self._calculate_price_impact(
                        symbol, 
                        trade.price,  # 現在可以直接使用 price
                        trade.volume,
                        trade.side    # 現在可以直接使用 side
                    )
                    
                    if abs(impact) >= threshold['impact']:
                        alert = TradeAlert(
                            symbol=symbol,
                            timestamp=trade.timestamp,
                            price=trade.price,
                            volume=trade.volume,
                            side=trade.side,
                            impact=impact,
                            description=f"Large {trade.side} trade detected: {trade.volume} {symbol[:3]} at {trade.price}"
                        )
                        
                        await self._handle_alert(alert)
            
        except Exception as e:
            logger.error(f"Error monitoring {symbol}: {e}")
    
    def _get_latest_depth(self, symbol: str) -> Optional[OrderBook]:
        """獲取最新深度數據"""
        query = (
            select(OrderBook)
            .join(OrderBook.trading_pair)
            .where(
                and_(
                    TradingPair.symbol == symbol,
                    OrderBook.timestamp >= datetime.now() - timedelta(minutes=5)
                )
            )
            .order_by(OrderBook.timestamp.desc())
            .limit(1)
        )
        
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def _get_recent_trades(self, symbol: str, minutes: int = 5) -> List[MarketData]:
        """獲取最近的交易數據"""
        query = (
            select(MarketData)
            .join(MarketData.trading_pair)
            .where(
                and_(
                    TradingPair.symbol == symbol,
                    MarketData.timestamp >= datetime.now() - timedelta(minutes=minutes)
                )
            )
            .order_by(MarketData.timestamp.desc())
        )
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    def _calculate_price_impact(
        self, 
        symbol: str, 
        price: float, 
        volume: float, 
        side: str
    ) -> float:
        """計算價格影響"""
        try:
            depth = self._get_latest_depth(symbol)
            if not depth:
                return 0.0
            
            # 獲取當前中間價格
            best_bid = float(depth.bids[0][0]) if depth.bids else 0
            best_ask = float(depth.asks[0][0]) if depth.asks else 0
            mid_price = (best_bid + best_ask) / 2
            
            if mid_price == 0:
                return 0.0
            
            # 計算價格偏離
            price_deviation = ((price - mid_price) / mid_price) * 100
            
            # 根據交易方向調整符號
            if side == 'sell' and price_deviation > 0:
                price_deviation = -price_deviation
            elif side == 'buy' and price_deviation < 0:
                price_deviation = -price_deviation
            
            return price_deviation
            
        except Exception as e:
            logger.error(f"Error calculating price impact: {e}")
            return 0.0
    
    async def _handle_alert(self, alert: TradeAlert):
        """處理告警"""
        # 添加到告警列表
        self.alerts.append(alert)
        
        # 記錄告警
        logger.warning(
            f"Large Trade Alert - {alert.symbol}: "
            f"{alert.volume} {'bought' if alert.side == 'buy' else 'sold'} "
            f"at {alert.price} (Impact: {alert.impact:.2f}%)"
        )
        
        # TODO: 實現更多告警處理邏輯，如：
        # - 發送郵件通知
        # - 發送Webhook
        # - 保存到數據庫
        # - 觸發交易策略等
    
    def get_recent_alerts(self, minutes: int = 60) -> List[TradeAlert]:
        """獲取最近的告警"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            alert for alert in self.alerts 
            if alert.timestamp >= cutoff_time
        ]
    
    def get_alert_summary(self) -> Dict:
        """獲取告警摘要"""
        recent_alerts = self.get_recent_alerts()
        if not recent_alerts:
            return {}
        
        summary = {}
        for alert in recent_alerts:
            if alert.symbol not in summary:
                summary[alert.symbol] = {
                    'count': 0,
                    'total_volume': 0,
                    'avg_impact': 0,
                    'max_impact': 0
                }
            
            s = summary[alert.symbol]
            s['count'] += 1
            s['total_volume'] += alert.volume
            s['avg_impact'] = (s['avg_impact'] * (s['count'] - 1) + alert.impact) / s['count']
            s['max_impact'] = max(s['max_impact'], abs(alert.impact))
        
        return summary