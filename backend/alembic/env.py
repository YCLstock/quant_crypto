from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os,sys
from dotenv import load_dotenv

# 添加父目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 載入環境變量
load_dotenv()

# 獲取配置對象
config = context.config

# 引入 models 中定義的 Base
from app.models.market import Base

# 設置數據庫 URL
# def get_url():
#     return os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5434/crypto_analytics")
def get_url():
    url = os.getenv("DATABASE_URL")
    if url is None:
        # 提供一個默認的數據庫 URL
        return "postgresql://postgres:postgres@localhost:5434/crypto_analytics"
    return url

# 更新 alembic.ini 中的 sqlalchemy.url
config.set_main_option("sqlalchemy.url", get_url())

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 設置目標 metadata
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()