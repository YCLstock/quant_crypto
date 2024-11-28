# backend/setup.py
from setuptools import setup, find_packages

setup(
    name="crypto-analytics",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.103.0",
        "uvicorn>=0.23.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "alembic>=1.12.0",
        "redis>=4.6.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "ccxt>=4.0.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.24.1",
        "websockets>=11.0.3",
        "psutil>=5.9.0",  # 添加 psutil 依賴
    ],
)