# app/monitoring/depth_monitor.py

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass
import json

from app.core.logging import logger
from app.core.config import settings
from app.models.market import OrderBookDepth
from sqlalchemy import select, func
from sqlalchemy.orm import Session

@dataclass
class DepthMetrics:
    symbol: str
    timestamp: datetime
    bid_ask_ratio: float
    spread: float
    depth_coverage: float
    update_latency: float
    processing_time: float
    error_rate: float

class DepthMonitor:
    def __init__(self, db: Session, websocket_client):
        self.db = db
        self.websocket = websocket_client
        self.metrics_history: Dict[str, List[DepthMetrics]] = {}
        self.alert_thresholds = {
            'max_spread': 0.01,           # 最大價差 1%
            'min_depth_coverage': 0.8,     # 最小深度覆蓋率 80%
            'max_update_latency': 1000,    # 最大更新延遲 1000ms
            'max_processing_time': 100,    # 最大處理時間 100ms
            'max_error_rate': 0.01         # 最大錯誤率 1%
        }
    
    async def start_monitoring(self, symbols: List[str], interval: int = 60):
        """啟動監控"""
        while True:
            try:
                for symbol in symbols:
                    metrics = await self.collect_metrics(symbol)
                    await self.analyze_metrics(metrics)
                    self.update_metrics_history(metrics)
                
                # 定期清理歷史數據
                self.cleanup_old_metrics()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in depth monitoring: {e}")
                await asyncio.sleep(5)
    
    async def collect_metrics(self, symbol: str) -> DepthMetrics:
        """收集深度數據指標"""
        try:
            # 獲取最新深度數據
            latest_depth = await self._get_latest_depth(symbol)
            
            # 計算買賣比例
            bid_volume = sum(float(bid[1]) for bid in latest_depth.bids)
            ask_volume = sum(float(ask[1]) for ask in latest_depth.asks)
            bid_ask_ratio = bid_volume / ask_volume if ask_volume > 0 else 0
            
            # 計算深度覆蓋率
            expected_levels = settings.DEPTH_LEVELS
            actual_levels = len(latest_depth.bids) + len(latest_depth.asks)
            depth_coverage = actual_levels / (2 * expected_levels)
            
            # 獲取WebSocket指標
            ws_metrics = self.websocket.get_health_metrics()
            stream_name = f"{symbol.lower()}@depth"
            stream_metrics = ws_metrics['connections'].get(stream_name, {})
            
            # 計算更新延遲
            current_time = datetime.now().timestamp()
            last_message_time = stream_metrics.get('last_message', current_time)
            update_latency = (current_time - last_message_time) * 1000
            
            # 計算錯誤率
            message_count = stream_metrics.get('message_count', 0)
            error_count = stream_metrics.get('error_count', 0)
            error_rate = error_count / message_count if message_count > 0 else 0
            
            return DepthMetrics(
                symbol=symbol,
                timestamp=datetime.now(),
                bid_ask_ratio=bid_ask_ratio,
                spread=latest_depth.spread,
                depth_coverage=depth_coverage,
                update_latency=update_latency,
                processing_time=latest_depth.processing_time,
                error_rate=error_rate
            )
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {symbol}: {e}")
            raise
    
    async def analyze_metrics(self, metrics: DepthMetrics):
        """分析指標並觸發告警"""
        alerts = []
        
        # 檢查價差
        if metrics.spread > self.alert_thresholds['max_spread']:
            alerts.append(f"High spread detected: {metrics.spread:.2%}")
        
        # 檢查深度覆蓋率
        if metrics.depth_coverage < self.alert_thresholds['min_depth_coverage']:
            alerts.append(f"Low depth coverage: {metrics.depth_coverage:.2%}")
        
        # 檢查更新延遲
        if metrics.update_latency > self.alert_thresholds['max_update_latency']:
            alerts.append(f"High update latency: {metrics.update_latency:.2f}ms")
        
        # 檢查處理時間
        if metrics.processing_time > self.alert_thresholds['max_processing_time']:
            alerts.append(f"High processing time: {metrics.processing_time:.2f}ms")
        
        # 檢查錯誤率
        if metrics.error_rate > self.alert_thresholds['max_error_rate']:
            alerts.append(f"High error rate: {metrics.error_rate:.2%}")
        
        # 發送告警
        if alerts:
            await self._send_alerts(metrics.symbol, alerts)
    
    async def _send_alerts(self, symbol: str, alerts: List[str]):
        """發送告警信息"""
        alert_message = f"Alerts for {symbol} at {datetime.now()}:\n" + "\n".join(alerts)
        logger.warning(alert_message)
        
        # TODO: 實現具體的告警發送機制（例如郵件、Slack等）
    
# app/monitoring/depth_monitor.py (續)

    async def _get_latest_depth(self, symbol: str) -> OrderBookDepth:
        """獲取最新深度數據"""
        query = select(OrderBookDepth).filter(
            OrderBookDepth.trading_pair.has(symbol=symbol)
        ).order_by(
            OrderBookDepth.timestamp.desc()
        ).limit(1)
        
        result = await self.db.execute(query)
        depth = result.scalar_one_or_none()
        
        if not depth:
            raise ValueError(f"No depth data found for {symbol}")
        
        return depth
    
    def update_metrics_history(self, metrics: DepthMetrics):
        """更新指標歷史"""
        if metrics.symbol not in self.metrics_history:
            self.metrics_history[metrics.symbol] = []
        
        history = self.metrics_history[metrics.symbol]
        history.append(metrics)
        
        # 只保留最近24小時的數據
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history[metrics.symbol] = [
            m for m in history if m.timestamp > cutoff_time
        ]
    
    def get_metrics_summary(self, symbol: str) -> Dict:
        """獲取指標摘要"""
        if symbol not in self.metrics_history:
            return {}
        
        metrics = self.metrics_history[symbol]
        if not metrics:
            return {}
        
        # 計算統計數據
        spreads = [m.spread for m in metrics]
        latencies = [m.update_latency for m in metrics]
        processing_times = [m.processing_time for m in metrics]
        
        return {
            'spread': {
                'current': metrics[-1].spread,
                'mean': statistics.mean(spreads),
                'max': max(spreads),
                'min': min(spreads)
            },
            'latency': {
                'current': metrics[-1].update_latency,
                'mean': statistics.mean(latencies),
                'max': max(latencies),
                'min': min(latencies)
            },
            'processing_time': {
                'current': metrics[-1].processing_time,
                'mean': statistics.mean(processing_times),
                'max': max(processing_times),
                'min': min(processing_times)
            },
            'depth_coverage': metrics[-1].depth_coverage,
            'error_rate': metrics[-1].error_rate,
            'last_update': metrics[-1].timestamp.isoformat()
        }
    
    def cleanup_old_metrics(self):
        """清理舊的指標數據"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        for symbol in self.metrics_history:
            self.metrics_history[symbol] = [
                m for m in self.metrics_history[symbol]
                if m.timestamp > cutoff_time
            ]