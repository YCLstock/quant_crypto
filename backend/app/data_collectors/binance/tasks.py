# backend/app/data_collectors/binance/tasks.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.core.logging import logger
from app.models.market import MarketData, OrderBook, TradingPair
from .collector import BinanceDataCollector
from .websocket import BinanceWebSocket

class DataCollectionTasks:
    def __init__(self):
        self.db: Session = SessionLocal()
        self.collector = BinanceDataCollector(self.db)
        self.websocket = BinanceWebSocket()
        self.running = False
        self.active_symbols: Set[str] = set()
        self.last_health_check = datetime.now()
        self.health_check_interval = timedelta(minutes=5)
        
    async def start_collection(self, symbols: Optional[List[str]] = None):
        """啟動數據採集任務"""
        self.running = True
        self.active_symbols = set(symbols) if symbols else set()
        
        try:
            # 首先更新交易對信息
            await self.collector.collect_trading_pairs()
            
            # 啟動各個採集任務
            tasks = [
                asyncio.create_task(self._run_market_data_collection()),
                asyncio.create_task(self._run_order_book_collection()),
                asyncio.create_task(self._run_websocket_collection()),
                asyncio.create_task(self._run_health_check())
            ]
            
            # 等待所有任務完成
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error in data collection: {str(e)}")
            raise
        finally:
            self.db.close()
    
    async def stop_collection(self):
        """停止數據採集"""
        self.running = False
        await self.websocket.close()
    
    async def _run_market_data_collection(self):
        """運行市場數據採集"""
        while self.running:
            try:
                symbols = list(self.active_symbols) if self.active_symbols else None
                await self.collector.collect_market_data(symbols)
                logger.info(f"Market data collected for {len(self.active_symbols) if symbols else 'all'} symbols")
                await asyncio.sleep(60)  # 每分鐘更新一次
                
            except Exception as e:
                logger.error(f"Error in market data collection: {str(e)}")
                await asyncio.sleep(5)  # 錯誤後等待5秒重試
    
    async def _run_order_book_collection(self):
        """運行訂單簿數據採集"""
        while self.running:
            try:
                if self.active_symbols:
                    await self.collector.collect_order_books(list(self.active_symbols))
                    logger.info(f"Order books collected for {len(self.active_symbols)} symbols")
                await asyncio.sleep(5)  # 每5秒更新一次
                
            except Exception as e:
                logger.error(f"Error in order book collection: {str(e)}")
                await asyncio.sleep(2)  # 錯誤後等待2秒重試
    
    async def _run_websocket_collection(self):
        """運行WebSocket數據採集"""
        while self.running:
            try:
                await self.websocket.connect()
                
                # 構建訂閱列表
                subscriptions = []
                for symbol in self.active_symbols:
                    symbol_lower = symbol.lower()
                    subscriptions.extend([
                        f"{symbol_lower}@trade",
                        f"{symbol_lower}@ticker",
                        f"{symbol_lower}@depth20@100ms"
                    ])
                
                # 訂閱數據流
                if subscriptions:
                    await self.websocket.subscribe(subscriptions)
                    
                    # 添加數據處理回調
                    for stream in subscriptions:
                        if '@trade' in stream:
                            await self.websocket.add_callback(
                                stream,
                                self._handle_trade_message
                            )
                        elif '@ticker' in stream:
                            await self.websocket.add_callback(
                                stream,
                                self._handle_ticker_message
                            )
                        elif '@depth' in stream:
                            await self.websocket.add_callback(
                                stream,
                                self._handle_depth_message
                            )
                    
                    # 開始監聽
                    await self.websocket.start_listening()
                
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await asyncio.sleep(5)  # 錯誤後等待5秒重試
                
        # 關閉連接
        await self.websocket.close()

    async def _handle_trade_message(self, data: Dict):
        """處理交易消息"""
        try:
            symbol = data.get('s')  # 交易對符號
            if not symbol or symbol not in self.active_symbols:
                return
                
            # 創建交易記錄
            trade_data = MarketData(
                trading_pair_id=self._get_trading_pair_id(symbol),
                timestamp=datetime.fromtimestamp(data['T'] / 1000),  # 轉換時間戳
                price=float(data['p']),
                volume=float(data['q']),
                is_buyer_maker=data['m']
            )
            
            self.db.add(trade_data)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing trade message: {e}")
            await self.db.rollback()

    async def _handle_ticker_message(self, data: Dict):
        """處理行情消息"""
        try:
            symbol = data.get('s')  # 交易對符號
            if not symbol or symbol not in self.active_symbols:
                return
                
            # 更新市場數據
            market_data = MarketData(
                trading_pair_id=self._get_trading_pair_id(symbol),
                timestamp=datetime.fromtimestamp(data['E'] / 1000),
                open_price=float(data['o']),
                high_price=float(data['h']),
                low_price=float(data['l']),
                close_price=float(data['c']),
                volume=float(data['v']),
                quote_volume=float(data['q']),
                number_of_trades=int(data['n'])
            )
            
            self.db.add(market_data)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing ticker message: {e}")
            await self.db.rollback()

