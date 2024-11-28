# app/services/historical/data_service.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from scipy import stats
from sklearn.cluster import KMeans

from app.core.config import settings
from app.core.logging import logger
from app.models.historical import HistoricalMetrics, MarketAnalysis
from app.models.market import TradingPair

class HistoricalDataService:
    def __init__(self, db: Session):
        self.db = db
    
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
            metrics = self._get_historical_metrics(
                symbol, timeframe, start_time, end_time
            )
            
            if not metrics:
                logger.warning(f"No metrics data found for {symbol} {timeframe}")
                return {}
            
            # 轉換為DataFrame
            df = pd.DataFrame([{
                'timestamp': m.timestamp,
                'volatility': m.volatility,
                'volatility_short': m.volatility_short,
                'volatility_medium': m.volatility_medium,
                'volatility_long': m.volatility_long,
                'returns': m.returns,
                'close_price': m.close_price,
                'volume': m.volume
            } for m in metrics])
            
            if df.empty:
                logger.warning("DataFrame is empty after conversion")
                return {}
                
            # 設置時間戳為索引
            df.set_index('timestamp', inplace=True)
            
            try:
                # 計算統計
                volatility_stats = self._calculate_volatility_stats(df)
                regime = self._detect_volatility_regime(df)
                trend = self._analyze_trend(df)
                
                # 生成市場分析報告
                analysis = MarketAnalysis(
                    trading_pair_id=metrics[0].trading_pair_id,
                    timestamp=datetime.now(),
                    timeframe=timeframe,
                    volatility_regime=regime['regime'],
                    volatility_percentile=regime['percentile'],
                    volatility_zscore=regime['zscore'],
                    trend_direction=trend['direction'],
                    trend_strength=trend['strength'],
                    trend_duration=trend['duration'],
                    market_regime=self._determine_market_regime(regime, trend),
                    market_score=self._calculate_market_score(regime, trend),
                    analysis_json={
                        'volatility_stats': volatility_stats,
                        'regime_analysis': regime,
                        'trend_analysis': trend
                    }
                )
                
                # 保存分析結果
                self.db.add(analysis)
                self.db.commit()
                
                return {
                    'volatility_stats': volatility_stats,
                    'regime_analysis': regime,
                    'trend_analysis': trend,
                    'market_regime': analysis.market_regime,
                    'market_score': analysis.market_score
                }
                
            except Exception as calc_error:
                logger.error(f"Error in calculations: {calc_error}", exc_info=True)
                self.db.rollback()
                raise
            
        except Exception as e:
            logger.error(f"Error in analyze_volatility: {e}", exc_info=True)
            if 'db' in locals() and hasattr(self, 'db'):
                self.db.rollback()
            raise

    def analyze_volatility_regimes(
        self,
        symbol: str,
        timeframe: str,
        lookback_days: int = 90
    ) -> Dict:
        """分析波動率區間特徵"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback_days)
            
            # 獲取數據
            metrics = self._get_historical_metrics(
                symbol, timeframe, start_time, end_time
            )
            
            if not metrics:
                logger.warning(f"No metrics found for {symbol} {timeframe}")
                return {}
                
            # 創建DataFrame
            df = pd.DataFrame([{
                'timestamp': m.timestamp,
                'volatility': m.volatility,
                'returns': m.returns,
                'close': m.close_price
            } for m in metrics])
            
            # 使用K-means進行區間識別
            kmeans = KMeans(n_clusters=3, random_state=42)
            df['regime'] = kmeans.fit_predict(df[['volatility']])
            
            # 計算區間特徵
            regime_stats = self._calculate_regime_statistics(df)
            
            # 獲取當前狀態
            current_regime = int(df['regime'].iloc[-1])
            current_vol = float(df['volatility'].iloc[-1])
            
            return {
                'current_regime': {
                    'id': current_regime,
                    'volatility': current_vol,
                    'characteristics': regime_stats[current_regime]
                },
                'regime_statistics': regime_stats,
                'transition_probabilities': self._calculate_regime_transitions(df['regime']).tolist(),
                'regime_duration': self._calculate_regime_durations(df),
                'stability_score': self._calculate_regime_stability(df)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volatility regimes: {e}", exc_info=True)
            raise

    def _calculate_volatility_stats(self, df: pd.DataFrame) -> Dict:
        """計算波動率統計指標"""
        try:
            volatility_series = df['volatility'].dropna()
            if volatility_series.empty:
                logger.warning("Empty volatility series")
                return {}
                
            stats_dict = {
                'current': float(volatility_series.iloc[-1]),
                'mean': float(volatility_series.mean()),
                'median': float(volatility_series.median()),
                'std': float(volatility_series.std()),
                'min': float(volatility_series.min()),
                'max': float(volatility_series.max()),
                'skew': float(stats.skew(volatility_series)) if len(volatility_series) > 2 else 0,
                'kurtosis': float(stats.kurtosis(volatility_series)) if len(volatility_series) > 2 else 0,
                'percentiles': {
                    '25': float(volatility_series.quantile(0.25)),
                    '50': float(volatility_series.quantile(0.50)),
                    '75': float(volatility_series.quantile(0.75)),
                    '90': float(volatility_series.quantile(0.90)),
                    '95': float(volatility_series.quantile(0.95))
                }
            }
            
            # 計算日變化率
            if len(volatility_series) > 1:
                daily_change = (volatility_series.iloc[-1] / volatility_series.iloc[-2] - 1) * 100
                stats_dict['daily_change'] = float(daily_change)
            
            return stats_dict
            
        except Exception as e:
            logger.error(f"Error calculating volatility stats: {e}", exc_info=True)
            return {}

    def _detect_volatility_regime(self, df: pd.DataFrame) -> Dict:
        """檢測波動率區間"""
        try:
            volatility_series = df['volatility'].dropna()
            if volatility_series.empty:
                logger.warning("Empty volatility series in regime detection")
                return {
                    'regime': 'Unknown',
                    'zscore': 0.0,
                    'percentile': 50.0,
                    'description': 'Insufficient data'
                }
            
            current_vol = volatility_series.iloc[-1]
            
            # 計算基本統計量
            vol_mean = volatility_series.mean()
            vol_std = volatility_series.std() if len(volatility_series) > 1 else 0
            
            # 計算Z分數
            zscore = (current_vol - vol_mean) / vol_std if vol_std > 0 else 0
            
            # 計算百分位數
            percentile = stats.percentileofscore(volatility_series, current_vol)
            
            # 判斷區間
            regime = self._determine_regime(zscore)
            
            return {
                'regime': regime,
                'zscore': float(zscore),
                'percentile': float(percentile),
                'description': self._generate_regime_description(regime, percentile)
            }
            
        except Exception as e:
            logger.error(f"Error detecting volatility regime: {e}", exc_info=True)
            return {
                'regime': 'Error',
                'zscore': 0.0,
                'percentile': 0.0,
                'description': str(e)
            }

    def _determine_regime(self, zscore: float) -> str:
        """根據Z分數確定區間"""
        if zscore > 2:
            return 'Extremely High'
        elif zscore > 1:
            return 'High'
        elif zscore < -2:
            return 'Extremely Low'
        elif zscore < -1:
            return 'Low'
        else:
            return 'Normal'

    def _generate_regime_description(self, regime: str, percentile: float) -> str:
        """生成區間描述"""
        return f"Current volatility is {regime} ({percentile:.1f}th percentile)"

    def _get_historical_metrics(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[HistoricalMetrics]:
        """獲取歷史指標數據"""
        try:
            trading_pair = self._get_trading_pair(symbol)
            if not trading_pair:
                logger.warning(f"Trading pair not found: {symbol}")
                return []
            
            query = self.db.query(HistoricalMetrics).filter(
                and_(
                    HistoricalMetrics.trading_pair_id == trading_pair.id,
                    HistoricalMetrics.timeframe == timeframe
                )
            )
            
            if start_time:
                query = query.filter(HistoricalMetrics.timestamp >= start_time)
            if end_time:
                query = query.filter(HistoricalMetrics.timestamp <= end_time)
            
            metrics = query.order_by(HistoricalMetrics.timestamp.asc()).all()
            
            if not metrics:
                logger.warning(f"No metrics found for {symbol} {timeframe}")
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}", exc_info=True)
            return []

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
            logger.error(f"Error getting trading pair: {e}", exc_info=True)
            return None
        
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """分析趨勢特徵"""
        try:
            if df.empty or 'close_price' not in df.columns:
                logger.warning("Empty DataFrame or missing close_price column")
                return {
                    'direction': 'Unknown',
                    'strength': 0.0,
                    'duration': 0,
                    'price_change_pct': 0.0
                }
            
            # 計算價格變化
            first_price = df['close_price'].iloc[0]
            last_price = df['close_price'].iloc[-1]
            if first_price <= 0:  # 防止除以零
                logger.warning("Invalid first price value")
                return {
                    'direction': 'Error',
                    'strength': 0.0,
                    'duration': 0,
                    'price_change_pct': 0.0
                }
                
            price_change = ((last_price / first_price) - 1) * 100
            
            # 計算移動平均
            try:
                df['ma_short'] = df['close_price'].rolling(window=7).mean()
                df['ma_long'] = df['close_price'].rolling(window=25).mean()
                
                # 計算趨勢強度
                if pd.isna(df['ma_long'].iloc[-1]):  # 檢查是否有足夠的數據
                    trend_strength = 0.0
                else:
                    trend_strength = ((df['ma_short'].iloc[-1] / df['ma_long'].iloc[-1]) - 1) * 100
                    
            except Exception as ma_error:
                logger.error(f"Error calculating moving averages: {ma_error}")
                trend_strength = 0.0
            
            # 判斷趨勢方向
            direction = self._determine_trend_direction(price_change)
            
            # 計算趨勢持續時間
            duration = self._calculate_trend_duration(df)
            
            return {
                'direction': direction,
                'strength': float(trend_strength),
                'duration': duration,
                'price_change_pct': float(price_change)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {e}", exc_info=True)
            return {
                'direction': 'Error',
                'strength': 0.0,
                'duration': 0,
                'price_change_pct': 0.0
            }

    def _determine_trend_direction(self, price_change: float) -> str:
        """根據價格變化確定趨勢方向"""
        if price_change > 5:
            return 'Uptrend'
        elif price_change < -5:
            return 'Downtrend'
        else:
            return 'Sideways'

    def _calculate_trend_duration(self, df: pd.DataFrame) -> int:
        """計算趨勢持續期"""
        try:
            if df.empty or 'close_price' not in df.columns:
                return 0
                
            prices = df['close_price'].values
            current_price = prices[-1]
            duration = 0
            
            # 從倒數第二個價格開始向前檢查
            for i in range(len(prices)-2, -1, -1):
                if (current_price > prices[i] and prices[-1] > prices[i]) or \
                (current_price < prices[i] and prices[-1] < prices[i]):
                    duration += 1
                else:
                    break
            
            return duration
            
        except Exception as e:
            logger.error(f"Error calculating trend duration: {e}")
            return 0

    def _calculate_regime_statistics(self, df: pd.DataFrame) -> Dict:
        """計算每個區間的統計特徵"""
        try:
            regime_stats = {}
            for regime in range(3):  # 3個區間
                regime_data = df[df['regime'] == regime]
                if not regime_data.empty:
                    regime_stats[regime] = {
                        'mean_volatility': float(regime_data['volatility'].mean()),
                        'count': len(regime_data),
                        'avg_returns': float(regime_data['returns'].mean()),
                        'std_returns': float(regime_data['returns'].std()),
                        'period': {
                            'start': regime_data['timestamp'].min().isoformat(),
                            'end': regime_data['timestamp'].max().isoformat()
                        }
                    }
                else:
                    regime_stats[regime] = {
                        'mean_volatility': 0.0,
                        'count': 0,
                        'avg_returns': 0.0,
                        'std_returns': 0.0,
                        'period': {
                            'start': None,
                            'end': None
                        }
                    }
            return regime_stats
        except Exception as e:
            logger.error(f"Error calculating regime statistics: {e}")
            return {}

    def get_market_analysis(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict]:
        """獲取市場分析結果"""
        try:
            # 獲取交易對信息
            trading_pair = self._get_trading_pair(symbol)
            if not trading_pair:
                logger.warning(f"Trading pair not found: {symbol}")
                return []
            
            # 查詢市場分析記錄
            analyses = self.db.query(MarketAnalysis).filter(
                and_(
                    MarketAnalysis.trading_pair_id == trading_pair.id,
                    MarketAnalysis.timeframe == timeframe
                )
            ).order_by(
                MarketAnalysis.timestamp.desc()
            ).limit(limit).all()
            
            # 轉換為字典格式
            results = []
            for analysis in analyses:
                result = {
                    'timestamp': analysis.timestamp,
                    'volatility_regime': analysis.volatility_regime,
                    'volatility_percentile': analysis.volatility_percentile,
                    'volatility_zscore': analysis.volatility_zscore,
                    'trend_direction': analysis.trend_direction,
                    'trend_strength': analysis.trend_strength,
                    'trend_duration': analysis.trend_duration,
                    'market_regime': analysis.market_regime,
                    'market_score': analysis.market_score,
                    'analysis_details': analysis.analysis_json
                }
                results.append(result)
            
            # 添加匯總統計
            if results:
                latest = results[0]
                latest['summary'] = {
                    'analysis_count': len(results),
                    'first_analysis': results[-1]['timestamp'].isoformat() if results else None,
                    'last_analysis': latest['timestamp'].isoformat(),
                    'average_score': sum(r['market_score'] for r in results) / len(results),
                    'regime_distribution': self._calculate_regime_distribution(results),
                    'trend_distribution': self._calculate_trend_distribution(results)
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting market analysis: {e}", exc_info=True)
            return []