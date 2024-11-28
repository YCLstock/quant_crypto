#!/usr/bin/env python3

import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta, timezone  # 添加 timezone 導入
from typing import List, Dict, Optional
from tqdm import tqdm
import pandas as pd
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.logging import logger
from app.models.market import TradingPair
from app.models.historical import HistoricalMetrics  
from app.services.historical.data_service import HistoricalDataService

class MarketAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        self.service = HistoricalDataService(db)
        
    async def analyze_markets(
        self,
        symbols: List[str],
        timeframes: List[str],
        days: int = 30,
        force_update: bool = False
    ):
        """執行市場分析"""
        try:
            total_tasks = len(symbols) * len(timeframes)
            start_time = datetime.now(timezone.utc) - timedelta(days=days)
            
            with tqdm(total=total_tasks, desc="Analyzing Markets") as pbar:
                for symbol in symbols:
                    logger.info(f"\nProcessing {symbol}")
                    
                    for timeframe in timeframes:
                        try:
                            # 檢查數據完整性
                            if not self._check_data_integrity(symbol, timeframe, start_time):
                                logger.warning(
                                    f"Insufficient data for {symbol} {timeframe}"
                                )
                                pbar.update(1)
                                continue
                            
                            # 檢查是否需要更新
                            if not force_update and self._has_recent_analysis(symbol, timeframe, start_time):
                                logger.info(
                                    f"Recent analysis exists for {symbol} {timeframe}"
                                )
                                pbar.update(1)
                                continue
                            
                            # 執行分析
                            analysis = self.service.analyze_volatility(
                                symbol=symbol,
                                timeframe=timeframe,
                                start_time=start_time
                            )
                            
                            if analysis:
                                self._log_analysis_results(symbol, timeframe, analysis)
                            else:
                                logger.warning(
                                    f"No analysis results for {symbol} {timeframe}"
                                )
                            
                            pbar.update(1)
                            
                        except Exception as e:
                            logger.error(
                                f"Error analyzing {symbol} {timeframe}: {e}"
                            )
                            
                        await asyncio.sleep(0.5)
            
            self._generate_analysis_report(symbols, timeframes)
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            raise
    
    def _check_data_integrity(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime
    ) -> bool:
        """檢查數據完整性"""
        try:
            # 確保時間是UTC
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            
            min_points = settings.MIN_DATA_POINTS.get(timeframe, 20)
            
            # 修正的SQLAlchemy 2.0查詢
            query = (
                select(func.count())
                .select_from(HistoricalMetrics)
                .where(
                    and_(
                        HistoricalMetrics.trading_pair.has(symbol=symbol),
                        HistoricalMetrics.timeframe == timeframe,
                        HistoricalMetrics.timestamp >= start_time
                    )
                )
            )
            
            count = self.db.execute(query).scalar_one()
            
            if count < min_points:
                logger.warning(
                    f"Insufficient data points for {symbol} {timeframe}. "
                    f"Got {count}, need {min_points}"
                )
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking data integrity: {e}")
            return False

    def _has_recent_analysis(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime
    ) -> bool:
        """檢查是否已有最新的分析數據"""
        try:
            result = self.service.analyze_volatility(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time
            )
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error checking recent analysis: {e}")
            return False

    def _generate_analysis_report(
        self,
        symbols: List[str],
        timeframes: List[str]
    ):
        """生成分析報告"""
        try:
            logger.info("\nAnalysis Report Summary:")
            logger.info("=" * 50)
            
            for symbol in symbols:
                logger.info(f"\n{symbol} Analysis:")
                logger.info("-" * 30)
                
                for timeframe in timeframes:
                    # 直接進行分析
                    analysis = self.service.analyze_volatility(
                        symbol=symbol,
                        timeframe=timeframe
                    )
                    
                    if analysis:
                        logger.info(f"\nTimeframe: {timeframe}")
                        logger.info(f"Market Regime: {analysis.get('market_regime')}")
                        logger.info(f"Market Score: {analysis.get('market_score')}")
                        logger.info(
                            f"Volatility: {analysis.get('volatility_stats', {}).get('current', 0):.2f}%"
                        )
                        logger.info(
                            f"Trend: {analysis.get('trend_analysis', {}).get('direction', 'Unknown')}"
                        )
                    else:
                        logger.warning(
                            f"No analysis data for {symbol} {timeframe}"
                        )
            
            logger.info("\n" + "=" * 50)
            
        except Exception as e:
            logger.error(f"Error generating analysis report: {e}")

    def _log_analysis_results(
        self,
        symbol: str,
        timeframe: str,
        analysis: Dict
    ):
        """記錄分析結果"""
        vol_stats = analysis.get('volatility_stats', {})
        trend_analysis = analysis.get('trend_analysis', {})
        
        logger.info(
            f"\n{symbol} {timeframe} Analysis:\n"
            f"Market Regime: {analysis.get('market_regime')}\n"
            f"Market Score: {analysis.get('market_score')}\n"
            f"Volatility: {vol_stats.get('current', 0):.2f}% "
            f"(Mean: {vol_stats.get('mean', 0):.2f}%)\n"
            f"Trend: {trend_analysis.get('direction', 'Unknown')} "
            f"(Strength: {trend_analysis.get('strength', 0):.1f}%)"
        )

def parse_args():
    """解析命令行參數"""
    import argparse
    parser = argparse.ArgumentParser(description='Market Analysis Tool')
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['BTCUSDT', 'ETHUSDT'],
        help='Trading symbols to analyze'
    )
    
    parser.add_argument(
        '--timeframes',
        nargs='+',
        default=['1h', '4h', '1d'],
        help='Timeframes to analyze'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to analyze'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update existing analysis'
    )
    
    return parser.parse_args()

async def main():
    args = parse_args()
    
    try:
        db = SessionLocal()
        analyzer = MarketAnalyzer(db)
        
        start_time = datetime.now()
        logger.info(
            f"Starting market analysis for symbols: {args.symbols}\n"
            f"Timeframes: {args.timeframes}\n"
            f"Days: {args.days}"
        )
        
        await analyzer.analyze_markets(
            symbols=args.symbols,
            timeframes=args.timeframes,
            days=args.days,
            force_update=args.force
        )
        
        duration = datetime.now() - start_time
        logger.info(f"\nAnalysis completed in {duration}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())