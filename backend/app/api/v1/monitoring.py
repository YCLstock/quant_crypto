# app/api/v1/monitoring.py

from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.monitoring.depth_monitor import DepthMonitor
from app.services.depth_archiver import DepthArchiver
from app.core.logging import logger

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/depth/metrics/{symbol}")
async def get_depth_metrics(
    symbol: str,
    db: Session = Depends(get_db)
) -> Dict:
    """獲取深度數據監控指標"""
    try:
        monitor = DepthMonitor(db)
        metrics = monitor.get_metrics_summary(symbol)
        
        if not metrics:
            raise HTTPException(
                status_code=404,
                detail=f"No metrics found for symbol {symbol}"
            )
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting depth metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/depth/archived/{symbol}")
async def get_archived_depth_data(
    symbol: str,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """獲取歸檔的深度數據"""
    try:
        archiver = DepthArchiver(db)
        data = await archiver.get_archived_data(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time
        )
        
        return data
    except Exception as e:
        logger.error(f"Error getting archived depth data: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/depth/system-status")
async def get_system_status(
    db: Session = Depends(get_db)
) -> Dict:
    """獲取系統狀態概覽"""
    try:
        # 收集各種系統指標
        status = {
            "database": await _check_database_status(db),
            "archival": await _check_archival_status(db),
            "monitoring": await _check_monitoring_status(db)
        }
        
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def _check_database_status(db: Session) -> Dict:
    """檢查數據庫狀態"""
    try:
        # 檢查最新數據時間
        result = await db.execute("""
            SELECT 
                COUNT(*) as total_records,
                MAX(timestamp) as latest_record,
                AVG(processing_time) as avg_processing_time
            FROM order_book_depths
            WHERE timestamp > NOW() - INTERVAL '1 day'
        """)
        stats = result.first()
        
        return {
            "total_records_24h": stats.total_records,
            "latest_record_time": stats.latest_record.isoformat() 
                if stats.latest_record else None,
            "avg_processing_time": float(stats.avg_processing_time or 0)
        }
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return {"error": str(e)}

async def _check_archival_status(db: Session) -> Dict:
    """檢查歸檔狀態"""
    try:
        result = await db.execute("""
            SELECT 
                COUNT(*) as archived_count,
                COUNT(*) FILTER (WHERE is_archived) as total_archived,
                MAX(timestamp) FILTER (WHERE is_archived) as latest_archive
            FROM order_book_depths
        """)
        stats = result.first()
        
        return {
            "total_records": stats.archived_count,
            "archived_records": stats.total_archived,
            "latest_archive_time": stats.latest_archive.isoformat() 
                if stats.latest_archive else None
        }
    except Exception as e:
        logger.error(f"Error checking archival status: {e}")
        return {"error": str(e)}

async def _check_monitoring_status(db: Session) -> Dict:
    """檢查監控系統狀態"""
    try:
        # 獲取最近的監控指標
        result = await db.execute("""
            SELECT 
                COUNT(DISTINCT symbol) as active_symbols,
                AVG(processing_time) as avg_processing_time,
                MAX(timestamp) as latest_update
            FROM order_book_depths
            WHERE timestamp > NOW() - INTERVAL '5 minute'
        """)
        stats = result.first()
        
        return {
            "active_symbols": stats.active_symbols,
            "avg_processing_time_5m": float(stats.avg_processing_time or 0),
            "latest_update": stats.latest_update.isoformat() 
                if stats.latest_update else None,
            "monitoring_status": "active" 
                if stats.latest_update and 
                   stats.latest_update > datetime.now() - timedelta(minutes=5)
                else "inactive"
        }
    except Exception as e:
        logger.error(f"Error checking monitoring status: {e}")
        return {"error": str(e)}

@router.post("/depth/maintenance/trigger")
async def trigger_maintenance(
    db: Session = Depends(get_db)
) -> Dict:
    """手動觸發維護任務"""
    try:
        archiver = DepthArchiver(db)
        
        # 執行歸檔和清理
        archived_count = await archiver.archive_old_data()
        cleaned_count = await archiver.cleanup_archived_data()
        
        return {
            "status": "success",
            "archived_records": archived_count,
            "cleaned_records": cleaned_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering maintenance: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )