# app/core/cache.py

from typing import Any, Optional, Union
from datetime import timedelta
import json
import pickle
from redis import Redis
from redis.client import Pipeline
from redis.exceptions import RedisError

from .config import settings
from .logging import logger

class CacheManager:
    """Redis緩存管理器"""
    
    def __init__(self):
        self.client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_timeout=5,
            retry_on_timeout=True
        )
        self.prefix = "crypto:"
        self._test_connection()
    
    def _test_connection(self) -> None:
        """測試Redis連接"""
        try:
            self.client.ping()
        except RedisError as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def _build_key(self, key: str) -> str:
        """生成帶前綴的鍵名"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """獲取緩存值"""
        try:
            full_key = self._build_key(key)
            value = await self.client.get(full_key)
            
            if value is None:
                return default
                
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return pickle.loads(value)
                
        except RedisError as e:
            logger.error(f"Error getting cache for {key}: {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """設置緩存值"""
        try:
            full_key = self._build_key(key)
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            else:
                value = pickle.dumps(value)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                    
                await self.client.setex(full_key, expire, value)
            else:
                await self.client.set(full_key, value)
                
            return True
            
        except RedisError as e:
            logger.error(f"Error setting cache for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """刪除緩存"""
        try:
            full_key = self._build_key(key)
            return bool(await self.client.delete(full_key))
        except RedisError as e:
            logger.error(f"Error deleting cache for {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        try:
            full_key = self._build_key(key)
            return await self.client.exists(full_key)
        except RedisError as e:
            logger.error(f"Error checking existence for {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """增加計數器值"""
        try:
            full_key = self._build_key(key)
            return await self.client.incrby(full_key, amount)
        except RedisError as e:
            logger.error(f"Error incrementing counter for {key}: {e}")
            return 0
    
    async def pipeline(self) -> Pipeline:
        """獲取管道以進行批量操作"""
        return self.client.pipeline()
    
    async def clear_prefix(self, prefix: str) -> int:
        """清除指定前綴的所有鍵"""
        try:
            pattern = f"{self.prefix}{prefix}*"
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Error clearing keys with prefix {prefix}: {e}")
            return 0
    
    def close(self) -> None:
        """關閉Redis連接"""
        try:
            self.client.close()
        except RedisError as e:
            logger.error(f"Error closing Redis connection: {e}")
            
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()