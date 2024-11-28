# app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Dict
import uvicorn
import asyncio  # 添加這個導入
import os
import signal
from app.core.config import settings
from app.core.logging import logger
from app.api.v1 import router as api_router  # 引入主路由

# 創建FastAPI應用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Crypto Analytics API"
)

# 配置CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  # Next.js 前端
    "http://localhost:8000",  # API 服務
]

# main.py 中的 CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js 開發服務器
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["Content-Length"],
    max_age=3600,  # 預檢請求的有效期（秒）
)

# 添加中間件來記錄請求
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # 添加詳細的日誌
    logger.info(
        f"Method: {request.method} "
        f"Path: {request.url.path} "
        f"Query Params: {request.query_params} "
        f"Duration: {duration:.3f}s "
        f"Status: {response.status_code}"
    )
    
    return response

# 全局異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Global exception occurred:\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Error: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": request.url.path,
            "timestamp": time.time()
        }
    )

# 添加API路由
app.include_router(
    api_router,
    prefix=settings.API_V1_STR
)

@app.get("/")
def read_root() -> Dict:
    """根路徑響應"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "active",
        "docs_url": "/docs",
        "timestamp": time.time()
    }

@app.get("/health")
def health_check() -> Dict:
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

from app.core.shutdown import graceful_shutdown
from app.core.database import SessionLocal, engine
from app.models.market import init_models  # 導入模型初始化函數

async def init_database():
    """初始化數據庫"""
    try:
        # 初始化數據庫模型
        init_models(engine)
        logger.info("Database models initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def cleanup_database():
    """清理數據庫連接"""
    try:
        db = SessionLocal()
        if hasattr(db, 'close'):
            if asyncio.iscoroutinefunction(db.close):
                await db.close()
            else:
                db.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

async def cleanup_monitors():
    """清理監控器"""
    try:
        # 停止所有監控任務
        # 這裡添加停止監控的邏輯
        logger.info("Monitors stopped")
    except Exception as e:
        logger.error(f"Error stopping monitors: {e}")

# 啟動事件
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    try:
        # 初始化數據庫
        await init_database()
        
        # 註冊清理處理器
        graceful_shutdown.add_shutdown_handler(cleanup_database)
        graceful_shutdown.add_shutdown_handler(cleanup_monitors)
        
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# 關閉事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    try:
        await cleanup_database()
        await cleanup_monitors()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# 添加API終止端點
@app.post("/api/v1/system/shutdown")
async def shutdown_application():
    """API終止端點"""
    logger.info("Shutdown requested via API")
    # 觸發SIGTERM信號
    os.kill(os.getpid(), signal.SIGTERM)
    return {"message": "Shutting down..."}

# 如果直接運行這個文件
if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # 修改為正確的導入路徑
        host="0.0.0.0",
        port=8000,
        reload=True,  # 開發模式下啟用自動重載
        workers=1,    # 在開發模式下使用單個worker
        log_level="info"
    )