# backend/app/data_collectors/binance/tasks.py (continued)

    async def _handle_depth_message(self, data: Dict):
        """處理深度消息"""
        try:
            symbol = data.get('s')  # 交易對符號
            if not symbol or symbol not in self.active_symbols:
                return
                
            # 創建訂單簿記錄
            order_book = OrderBook(
                trading_pair_id=self._get_trading_pair_id(symbol),
                timestamp=datetime.fromtimestamp(data['E'] / 1000),
                bids=data['b'],  # 買單列表
                asks=data['a'],  # 賣單列表
                last_update_id=data['u']  # 最後更新ID
            )
            
            self.db.add(order_book)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing depth message: {e}")
            await self.db.rollback()
    
    async def _run_health_check(self):
        """運行健康檢查"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # 每5分鐘執行一次健康檢查
                if current_time - self.last_health_check >= self.health_check_interval:
                    await self._perform_health_check()
                    self.last_health_check = current_time
                
                await asyncio.sleep(60)  # 每分鐘檢查一次時間
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(5)
    
    async def _perform_health_check(self):
        """執行健康檢查"""
        try:
            # 檢查 WebSocket 連接狀態
            ws_status = self.websocket.get_subscription_status()
            if not ws_status['connected']:
                logger.warning("WebSocket connection lost, attempting to reconnect...")
                await self.websocket.reconnect()
            
            # 檢查數據延遲
            metrics = self.websocket.get_health_metrics()
            if metrics['connection_status']['last_message_age'] > timedelta(minutes=1):
                logger.warning("Data delay detected, checking connection...")
                await self.websocket.reconnect()
            
            # 檢查錯誤率
            if metrics['error_rate'] > 0.1:  # 錯誤率超過10%
                logger.warning(f"High error rate detected: {metrics['error_rate']:.2%}")
            
            # 檢查消息處理率
            if metrics['messages_per_second'] < 0.1:  # 每秒消息少於0.1條
                logger.warning(f"Low message rate: {metrics['messages_per_second']:.2f} msgs/sec")
            
            # 檢查數據庫連接
            try:
                self.db.execute("SELECT 1")
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                self._reconnect_database()
            
            logger.info("Health check completed successfully")
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
    
    def _reconnect_database(self):
        """重新連接數據庫"""
        try:
            self.db.close()
            self.db = SessionLocal()
            logger.info("Database connection restored")
        except Exception as e:
            logger.error(f"Error reconnecting to database: {e}")
    
    def _get_trading_pair_id(self, symbol: str) -> int:
        """獲取交易對ID"""
        try:
            trading_pair = self.db.query(TradingPair).filter_by(
                symbol=symbol,
                is_active=1
            ).first()
            
            if not trading_pair:
                raise ValueError(f"Trading pair not found: {symbol}")
                
            return trading_pair.id
            
        except Exception as e:
            logger.error(f"Error getting trading pair ID for {symbol}: {e}")
            raise

    @staticmethod
    async def run_quick_test(symbols: List[str] = None):
        """運行快速測試"""
        if not symbols:
            symbols = ['BTCUSDT', 'ETHUSDT']
            
        tasks = DataCollectionTasks()
        try:
            logger.info(f"Starting quick test for symbols: {symbols}")
            
            # 測試交易對收集
            await tasks.collector.collect_trading_pairs()
            
            # 測試市場數據收集
            market_data = await tasks.collector.collect_market_data(symbols)
            logger.info(f"Collected {len(market_data)} market data records")
            
            # 測試訂單簿收集
            order_books = await tasks.collector.collect_order_books(symbols)
            logger.info(f"Collected {len(order_books)} order book records")
            
            # 測試 WebSocket 連接
            await tasks.websocket.connect()
            subscription = f"{symbols[0].lower()}@trade"
            await tasks.websocket.subscribe(subscription)
            logger.info("WebSocket connection test passed")
            
            # 關閉連接
            await tasks.websocket.close()
            
            logger.info("Quick test completed successfully")
            
        except Exception as e:
            logger.error(f"Error during quick test: {e}")
        finally:
            tasks.db.close()
    
    async def get_collection_status(self) -> Dict:
        """獲取數據收集狀態"""
        try:
            status = {
                'active_symbols': list(self.active_symbols),
                'running': self.running,
                'websocket': self.websocket.get_subscription_status(),
                'health_metrics': self.websocket.get_health_metrics(),
                'last_health_check': self.last_health_check.isoformat(),
                'database_connected': True
            }
            
            # 獲取最新數據統計
            latest_market_data = self.db.query(
                TradingPair.symbol,
                func.max(MarketData.timestamp).label('last_update'),
                func.count(MarketData.id).label('total_records')
            ).join(MarketData.trading_pair).group_by(TradingPair.symbol).all()
            
            status['market_data'] = {
                record.symbol: {
                    'last_update': record.last_update.isoformat(),
                    'total_records': record.total_records
                }
                for record in latest_market_data
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting collection status: {e}")
            return {
                'error': str(e),
                'running': self.running,
                'active_symbols': list(self.active_symbols)
            }