import json
import asyncio
from typing import Dict, List, Callable, Optional
import websockets
from datetime import datetime, timedelta
from app.core.logging import logger

class BinanceWebSocket:
    def __init__(self):
        self.base_url = "wss://stream.binance.com:9443/ws"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.running = True
        self.health_metrics = {
            'start_time': datetime.now(),
            'messages_received': 0,
            'errors_count': 0,
            'last_message_time': None,
            'reconnect_count': 0
        }
        
    async def connect(self):
        """連接到 WebSocket"""
        try:
            self.websocket = await websockets.connect(
                self.base_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10
            )
            logger.info("Connected to Binance WebSocket")
            self.health_metrics['last_connect_time'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.health_metrics['errors_count'] += 1
            raise
    
    async def subscribe(self, streams: List[str]):
        """訂閱多個數據流"""
        if not self.websocket:
            await self.connect()
        
        try:
            # 如果是單個字符串，轉換為列表
            if isinstance(streams, str):
                streams = [streams]
                
            subscribe_message = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": len(self.subscriptions)
            }
            
            await self.websocket.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to streams: {streams}")
            
            # 初始化訂閱回調列表
            for stream in streams:
                if stream not in self.subscriptions:
                    self.subscriptions[stream] = []
                    
        except Exception as e:
            logger.error(f"Error subscribing to streams: {e}")
            self.health_metrics['errors_count'] += 1
            raise
    
    async def add_callback(self, stream: str, callback: Callable):
        """為特定數據流添加回調函數"""
        if stream not in self.subscriptions:
            self.subscriptions[stream] = []
        self.subscriptions[stream].append(callback)
    
    async def start_listening(self):
        """開始監聽數據流"""
        if not self.websocket:
            await self.connect()
            
        try:
            while self.running:
                try:
                    message = await self.websocket.recv()
                    self.health_metrics['messages_received'] += 1
                    self.health_metrics['last_message_time'] = datetime.now()
                    
                    data = json.loads(message)
                    
                    # 處理訂閱確認消息
                    if 'result' in data:
                        continue
                    
                    # 處理心跳消息
                    if 'ping' in data:
                        await self.websocket.send(json.dumps({"pong": data['ping']}))
                        continue
                    
                    # 處理數據消息
                    stream = data.get('stream')
                    if stream and stream in self.subscriptions:
                        for callback in self.subscriptions[stream]:
                            try:
                                await callback(data['data'])
                            except Exception as e:
                                logger.error(f"Error in callback for stream {stream}: {e}")
                                self.health_metrics['errors_count'] += 1
                    
                except websockets.ConnectionClosed:
                    logger.warning("WebSocket connection closed, attempting to reconnect...")
                    await self.reconnect()
                    
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {e}")
            self.health_metrics['errors_count'] += 1
            raise
        finally:
            await self.close()
    
    async def reconnect(self):
        """重新連接並重新訂閱"""
        try:
            self.health_metrics['reconnect_count'] += 1
            await self.connect()
            
            # 重新訂閱所有活動的數據流
            if self.subscriptions:
                streams = list(self.subscriptions.keys())
                await self.subscribe(streams)
                
        except Exception as e:
            logger.error(f"Failed to reconnect: {e}")
            self.health_metrics['errors_count'] += 1
            await asyncio.sleep(5)  # 等待5秒後重試
            raise
    
    async def unsubscribe(self, streams: List[str]):
        """取消訂閱數據流"""
        try:
            if isinstance(streams, str):
                streams = [streams]
                
            unsubscribe_message = {
                "method": "UNSUBSCRIBE",
                "params": streams,
                "id": len(self.subscriptions) + 1
            }
            
            await self.websocket.send(json.dumps(unsubscribe_message))
            
            # 移除訂閱回調
            for stream in streams:
                self.subscriptions.pop(stream, None)
                
        except Exception as e:
            logger.error(f"Error unsubscribing from streams: {e}")
            self.health_metrics['errors_count'] += 1
            raise
    
    async def close(self):
        """關閉 WebSocket 連接"""
        self.running = False
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None
                self.subscriptions.clear()

    def get_subscription_status(self) -> Dict:
        """獲取訂閱狀態"""
        return {
            'connected': self.websocket is not None and not self.websocket.closed,
            'subscriptions': list(self.subscriptions.keys()),
            'health_metrics': {
                'uptime': str(datetime.now() - self.health_metrics['start_time']),
                'messages_received': self.health_metrics['messages_received'],
                'errors_count': self.health_metrics['errors_count'],
                'last_message_time': self.health_metrics['last_message_time'],
                'reconnect_count': self.health_metrics['reconnect_count']
            }
        }

    def get_health_metrics(self) -> Dict:
        """獲取健康指標"""
        current_time = datetime.now()
        return {
            'uptime': str(current_time - self.health_metrics['start_time']),
            'messages_per_second': self._calculate_message_rate(),
            'error_rate': self._calculate_error_rate(),
            'connection_status': {
                'connected': self.websocket is not None and not self.websocket.closed,
                'last_message_age': str(current_time - (self.health_metrics['last_message_time'] or current_time)),
                'reconnect_count': self.health_metrics['reconnect_count']
            }
        }
    
    def _calculate_message_rate(self) -> float:
        """計算消息接收率"""
        uptime = (datetime.now() - self.health_metrics['start_time']).total_seconds()
        return self.health_metrics['messages_received'] / max(uptime, 1)
    
    def _calculate_error_rate(self) -> float:
        """計算錯誤率"""
        total_operations = self.health_metrics['messages_received'] + self.health_metrics['errors_count']
        return self.health_metrics['errors_count'] / max(total_operations, 1)