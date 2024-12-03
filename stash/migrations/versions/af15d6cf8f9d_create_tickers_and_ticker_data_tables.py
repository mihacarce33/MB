"""Create Tickers and ticker_data tables

Revision ID: af15d6cf8f9d
Revises: 
Create Date: 2024-12-02 20:13:38.886668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af15d6cf8f9d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create `Tickers` table
    op.create_table(
        'Tickers',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('ticker', sa.String(255), nullable=False, unique=True)
    )

    # Create `ticker_data` table
    op.create_table(
        'ticker_data',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('ticker', sa.VARCHAR(255), sa.ForeignKey('Tickers.ticker'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('last_transaction_price', sa.Float),
        sa.Column('max_price', sa.Float),
        sa.Column('min_price', sa.Float),
        sa.Column('average_price', sa.Float),
        sa.Column('percent_change', sa.Float),
        sa.Column('quantity', sa.Integer),
        sa.Column('best_turnover', sa.Float),
        sa.Column('total_turnover', sa.Float),
        sa.UniqueConstraint('date', 'ticker', name='uq_date_ticker')
    )


def downgrade():
    # Drop `ticker_data` table
    op.drop_table('ticker_data')

    # Drop `Tickers` table
    op.drop_table('Tickers')