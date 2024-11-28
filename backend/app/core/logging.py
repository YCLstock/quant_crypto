# app/core/logging.py
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path

from .config import settings

def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """設置日誌配置"""
    # 使用參數或設定檔的值
    level = level or settings.LOGGING_LEVEL
    log_format = log_format or settings.LOG_FORMAT

    # 配置根日誌記錄器
    root_logger = logging.getLogger()
    
    # 設置日誌級別
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # 創建格式化器
    formatter = logging.Formatter(log_format)

    # 配置控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 配置文件處理器
    if log_file:
        # 使用絕對路徑
        log_path = Path(log_file)
        if not log_path.is_absolute():
            # 如果是相對路徑，則使用專案根目錄
            log_path = Path(__file__).parent.parent.parent / 'logs' / log_file

        # 確保日誌目錄存在
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            str(log_path),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

# 創建一個用於應用程序的日誌記錄器
logger = logging.getLogger("crypto_analytics")

# 初始化日誌配置
if not logger.handlers:  # 只在沒有處理器時初始化
    setup_logging()