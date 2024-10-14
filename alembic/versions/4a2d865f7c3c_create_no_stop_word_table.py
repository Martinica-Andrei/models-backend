"""create_no_stop_word_table

Revision ID: 4a2d865f7c3c
Revises: d5d192e93428
Create Date: 2024-10-14 20:10:38.987587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '4a2d865f7c3c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('no_stop_word',
    sa.Column('value', sa.String(length=1), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('value')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('no_stop_word')
    # ### end Alembic commands ###
