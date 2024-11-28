# backend/app/data_collectors/binance/depth_collector.py

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json

from app.core.logging import logger
from app.models.market import OrderBook
from sqlalchemy.orm import Session

class DepthDataManager:
    def __init__(self, db: Session):
        self.db = db
        self.depth_cache: Dict[str, Dict] = {}
        self.last_update_id: Dict[str, int] = {}
        
    async def process_depth_update(self, symbol: str, data: Dict):
        """處理深度數據更新"""
        try:
            # 確保數據有效性
            if not self._validate_depth_data(data):
                logger.warning(f"Invalid depth data received for {symbol}")
                return
                
            # 更新本地緩存
            self._update_depth_cache(symbol, data)
            
            # 創建訂單簿記錄
            order_book = OrderBook(
                trading_pair_id=self._get_trading_pair_id(symbol),
                timestamp=datetime.now(),
                bids=data.get('b', []),  # Binance格式的買單
                asks=data.get('a', []),  # Binance格式的賣單
                last_update_id=data.get('u', 0)  # 最後更新ID
            )
            
            self.db.add(order_book)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing depth update for {symbol}: {e}")
            await self.db.rollback()
    
    def _validate_depth_data(self, data: Dict) -> bool:
        """驗證深度數據的有效性"""
        required_fields = ['u', 'b', 'a']  # u: updateId, b: bids, a: asks
        return all(field in data for field in required_fields)
    
    def _update_depth_cache(self, symbol: str, data: Dict):
        """更新深度數據緩存"""
        if symbol not in self.depth_cache:
            self.depth_cache[symbol] = {'bids': {}, 'asks': {}}
            
        # 更新買單
        for bid in data.get('b', []):
            price, quantity = float(bid[0]), float(bid[1])
            if quantity > 0:
                self.depth_cache[symbol]['bids'][price] = quantity
            else:
                self.depth_cache[symbol]['bids'].pop(price, None)
                
        # 更新賣單
        for ask in data.get('a', []):
            price, quantity = float(ask[0]), float(ask[1])
            if quantity > 0:
                self.depth_cache[symbol]['asks'][price] = quantity
            else:
                self.depth_cache[symbol]['asks'].pop(price, None)
                
        # 更新最後更新ID
        self.last_update_id[symbol] = data.get('u', 0)
    
    def get_current_depth(self, symbol: str) -> Dict:
        """獲取當前深度數據"""
        if symbol not in self.depth_cache:
            return {'bids': [], 'asks': []}
            
        cache = self.depth_cache[symbol]
        
        # 轉換為排序後的列表格式
        bids = sorted(
            [[price, qty] for price, qty in cache['bids'].items()],
            key=lambda x: x[0],
            reverse=True
        )
        asks = sorted(
            [[price, qty] for price, qty in cache['asks'].items()],
            key=lambda x: x[0]
        )
        
        return {
            'bids': bids[:20],  # 只返回前20檔
            'asks': asks[:20],
            'lastUpdateId': self.last_update_id.get(symbol, 0)
        }
    
    def clear_depth_cache(self, symbol: str):
        """清除深度數據緩存"""
        self.depth_cache.pop(symbol, None)
        self.last_update_id.pop(symbol, None)
    
    def _get_trading_pair_id(self, symbol: str) -> int:
        """獲取交易對ID（需要實現）"""
        # TODO: 實現從資料庫獲取交易對ID的邏輯
        pass