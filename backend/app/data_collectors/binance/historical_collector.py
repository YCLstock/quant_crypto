# backend/app/data_collectors/binance/historical_collector.py

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.config import settings
from app.core.logging import logger
from app.models.historical import HistoricalMetrics, MarketAnalysis
from app.models.market import TradingPair

class HistoricalDataCollector:
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': settings.BINANCE_API_KEY
        })
        self.rate_limit_remaining = settings.BINANCE_RATE_LIMIT
        self.last_request_time = datetime.now()
    
    def collect_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """收集歷史K線數據"""
        try:
            # 設置時間範圍
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(days=settings.HISTORICAL_INITIAL_DAYS)
            
            # 檢查交易對是否存在
            trading_pair = self._get_trading_pair(symbol)
            if not trading_pair:
                raise ValueError(f"Trading pair not found: {symbol}")
            
            # 分批收集數據
            all_klines = []
            current_start = start_time
            
            while current_start < end_time:
                current_end = min(
                    current_start + timedelta(days=7),
                    end_time
                )
                
                # 收集一批數據
                klines = self._fetch_klines(
                    symbol,
                    timeframe,
                    current_start,
                    current_end
                )
                
                if klines:
                    all_klines.extend(klines)
                    
                # 更新開始時間
                current_start = current_end
                
                # 檢查並等待速率限制
                self._handle_rate_limit()
            
            # 處理並保存數據
            self._process_and_save_klines(trading_pair.id, timeframe, all_klines)
            
            return all_klines
            
        except Exception as e:
            logger.error(f"Error collecting historical data for {symbol}: {e}")
            raise
    
    def _fetch_klines(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """從Binance獲取K線數據"""
        try:
            params = {
                'symbol': symbol,
                'interval': timeframe,
                'startTime': int(start_time.timestamp() * 1000),
                'endTime': int(end_time.timestamp() * 1000),
                'limit': settings.BINANCE_MAX_LIMIT
            }
            
            url = f"{self.base_url}/api/v3/klines"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            klines = response.json()
            return [
                {
                    'timestamp': datetime.fromtimestamp(k[0] / 1000),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': datetime.fromtimestamp(k[6] / 1000),
                    'quote_volume': float(k[7]),
                    'trades': int(k[8]),
                    'taker_buy_base': float(k[9]),
                    'taker_buy_quote': float(k[10])
                }
                for k in klines
            ]
            
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            raise
    
    def _process_and_save_klines(
        self,
        trading_pair_id: int,
        timeframe: str,
        klines: List[Dict]
    ) -> None:
        """處理和保存K線數據"""
        try:
            # 轉換為DataFrame進行計算
            df = pd.DataFrame(klines)
            if df.empty:
                return
                
            # 確保時間戳是正確的日期時間格式
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 計算技術指標，傳入時間週期
            metrics = self._calculate_metrics(df, timeframe)
            
            # 保存到數據庫
            for timestamp, row in metrics.iterrows():
                historical_metric = HistoricalMetrics(
                    trading_pair_id=trading_pair_id,
                    timestamp=timestamp,
                    timeframe=timeframe,
                    open_price=row['open'],
                    high_price=row['high'],
                    low_price=row['low'],
                    close_price=row['close'],
                    volume=row['volume'],
                    volatility=row.get('volatility'),
                    ma7=row.get('ma7'),
                    ma25=row.get('ma25'),
                    ma99=row.get('ma99'),
                    rsi=row.get('rsi'),
                    bb_upper=row.get('bb_upper'),
                    bb_middle=row.get('bb_middle'),
                    bb_lower=row.get('bb_lower'),
                    bb_width=row.get('bb_width'),
                    returns=row.get('returns'),
                    log_returns=row.get('log_returns'),
                    realized_volatility=row.get('realized_volatility'),
                    price_momentum=row.get('price_momentum'),
                    volume_momentum=row.get('volume_momentum')
                )
                self.db.add(historical_metric)
                
            # 分批提交以提高性能
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing and saving klines: {e}")
            self.db.rollback()
            raise
    
    def _calculate_metrics(self, df: pd.DataFrame, timeframe: str = '1h') -> pd.DataFrame:
        """計算技術指標和波動率"""
        try:
            # 確保使用時間戳作為索引
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
            
            # 基礎計算
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close']/df['close'].shift(1))
            
            # 波動率計算 (使用年化因子)
            annualization_factor = self._get_annualization_factor(df.index)
            
            # 使用對應時間週期的窗口大小
            volatility_window = settings.VOLATILITY_WINDOWS.get(timeframe, 20)  # 默認使用20
            
            # 計算基本波動率
            df['volatility'] = df['returns'].rolling(
                window=volatility_window
            ).std() * np.sqrt(annualization_factor)
            
            # 移動平均線
            df['ma7'] = df['close'].rolling(window=7).mean()
            df['ma25'] = df['close'].rolling(window=25).mean()
            df['ma99'] = df['close'].rolling(window=99).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=settings.RSI_PERIOD).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=settings.RSI_PERIOD).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 布林帶
            df['bb_middle'] = df['close'].rolling(
                window=settings.BOLLINGER_PERIOD
            ).mean()
            std_dev = df['close'].rolling(window=settings.BOLLINGER_PERIOD).std()
            df['bb_upper'] = df['bb_middle'] + (std_dev * settings.BOLLINGER_STD_DEV)
            df['bb_lower'] = df['bb_middle'] - (std_dev * settings.BOLLINGER_STD_DEV)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            
            # 已實現波動率 - 使用實際時間週期的窗口
            df['realized_volatility'] = df['log_returns'].rolling(
                window=volatility_window
            ).std() * np.sqrt(annualization_factor)
            
            # 動量指標
            df['price_momentum'] = df['close'].pct_change(periods=10)
            df['volume_momentum'] = df['volume'].pct_change(periods=10)
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            raise
    
    def _get_trading_pair(self, symbol: str) -> Optional[TradingPair]:
        """獲取交易對信息"""
        try:
            return self.db.query(TradingPair).filter(
                and_(
                    TradingPair.symbol == symbol,
                    TradingPair.is_active == 1
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting trading pair: {e}")
            raise
    
    def _handle_rate_limit(self):
        """處理API速率限制"""
        current_time = datetime.now()
        time_passed = (current_time - self.last_request_time).total_seconds()
        
        # 重置速率限制
        if time_passed >= 60:
            self.rate_limit_remaining = settings.BINANCE_RATE_LIMIT
            self.last_request_time = current_time
        
        # 檢查是否需要等待
        if self.rate_limit_remaining <= 0:
            wait_time = 60 - time_passed
            if wait_time > 0:
                time.sleep(wait_time)
                self.rate_limit_remaining = settings.BINANCE_RATE_LIMIT
                self.last_request_time = datetime.now()
        
        self.rate_limit_remaining -= 1

    def _get_annualization_factor(self, index) -> float:
        """根據時間間隔計算年化因子"""
        if len(index) < 2:
            return 252  # 默認使用交易日數
            
        # 計算平均時間間隔（秒）
        avg_interval = (index[-1] - index[0]).total_seconds() / (len(index) - 1)
        
        # 根據間隔返回適當的年化因子
        if avg_interval <= 3600:  # 小時級別或更小
            return 365 * 24  # 每年小時數
        elif avg_interval <= 86400:  # 日級別
            return 365
        else:  # 週級別或更大
            return 52
    
    def close(self):
        """關閉sessions"""
        self.session.close()