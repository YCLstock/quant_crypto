# app/services/depth_archiver.py

import zlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.market import OrderBookDepth
from app.core.config import settings

class DepthArchiver:
    def __init__(self, db: Session):
        self.db = db
        self.compression_level = 6  # zlib壓縮級別 (0-9)
    
    def compress_depth_data(self, data: Dict) -> bytes:
        """壓縮深度數據"""
        json_str = json.dumps(data)
        return zlib.compress(json_str.encode(), self.compression_level)
    
    def decompress_depth_data(self, compressed_data: bytes) -> Dict:
        """解壓深度數據"""
        json_str = zlib.decompress(compressed_data).decode()
        return json.loads(json_str)
    
    async def archive_old_data(self, days_old: int = 7):
        """歸檔舊的深度數據"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # 查找需要歸檔的數據
            query = select(OrderBookDepth).filter(
                OrderBookDepth.timestamp < cutoff_date,
                OrderBookDepth.is_archived == False  # 假設添加了is_archived欄位
            )
            
            results = await self.db.execute(query)
            depth_records = results.scalars().all()
            
            archived_count = 0
            for record in depth_records:
                # 壓縮數據
                depth_data = {
                    'bids': record.bids,
                    'asks': record.asks,
                    'timestamp': record.timestamp.isoformat(),
                    'last_update_id': record.last_update_id
                }
                
                compressed_data = self.compress_depth_data(depth_data)
                
                # 更新記錄
                record.compressed_data = compressed_data
                record.is_archived = True
                record.bids = None  # 清除原始數據
                record.asks = None
                
                archived_count += 1
                
                # 每100條記錄提交一次
                if archived_count % 100 == 0:
                    await self.db.commit()
            
            # 最後提交
            if archived_count % 100 != 0:
                await self.db.commit()
            
            logger.info(f"Archived {archived_count} depth records")
            
            return archived_count
            
        except Exception as e:
            logger.error(f"Error archiving depth data: {e}")
            await self.db.rollback()
            raise
    
    async def cleanup_archived_data(self, days_to_keep: int = 90):
        """清理已歸檔的舊數據"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 刪除超過保留期限的歸檔數據
            query = select(OrderBookDepth).filter(
                OrderBookDepth.timestamp < cutoff_date,
                OrderBookDepth.is_archived == True
            )
            
            results = await self.db.execute(query)
            old_records = results.scalars().all()
            
            deleted_count = 0
            for record in old_records:
                self.db.delete(record)
                deleted_count += 1
                
                # 每100條記錄提交一次
                if deleted_count % 100 == 0:
                    await self.db.commit()
            
            # 最後提交
            if deleted_count % 100 != 0:
                await self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} archived depth records")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up archived data: {e}")
            await self.db.rollback()
            raise
    
    async def get_archived_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """獲取歸檔數據"""
        try:
            query = select(OrderBookDepth).filter(
                OrderBookDepth.trading_pair.has(symbol=symbol),
                OrderBookDepth.timestamp.between(start_time, end_time),
                OrderBookDepth.is_archived == True
            )
            
            results = await self.db.execute(query)
            archived_records = results.scalars().all()
            
            decompressed_data = []
            for record in archived_records:
                if record.compressed_data:
                    depth_data = self.decompress_depth_data(record.compressed_data)
                    decompressed_data.append(depth_data)
            
            return decompressed_data
            
        except Exception as e:
            logger.error(f"Error retrieving archived data: {e}")
            raise
    
    async def run_maintenance(self):
        """運行維護任務"""
        while True:
            try:
                # 歸檔7天前的數據
                await self.archive_old_data(days_old=7)
                
                # 清理90天前的歸檔數據
                await self.cleanup_archived_data(days_to_keep=90)
                
                # 每天運行一次
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Error in maintenance task: {e}")
                await asyncio.sleep(3600)  # 出錯後等待1小時後重試