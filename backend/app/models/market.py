from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, 
    Enum, JSON, Boolean, LargeBinary,BigInteger,  # 添加 BigInteger 導入
)
from sqlalchemy.orm import relationship, validates  # 添加 validates 導入
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Exchange(Base):
    """交易所信息表"""
    __tablename__ = 'exchanges'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    api_key = Column(String(100))
    api_secret = Column(String(100))
    api_url = Column(String(200))
    status = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 關聯
    trading_pairs = relationship("TradingPair", back_populates="exchange")
    market_data = relationship("MarketData", back_populates="exchange")
    order_books = relationship("OrderBook", back_populates="exchange")
    depth_data = relationship("OrderBookDepth", back_populates="exchange")
    large_trades = relationship("LargeTradeRecord", back_populates="exchange")

class TradingPair(Base):
    """交易對信息表"""
    __tablename__ = 'trading_pairs'
    
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, ForeignKey('exchanges.id'))
    base_currency = Column(String(10), nullable=False)
    quote_currency = Column(String(10), nullable=False)
    symbol = Column(String(20), nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯會在所有類定義完後設置

class MarketData(Base):
    """市場數據表"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, ForeignKey('exchanges.id'))
    trading_pair_id = Column(Integer, ForeignKey('trading_pairs.id'))
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # 新增欄位
    price = Column(Float, nullable=False, index=True)  # 新增索引提高查詢性能
    side = Column(String(4), nullable=False)  # buy/sell
    
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    
    quote_volume = Column(Float)
    number_of_trades = Column(Integer)
    taker_buy_base_volume = Column(Float)
    taker_buy_quote_volume = Column(Float)
    
    weighted_average_price = Column(Float)
    price_change = Column(Float)
    price_change_percent = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    exchange = relationship("Exchange", back_populates="market_data")
    trading_pair = relationship("TradingPair", back_populates="market_data")

    @validates('side')
    def validate_side(self, key, side):
        """驗證交易方向"""
        if side not in ('buy', 'sell'):
            return 'buy'  # 默認值
        return side

    @validates('price')
    def validate_price(self, key, price):
        """驗證價格"""
        if price is None or price < 0:
            if self.close_price is not None:
                return self.close_price
            return 0.0
        return price

class OrderBook(Base):
    """訂單簿數據表"""
    __tablename__ = 'order_books'
    
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, ForeignKey('exchanges.id'))
    trading_pair_id = Column(Integer, ForeignKey('trading_pairs.id'))
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # 訂單簿數據以JSON格式存儲
    bids = Column(JSON)  # [[price, quantity], ...]
    asks = Column(JSON)  # [[price, quantity], ...]
    
    # 將 last_update_id 改為 BigInteger
    last_update_id = Column(BigInteger)  # 最後更新ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    exchange = relationship("Exchange")
    trading_pair = relationship("TradingPair")

class OrderBookDepth(Base):
    """完整訂單簿深度數據"""
    __tablename__ = 'order_book_depths'
    
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, ForeignKey('exchanges.id'))
    trading_pair_id = Column(Integer, ForeignKey('trading_pairs.id'))
    timestamp = Column(DateTime, nullable=False, index=True)
    
    bids = Column(JSON)
    asks = Column(JSON)
    
    bid_volume = Column(Float)
    ask_volume = Column(Float)
    spread = Column(Float)
    mid_price = Column(Float)
    
    last_update_id = Column(Integer)
    first_update_id = Column(Integer)
    update_type = Column(String(20))
    
    depth_level = Column(Integer)
    is_snapshot = Column(Boolean, default=False)
    processing_time = Column(Float)
    
    is_archived = Column(Boolean, default=False)
    compressed_data = Column(LargeBinary)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    exchange = relationship("Exchange")
    trading_pair = relationship("TradingPair", back_populates="depth_data")

class LargeTradeRecord(Base):
    """大額交易記錄"""
    __tablename__ = 'large_trade_records'
    
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, ForeignKey('exchanges.id'))
    trading_pair_id = Column(Integer, ForeignKey('trading_pairs.id'))
    timestamp = Column(DateTime, nullable=False, index=True)
    
    trade_size = Column(Float)
    price = Column(Float)
    side = Column(String(10))
    price_impact = Column(Float)
    volume_ratio = Column(Float)
    
    is_whale = Column(Boolean, default=False)
    pattern_type = Column(String(50))
    notes = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯
    exchange = relationship("Exchange")
    trading_pair = relationship("TradingPair", back_populates="large_trades")

# 在所有類定義完後設置 TradingPair 的關聯
TradingPair.exchange = relationship("Exchange", back_populates="trading_pairs")
TradingPair.market_data = relationship("MarketData", back_populates="trading_pair")
TradingPair.order_books = relationship("OrderBook", back_populates="trading_pair")
TradingPair.depth_data = relationship("OrderBookDepth", back_populates="trading_pair")
TradingPair.large_trades = relationship("LargeTradeRecord", back_populates="trading_pair")

# 在 models/market.py 中添加新模型

class KlineData(Base):
    """K線數據模型"""
    __tablename__ = 'kline_data'
    
    # 主鍵和關聯鍵
    id = Column(Integer, primary_key=True)
    exchange_id = Column(Integer, ForeignKey('exchanges.id'), nullable=False)
    trading_pair_id = Column(Integer, ForeignKey('trading_pairs.id'), nullable=False)
    
    # 時間相關
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    interval = Column(String(10), nullable=False)  # '1m', '1h', '1d' 等
    
    # OHLCV 基礎數據
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # 額外交易統計
    quote_volume = Column(Float)
    number_of_trades = Column(Integer)
    taker_buy_base_volume = Column(Float)
    taker_buy_quote_volume = Column(Float)
    
    # 技術分析欄位
    vwap = Column(Float)  # Volume Weighted Average Price
    volatility = Column(Float)  # 波動率
    
    # 元數據
    source = Column(String(50))  # 數據來源標識
    is_complete = Column(Boolean, default=True)  # 數據完整性標記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 關聯關係
    exchange = relationship("Exchange", back_populates="kline_data")
    trading_pair = relationship("TradingPair", back_populates="kline_data")
    
    # 數據驗證方法
    @validates('interval')
    def validate_interval(self, key, interval):
        """驗證時間間隔格式"""
        valid_intervals = {'1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'}
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval: {interval}")
        return interval
    
    @validates('open_price', 'high_price', 'low_price', 'close_price')
    def validate_prices(self, key, value):
        """驗證價格數據"""
        if value is None or value < 0:
            raise ValueError(f"Invalid price value for {key}: {value}")
        return value
    
    @validates('volume', 'quote_volume')
    def validate_volumes(self, key, value):
        """驗證交易量數據"""
        if value is not None and value < 0:
            raise ValueError(f"Invalid volume value for {key}: {value}")
        return value or 0.0
    
    def calculate_volatility(self):
        """計算當前K線的波動率"""
        if self.high_price and self.low_price and self.low_price > 0:
            return ((self.high_price - self.low_price) / self.low_price) * 100
        return 0.0
    
    def calculate_vwap(self):
        """計算成交量加權平均價格"""
        if self.quote_volume and self.volume and self.volume > 0:
            return self.quote_volume / self.volume
        return self.close_price
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.vwap:
            self.vwap = self.calculate_vwap()
        if not self.volatility:
            self.volatility = self.calculate_volatility()
    
    def __repr__(self):
        return (f"<KlineData(pair='{self.trading_pair.symbol}', "
                f"interval='{self.interval}', "
                f"timestamp='{self.timestamp}', "
                f"close='{self.close_price}')>")

# 在 Exchange 模型中添加關聯
Exchange.kline_data = relationship("KlineData", back_populates="exchange")

# 在 TradingPair 模型中添加關聯
TradingPair.kline_data = relationship("KlineData", back_populates="trading_pair")

# 在 market.py 文件的最後添加這些關係定義

from .historical import HistoricalMetrics, MarketAnalysis

# 添加到 TradingPair 類
TradingPair.historical_metrics = relationship("HistoricalMetrics", backref="trading_pair")
TradingPair.market_analysis = relationship("MarketAnalysis", backref="trading_pair")

# 確保所有表的關聯都被正確定義
from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers

# 配置映射器
configure_mappers()

def init_models(engine):
    """初始化所有模型"""
    Base.metadata.create_all(engine)