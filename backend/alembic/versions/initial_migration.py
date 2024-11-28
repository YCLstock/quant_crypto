from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 創建 exchanges 表
    op.create_table('exchanges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('api_key', sa.String(100)),
        sa.Column('api_secret', sa.String(100)),
        sa.Column('api_url', sa.String(200)),
        sa.Column('status', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # 創建 trading_pairs 表
    op.create_table('trading_pairs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange_id', sa.Integer(), sa.ForeignKey('exchanges.id')),
        sa.Column('base_currency', sa.String(10), nullable=False),
        sa.Column('quote_currency', sa.String(10), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )

    # 創建 market_data 表
    op.create_table('market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange_id', sa.Integer(), sa.ForeignKey('exchanges.id')),
        sa.Column('trading_pair_id', sa.Integer(), sa.ForeignKey('trading_pairs.id')),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('side', sa.String(4), nullable=False),
        sa.Column('open_price', sa.Float()),
        sa.Column('high_price', sa.Float()),
        sa.Column('low_price', sa.Float()),
        sa.Column('close_price', sa.Float()),
        sa.Column('volume', sa.Float()),
        sa.Column('quote_volume', sa.Float()),
        sa.Column('number_of_trades', sa.Integer()),
        sa.Column('taker_buy_base_volume', sa.Float()),
        sa.Column('taker_buy_quote_volume', sa.Float()),
        sa.Column('weighted_average_price', sa.Float()),
        sa.Column('price_change', sa.Float()),
        sa.Column('price_change_percent', sa.Float()),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )

    # 創建索引
    op.create_index(op.f('ix_market_data_timestamp'), 'market_data', ['timestamp'])
    op.create_index(op.f('ix_market_data_price'), 'market_data', ['price'])

def downgrade():
    # 刪除索引
    op.drop_index(op.f('ix_market_data_timestamp'), table_name='market_data')
    op.drop_index(op.f('ix_market_data_price'), table_name='market_data')
    
    # 刪除表格
    op.drop_table('market_data')
    op.drop_table('trading_pairs')
    op.drop_table('exchanges')