# app/core/cache_strategies.py

from typing import Optional, Dict, Any
from datetime import timedelta
import hashlib
import json

from .cache import CacheManager
from .logging import logger

class MarketDataCache:
    """市場數據緩存策略"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.default_ttl = timedelta(minutes=5)
    
    def _generate_key(self, symbol: str, timeframe: str, **params) -> str:
        """生成緩存鍵"""
        # 對參數進行排序以確保一致性
        param_str = json.dumps(sorted(params.items()))
        key_base = f"market:{symbol}:{timeframe}:{param_str}"
        return hashlib.md5(key_base.encode()).hexdigest()
    
    async def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        **params
    ) -> Optional[Dict[str, Any]]:
        """獲取市場數據緩存"""
        key = self._generate_key(symbol, timeframe, **params)
        return await self.cache.get(key)
    
    async def set_market_data(
        self,
        symbol: str,
        timeframe: str,
        data: Dict[str, Any],
        ttl: Optional[timedelta] = None,
        **params
    ) -> bool:
        """設置市場數據緩存"""
        key = self._generate_key(symbol, timeframe, **params)
        return await self.cache.set(key, data, expire=ttl or self.default_ttl)
    
    async def invalidate_symbol_data(self, symbol: str) -> int:
        """清除指定交易對的所有緩存"""
        return await self.cache.clear_prefix(f"market:{symbol}")

class RateLimiter:
    """API速率限制器"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.window = 60  # 60秒窗口
        self.max_requests = 1200  # 每分鐘最大請求數
    
    async def check_rate_limit(self, api_key: str) -> bool:
        """檢查是否超過速率限制"""
        key = f"ratelimit:{api_key}"
        current = await self.cache.increment(key)
        
        if current == 1:
            # 第一次請求，設置過期時間
            await self.cache.expire(key, self.window)
            
        return current <= self.max_requests
    
    async def get_remaining_requests(self, api_key: str) -> int:
        """獲取剩餘可用請求數"""
        key = f"ratelimit:{api_key}"
        current = await self.cache.get(key, 0)
        return max(0, self.max_requests - int(current))

class OrderBookCache:
    """訂單簿緩存策略"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.default_ttl = timedelta(seconds=30)
    
    async def get_order_book(
        self,
        symbol: str,
        depth: int = 100
    ) -> Optional[Dict[str, Any]]:
        """獲取訂單簿緩存"""
        key = f"orderbook:{symbol}:{depth}"
        return await self.cache.get(key)
    
    async def set_order_book(
        self,
        symbol: str,
        data: Dict[str, Any],
        depth: int = 100,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """設置訂單簿緩存"""
        key = f"orderbook:{symbol}:{depth}"
        return await self.cache.set(key, data, expire=ttl or self.default_ttl)
    
    async def update_order_book(
        self,
        symbol: str,
        updates: Dict[str, Any],
        depth: int = 100
    ) -> bool:
        """更新訂單簿緩存"""
        try:
            key = f"orderbook:{symbol}:{depth}"
            current = await self.cache.get(key, {})
            
            if not current:
                return False
            
            # 更新買賣單
            if 'bids' in updates:
                current['bids'].update(updates['bids'])
            if 'asks' in updates:
                current['asks'].update(updates['asks'])
            
            return await self.cache.set(
                key,
                current,
                expire=self.default_ttl
            )
            
        except Exception as e:
            logger.error(f"Error updating order book cache: {e}")
            return False