# scripts/run_app.py

import sys
from pathlib import Path
import uvicorn
import asyncio
from app.core.logging import logger

sys.path.append(str(Path(__file__).parent.parent))

def run_app():
    """運行FastAPI應用"""
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # 生產環境關閉自動重載
            workers=4,     # 生產環境使用多個worker
            log_config=None  # 使用自定義的日誌配置
        )
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_app()