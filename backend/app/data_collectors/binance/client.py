# backend/app/data_collectors/binance/client.py
from typing import Dict, Optional, List
import hmac
import hashlib
import time
from urllib.parse import urlencode
import backoff
import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import logger

class BinanceClient:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.api_key = settings.BINANCE_API_KEY
        self.api_secret = settings.BINANCE_API_SECRET
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _generate_signature(self, params: Dict) -> str:
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, TimeoutError),
        max_tries=3
    )
    async def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """通用請求方法，包含重試機制"""
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key} if self.api_key else {}
        
        try:
            response = await self.client.request(
                method,
                url,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            raise HTTPException(status_code=response.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"Error making request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_exchange_info(self) -> Dict:
        """獲取交易所規則和交易對信息"""
        return await self._make_request("GET", "/api/v3/exchangeInfo")
    
    async def get_ticker_24h(self, symbol: Optional[str] = None) -> Dict:
        """獲取24小時價格變動情況"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return await self._make_request("GET", "/api/v3/ticker/24hr", params)
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """獲取訂單簿數據"""
        params = {'symbol': symbol, 'limit': limit}
        return await self._make_request("GET", "/api/v3/depth", params)

    async def get_klines(self, symbol: str, interval: str, limit: int = 500) -> List:
        """獲取K線數據
        intervals: 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return await self._make_request("GET", "/api/v3/klines", params)