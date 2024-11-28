# backend/app/models/historical.py

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.market import Base

class HistoricalMetrics(Base):
    """歷史技術指標數據表"""
    __tablename__ = 'historical_metrics'
    
    id = Column(Integer, primary_key=True)
    trading_pair_id = Column(Integer, ForeignKey('trading_pairs.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d 等
    
    # 價格指標
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    
    # 波動率指標
    volatility = Column(Float)  # 歷史波動率
    volatility_short = Column(Float)  # 短期波動率
    volatility_medium = Column(Float)  # 中期波動率
    volatility_long = Column(Float)  # 長期波動率
    
    # 移動平均線
    ma7 = Column(Float)
    ma25 = Column(Float)
    ma99 = Column(Float)
    
    # 技術指標
    rsi = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    bb_width = Column(Float)
    
    # 統計指標
    returns = Column(Float)
    log_returns = Column(Float)
    realized_volatility = Column(Float)
    
    # 衍生指標
    price_momentum = Column(Float)
    volume_momentum = Column(Float)
    
    # 其他數據
    metrics_json = Column(JSON)
    is_complete = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_historical_metrics_pair_time', 
              trading_pair_id, timestamp, timeframe),
    )

class MarketAnalysis(Base):
    """市場分析結果表"""
    __tablename__ = 'market_analysis'
    
    id = Column(Integer, primary_key=True)
    trading_pair_id = Column(Integer, ForeignKey('trading_pairs.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    timeframe = Column(String(10), nullable=False)
    
    # 統計摘要
    price_mean = Column(Float)
    price_std = Column(Float)
    price_skew = Column(Float)
    price_kurtosis = Column(Float)
    
    # 波動率分析
    volatility_regime = Column(String(20))  # 波動率區間分類
    volatility_percentile = Column(Float)  # 波動率百分位
    volatility_zscore = Column(Float)  # 波動率Z分數
    
    # 趨勢分析
    trend_direction = Column(String(20))  # 上升/下降/盤整
    trend_strength = Column(Float)  # 趨勢強度
    trend_duration = Column(Integer)  # 趨勢持續期
    
    # 市場狀態
    market_regime = Column(String(20))  # 市場狀態分類
    market_score = Column(Float)  # 綜合市場評分
    
    # 分析結果
    analysis_json = Column(JSON)  # 詳細分析結果
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_market_analysis_pair_time',
              trading_pair_id, timestamp, timeframe),
    )