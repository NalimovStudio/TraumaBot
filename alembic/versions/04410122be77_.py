"""fix duplicate tables

Revision ID: 04410122be77
Revises: ad64090b7670
Create Date: 2025-10-27 09:14:16.238595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04410122be77'
down_revision = 'ad64090b7670'
branch_labels = None
depends_on = None


def upgrade():
    # Таблицы уже созданы в миграции 128c1008f804
    # Оставляем пустую миграцию чтобы не ломать последовательность
    pass


def downgrade():
    # Оставляем пустым для симметрии
    pass