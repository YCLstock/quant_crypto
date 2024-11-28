"""add_kline_data

Revision ID: e826449cda85
Revises: initial_migration
Create Date: 2024-11-12 19:35:46.824867+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e826449cda85'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'kline_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange_id', sa.Integer(), nullable=False),
        sa.Column('trading_pair_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interval', sa.String(10), nullable=False),  # '1h', '1d'等
        
        # OHLCV數據
        sa.Column('open_price', sa.Float(), nullable=False),
        sa.Column('high_price', sa.Float(), nullable=False),
        sa.Column('low_price', sa.Float(), nullable=False),
        sa.Column('close_price', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        
        # 額外統計數據
        sa.Column('quote_volume', sa.Float(), nullable=True),
        sa.Column('number_of_trades', sa.Integer(), nullable=True),
        sa.Column('taker_buy_base_volume', sa.Float(), nullable=True),
        sa.Column('taker_buy_quote_volume', sa.Float(), nullable=True),
        
        # 額外欄位用於數據分析
        sa.Column('vwap', sa.Float(), nullable=True),  # 成交量加權平均價
        sa.Column('volatility', sa.Float(), nullable=True),  # 波動率
        
        # 元數據
        sa.Column('source', sa.String(50), nullable=True),  # 數據來源
        sa.Column('is_complete', sa.Boolean(), default=True),  # 數據是否完整
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        
        # 主鍵
        sa.PrimaryKeyConstraint('id'),
        
        # 外鍵
        sa.ForeignKeyConstraint(['exchange_id'], ['exchanges.id'], ),
        sa.ForeignKeyConstraint(['trading_pair_id'], ['trading_pairs.id'], ),
        
        # 索引
        sa.Index('idx_kline_timestamp', 'timestamp'),
        sa.Index('idx_kline_trading_pair', 'trading_pair_id'),
        sa.Index('idx_kline_interval', 'interval'),
        sa.Index('idx_kline_complete', 'is_complete'),
        
        # 複合索引
        sa.Index('idx_kline_pair_time', 'trading_pair_id', 'timestamp'),
        sa.Index('idx_kline_pair_interval', 'trading_pair_id', 'interval'),
        
        # 唯一約束
        sa.UniqueConstraint('trading_pair_id', 'timestamp', 'interval', name='unique_kline_data')
    )
    
    # 可選：為大型數據集創建分區
    # 注意：這需要PostgreSQL 10+並啟用分區功能
    """
    op.execute('''
        CREATE TABLE IF NOT EXISTS kline_data_y2024m01 PARTITION OF kline_data
        FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
        
        CREATE TABLE IF NOT EXISTS kline_data_y2024m02 PARTITION OF kline_data
        FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
    ''')
    """

def downgrade():
    op.drop_table('kline_data')