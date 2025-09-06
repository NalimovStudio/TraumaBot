"""change dialog model

Revision ID: 4b87624d2f57
Revises: ad64090b7670
Create Date: 2025-09-06 16:32:57.752014

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4b87624d2f57'
down_revision = 'ad64090b7670'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users_dialogs_logging', sa.Column('dialogue_id', postgresql.UUID(as_uuid=True), nullable=False, comment="ID сессии диалога"))
    op.add_column('users_dialogs_logging', sa.Column('role', sa.String(), nullable=False, comment="Роль отправителя (user или assistant)"))
    op.alter_column('users_dialogs_logging', 'messages', new_column_name='message_text', existing_type=sa.String(), comment="Текст сообщения")


def downgrade():
    op.alter_column('users_dialogs_logging', 'message_text', new_column_name='message', existing_type=sa.String(), comment="Массив сообщений пользователя")
    op.drop_column('users_dialogs_logging', 'role')
    op.drop_column('users_dialogs_logging', 'dialogue_id')
    # ### end Alembic commands ###
