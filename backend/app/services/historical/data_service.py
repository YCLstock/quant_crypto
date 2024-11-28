# backend/app/services/historical/data_service.py

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.core.logging import logger
from app.models.historical import HistoricalMetrics
from app.models.market import TradingPair

class HistoricalDataService:
    def __init__(self, db: Session):
        self.db = db
        # 為不同時間週期定義年化因子
        self.annualization_factors = {
            '1m': 525600,  # 365 * 24 * 60
            '5m': 105120,  # 365 * 24 * 12
            '15m': 35040,  # 365 * 24 * 4
            '30m': 17520,  # 365 * 24 * 2
            '1h': 8760,    # 365 * 24
            '4h': 2190,    # 365 * 6
            '1d': 252,     # 交易日數
            '1w': 52,      # 週數
        }
        # 為不同時間週期定義波動率窗口
        self.volatility_windows = {
            '1m': 1440,    # 1天
            '5m': 288,     # 1天
            '15m': 96,     # 1天
            '30m': 48,     # 1天
            '1h': 24,      # 1天
            '4h': 30,      # 5天
            '1d': 20,      # 20天
            '1w': 12,      # 12週
        }

    def analyze_volatility(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """分析波動率特徵"""
        try:
            # 獲取歷史數據
            metrics = self._get_historical_data(
                symbol, timeframe, start_time, end_time
            )

            if not metrics or len(metrics) < 2:
                logger.warning(f"Insufficient data for {symbol} {timeframe}")
                return {}

            # 轉換為DataFrame
            df = self._prepare_dataframe(metrics)
            
            # 計算波動率
            df = self._calculate_volatility(df, timeframe)
            
            # 計算技術指標
            df = self._calculate_technical_indicators(df)
            
            # 生成分析結果
            analysis = self._generate_analysis(df, timeframe)
            
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing volatility for {symbol} {timeframe}: {e}")
            return {}

    def _get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[HistoricalMetrics]:
        """獲取歷史數據"""
        try:
            # 獲取交易對
            trading_pair = self._get_trading_pair(symbol)
            if not trading_pair:
                return []

            # 構建查詢
            query = select(HistoricalMetrics).where(
                and_(
                    HistoricalMetrics.trading_pair_id == trading_pair.id,
                    HistoricalMetrics.timeframe == timeframe
                )
            )

            # 確保時間參數使用 UTC
            if start_time:
                start_time = start_time.astimezone(timezone.utc)
                query = query.where(HistoricalMetrics.timestamp >= start_time)
            if end_time:
                end_time = end_time.astimezone(timezone.utc)
                query = query.where(HistoricalMetrics.timestamp <= end_time)

            # 排序並執行查詢
            query = query.order_by(HistoricalMetrics.timestamp.asc())
            result = self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []

    def _prepare_dataframe(self, metrics: List[HistoricalMetrics]) -> pd.DataFrame:
        """準備數據框架"""
        try:
            # 創建初始 DataFrame
            df = pd.DataFrame([{
                'timestamp': m.timestamp.astimezone(timezone.utc),  # 轉換為 UTC
                'open': m.open_price,
                'high': m.high_price,
                'low': m.low_price,
                'close': m.close_price,
                'volume': m.volume
            } for m in metrics])
            
            if df.empty:
                return pd.DataFrame()
            
            # 設置時間索引
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df.set_index('timestamp', inplace=True)
            
            # 清理數據
            df = df[~df.index.duplicated(keep='first')]  # 移除重複的時間戳
            df.sort_index(inplace=True)  # 按時間排序
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing DataFrame: {e}")
            return pd.DataFrame()

    def _calculate_volatility(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """計算波動率"""
        try:
            # 計算收益率
            df['returns'] = df['close'].pct_change()
            
            # 獲取相應的窗口大小和年化因子
            window = self.volatility_windows.get(timeframe, 20)
            annualization_factor = self.annualization_factors.get(timeframe, 252)
            
            # 計算波動率
            df['volatility'] = (
                df['returns']
                .rolling(window=window, min_periods=2)
                .std()
                * np.sqrt(annualization_factor)
                * 100  # 轉換為百分比
            )
            
            # 計算對數收益率（用於更準確的波動率估計）
            df['log_returns'] = np.log(df['close']/df['close'].shift(1))
            df['realized_volatility'] = (
                df['log_returns']
                .rolling(window=window)
                .std()
                * np.sqrt(annualization_factor)
                * 100
            )
            
            return df

        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return df

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        try:
            # 移動平均線
            df['ma7'] = df['close'].rolling(window=7).mean()
            df['ma25'] = df['close'].rolling(window=25).mean()
            df['ma99'] = df['close'].rolling(window=99).mean()
            
            # 布林帶
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_std'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
            df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
            
            return df

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df

    def _generate_analysis(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """生成分析結果"""
        try:
            if df.empty or 'volatility' not in df.columns:
                return {}

            # 使用UTC時間
            current_time = datetime.now(timezone.utc)
            
            current_volatility = df['volatility'].iloc[-1]
            volatility_series = df['volatility'].dropna()
            
            regime = self._determine_volatility_regime(
                current_volatility,
                volatility_series
            )
            
            trend = self._analyze_trend(df)
            
            return {
                'timestamp': current_time.isoformat(),
                'timeframe': timeframe,
                'volatility_stats': {
                    'current': float(current_volatility),
                    'mean': float(volatility_series.mean()),
                    'median': float(volatility_series.median()),
                    'std': float(volatility_series.std()),
                    'min': float(volatility_series.min()),
                    'max': float(volatility_series.max()),
                },
                'regime_analysis': regime,
                'trend_analysis': trend,
                'market_regime': self._determine_market_regime(regime, trend),
                'market_score': self._calculate_market_score(regime, trend)
            }

        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return {}


    def _get_trading_pair(self, symbol: str) -> Optional[TradingPair]:
        """獲取交易對信息"""
        return self.db.query(TradingPair).filter(
            and_(
                TradingPair.symbol == symbol,
                TradingPair.is_active == 1
            )
        ).first()

    def _determine_volatility_regime(
        self,
        current: float,
        series: pd.Series
    ) -> Dict:
        """判斷波動率區間"""
        mean = series.mean()
        std = series.std()
        zscore = (current - mean) / std if std > 0 else 0
        percentile = series.rank(pct=True).iloc[-1] * 100

        if zscore > 2:
            regime = 'Extremely High'
        elif zscore > 1:
            regime = 'High'
        elif zscore < -2:
            regime = 'Extremely Low'
        elif zscore < -1:
            regime = 'Low'
        else:
            regime = 'Normal'

        return {
            'regime': regime,
            'zscore': float(zscore),
            'percentile': float(percentile),
            'description': f"Volatility is {regime.lower()} ({percentile:.1f}th percentile)"
        }

    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """分析趨勢"""
        try:
            if df.empty or len(df) < 2:
                return {
                    'direction': 'Unknown',
                    'strength': 0.0,
                    'duration': 0,
                    'price_change_pct': 0.0
                }

            # 計算價格變化
            price_change = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
            
            # 計算趨勢強度和方向
            if price_change > 5:
                direction = 'Uptrend'
            elif price_change < -5:
                direction = 'Downtrend'
            else:
                direction = 'Sideways'

            # 計算趨勢持續時間
            trend_changes = df['close'].diff().dropna()
            current_trend = trend_changes.iloc[-1] > 0
            duration = 1
            
            for change in reversed(trend_changes.iloc[:-1]):
                if (change > 0) == current_trend:
                    duration += 1
                else:
                    break

            return {
                'direction': direction,
                'strength': abs(price_change),
                'duration': duration,
                'price_change_pct': price_change
            }

        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return {
                'direction': 'Error',
                'strength': 0.0,
                'duration': 0,
                'price_change_pct': 0.0
            }

    def _determine_market_regime(self, volatility: Dict, trend: Dict) -> str:
        """判斷市場狀態"""
        vol_regime = volatility['regime']
        trend_direction = trend['direction']

        if vol_regime in ['Extremely High', 'High']:
            if trend_direction == 'Uptrend':
                return 'Bullish Volatile'
            elif trend_direction == 'Downtrend':
                return 'Bearish Volatile'
            return 'High Volatility Range'

        elif vol_regime in ['Extremely Low', 'Low']:
            if trend_direction == 'Sideways':
                return 'Consolidation'
            return 'Low Volatility Trend'

        else:
            if trend_direction == 'Uptrend':
                return 'Steady Uptrend'
            elif trend_direction == 'Downtrend':
                return 'Steady Downtrend'
            return 'Normal Range'

    def _calculate_market_score(self, volatility: Dict, trend: Dict) -> float:
        """計算市場評分"""
        try:
            # 波動率分數 (0-40分)
            vol_zscore = abs(volatility['zscore'])
            vol_score = max(0, min(40, (1 - vol_zscore / 3) * 40))

            # 趨勢分數 (0-40分)
            trend_strength = abs(trend['strength'])
            trend_score = max(0, min(40, (trend_strength / 10) * 40))

            # 持續性分數 (0-20分)
            duration = trend['duration']
            duration_score = max(0, min(20, (duration / 20) * 20))

            return round(vol_score + trend_score + duration_score, 2)

        except Exception as e:
            logger.error(f"Error calculating market score: {e}")
            return 0.0