from typing import Any, Dict, Optional, List, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field

class Settings(BaseSettings):
    # 基本配置
    PROJECT_NAME: str = "Crypto Analytics"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 日誌配置
    LOGGING_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None  # 測試時不寫入文件

    # 數據庫配置
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5434"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "crypto_analytics"
    DATABASE_URL: Optional[str] = None

    # Binance API配置
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""

    # 歷史數據收集配置
    HISTORICAL_DATA_TIMEFRAMES: List[str] = [
        "1m", "5m", "15m", "30m",  # 分鐘級別
        "1h", "4h", "12h",         # 小時級別
        "1d", "1w"                 # 日/週級別
    ]

    # Binance API 限制配置
    BINANCE_RATE_LIMIT: int = 1200
    BINANCE_WEIGHT_LIMIT: int = 1000
    BINANCE_MAX_LIMIT: int = 1000
    
    # 數據收集配置
    HISTORICAL_INITIAL_DAYS: int = 30
    HISTORICAL_UPDATE_INTERVAL: int = 60
    HISTORICAL_BATCH_SIZE: int = 500

    # 波動率配置
    VOLATILITY_FACTORS: Dict[str, int] = {
        '1m': 525600,  # 365 * 24 * 60
        '5m': 105120,  # 365 * 24 * 12
        '15m': 35040,  # 365 * 24 * 4
        '30m': 17520,  # 365 * 24 * 2
        '1h': 8760,    # 365 * 24
        '4h': 2190,    # 365 * 6
        '1d': 252,     # 交易日數
        '1w': 52,      # 週數
    }

    VOLATILITY_WINDOWS: Dict[str, int] = {
        '1m': 1440,    # 1天
        '5m': 288,     # 1天
        '15m': 96,     # 1天
        '30m': 48,     # 1天
        '1h': 24,      # 1天
        '4h': 30,      # 5天
        '1d': 20,      # 20天
        '1w': 12,      # 12週
    }

    # 時間相關配置
    USE_UTC: bool = True  # 統一使用UTC時間
    TIMEZONE: str = "UTC"  # 默認時區
    
    # 數據收集設置
    MIN_DATA_POINTS: Dict[str, int] = {
        '1m': 60,   # 至少1小時數據
        '5m': 24,   # 至少2小時數據
        '15m': 16,  # 至少4小時數據
        '30m': 16,  # 至少8小時數據
        '1h': 24,   # 至少1天數據
        '4h': 30,   # 至少5天數據
        '1d': 20,   # 至少20天數據
        '1w': 12,   # 至少12週數據
    }

    # 波動率週期定義 - 添加型別標註
    VOLATILITY_PERIODS: Dict[str, Dict[str, int]] = {
        'short': {
            '1h': 12,    # 12小時
            '4h': 6,     # 1天
            '1d': 7,     # 7天
        },
        'medium': {
            '1h': 24,    # 1天
            '4h': 30,    # 5天
            '1d': 20,    # 20天
        },
        'long': {
            '1h': 168,   # 7天
            '4h': 180,   # 30天
            '1d': 60,    # 60天
        }
    }

    # 技術指標配置
    MOVING_AVERAGE_WINDOWS: List[int] = [7, 25, 99]  # MA週期
    RSI_PERIOD: int = 14
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD_DEV: float = 2.0
    
    # 數據存儲配置
    DATA_RETENTION_DAYS: int = 365
    CACHE_RETENTION_HOURS: int = 24
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_EXPIRE_TIME: int = 3600

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def get_timeframe_seconds(self, timeframe: str) -> int:
        """將時間週期轉換為秒數"""
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        
        if unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        elif unit == 'w':
            return value * 604800
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")
    
    def get_collection_interval(self, timeframe: str) -> int:
        """獲取數據收集間隔"""
        seconds = self.get_timeframe_seconds(timeframe)
        # 收集間隔為週期的 1/2
        return max(seconds // 2, self.HISTORICAL_UPDATE_INTERVAL)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# 實例化配置
settings = Settings()