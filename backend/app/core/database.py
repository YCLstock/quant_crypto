# 位置: /backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from influxdb_client import InfluxDBClient
import redis
from ..models.market import Base, init_models
from .config import settings

# PostgreSQL Configuration
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# InfluxDB Configuration
# influxdb_client = InfluxDBClient(
#     url=settings.INFLUXDB_URL,
#     token=settings.INFLUXDB_TOKEN,
#     org=settings.INFLUXDB_ORG
# )

# Redis Configuration
# redis_client = redis.Redis(
#     host=settings.REDIS_HOST,
#     port=settings.REDIS_PORT,
#     db=settings.REDIS_DB,
#     password=settings.REDIS_PASSWORD,
#     decode_responses=True
# )

# 初始化模型
init_models(engine)

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# InfluxDB Dependency
def get_influxdb():
    try:
        yield influxdb_client
    finally:
        influxdb_client.close()

# Redis Dependency
def get_redis():
    try:
        yield redis_client
    finally:
        redis_client.close()