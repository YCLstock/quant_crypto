# backend/app/data_collectors/binance/collector.py
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.core.logging import logger
from app.models.market import Exchange, TradingPair, MarketData, OrderBook
from .client import BinanceClient

class BinanceDataCollector:
    def __init__(self, db: Session):
        self.db = db
        self.exchange_id = self._get_or_create_exchange()
        self.active_pairs = {}  # 緩存活動的交易對
    
    def _get_or_create_exchange(self) -> int:
        """獲取或創建交易所記錄"""
        try:
            exchange = self.db.query(Exchange).filter_by(name="Binance").first()
            if not exchange:
                exchange = Exchange(
                    name="Binance",
                    api_url="https://api.binance.com",
                    status="active",
                    api_key=settings.BINANCE_API_KEY,
                    api_secret=settings.BINANCE_API_SECRET
                )
                self.db.add(exchange)
                self.db.commit()
            return exchange.id
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_or_create_exchange: {str(e)}")
            self.db.rollback()
            raise
    
    def _get_trading_pair_id(self, symbol: str) -> Optional[int]:
        """獲取交易對ID"""
        if symbol in self.active_pairs:
            return self.active_pairs[symbol]
            
        pair = self.db.query(TradingPair).filter_by(
            exchange_id=self.exchange_id,
            symbol=symbol,
            is_active=1
        ).first()
        
        if pair:
            self.active_pairs[symbol] = pair.id
            return pair.id
        return None
    
    async def collect_trading_pairs(self) -> List[TradingPair]:
        """收集並更新交易對信息"""
        try:
            async with BinanceClient() as client:
                exchange_info = await client.get_exchange_info()
                
                pairs = []
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['status'] != 'TRADING':
                        continue
                        
                    pair = self.db.query(TradingPair).filter_by(
                        exchange_id=self.exchange_id,
                        symbol=symbol_info['symbol']
                    ).first()
                    
                    if not pair:
                        pair = TradingPair(
                            exchange_id=self.exchange_id,
                            symbol=symbol_info['symbol'],
                            base_currency=symbol_info['baseAsset'],
                            quote_currency=symbol_info['quoteAsset'],
                            is_active=1
                        )
                        self.db.add(pair)
                        pairs.append(pair)
                    
                    # 更新緩存
                    self.active_pairs[symbol_info['symbol']] = pair.id
                
                if pairs:
                    self.db.commit()
                return pairs
                
        except Exception as e:
            logger.error(f"Error collecting trading pairs: {str(e)}")
            self.db.rollback()
            raise
    
    async def collect_market_data(self, symbols: Optional[List[str]] = None) -> List[MarketData]:
        """收集市場數據"""
        try:
            async with BinanceClient() as client:
                tickers = await client.get_ticker_24h()
                if isinstance(tickers, dict):  # 單一交易對的情況
                    tickers = [tickers]
                
                if symbols:
                    tickers = [t for t in tickers if t['symbol'] in symbols]
                
                market_data = []
                for ticker in tickers:
                    pair_id = self._get_trading_pair_id(ticker['symbol'])
                    if not pair_id:
                        continue
                    
                    # 確保價格和交易方向不為空
                    close_price = float(ticker['lastPrice'])
                    open_price = float(ticker['openPrice'])
                    
                    data = MarketData(
                        exchange_id=self.exchange_id,
                        trading_pair_id=pair_id,
                        timestamp=datetime.now(),
                        # 設置 price 為收盤價
                        price=close_price,
                        # 根據價格變動決定交易方向
                        side='buy' if close_price >= open_price else 'sell',
                        open_price=open_price,
                        high_price=float(ticker['highPrice']),
                        low_price=float(ticker['lowPrice']),
                        close_price=close_price,
                        volume=float(ticker['volume']),
                        quote_volume=float(ticker['quoteVolume']),
                        number_of_trades=int(ticker['count']),
                        price_change=float(ticker['priceChange']),
                        price_change_percent=float(ticker['priceChangePercent']),
                        taker_buy_base_volume=float(ticker.get('takerBuyBaseVolume', 0)),
                        taker_buy_quote_volume=float(ticker.get('takerBuyQuoteVolume', 0)),
                        weighted_average_price=float(ticker.get('weightedAvgPrice', close_price))
                    )
                    self.db.add(data)
                    market_data.append(data)
                
                if market_data:
                    self.db.commit()
                    logger.info(f"Collected {len(market_data)} market data records")
                return market_data
                
        except Exception as e:
            logger.error(f"Error collecting market data: {str(e)}")
            self.db.rollback()
            raise
    
    async def collect_order_books(self, symbols: List[str]) -> List[OrderBook]:
        """收集訂單簿數據"""
        try:
            async with BinanceClient() as client:
                order_books = []
                for symbol in symbols:
                    pair_id = self._get_trading_pair_id(symbol)
                    if not pair_id:
                        continue
                    
                    book_data = await client.get_order_book(symbol)
                    order_book = OrderBook(
                        exchange_id=self.exchange_id,
                        trading_pair_id=pair_id,
                        timestamp=datetime.now(),
                        bids=book_data['bids'],
                        asks=book_data['asks'],
                        last_update_id=book_data['lastUpdateId']
                    )
                    self.db.add(order_book)
                    order_books.append(order_book)
                
                if order_books:
                    self.db.commit()
                return order_books
                
        except Exception as e:
            logger.error(f"Error collecting order books: {str(e)}")
            self.db.rollback()
            raise