"""Added Admin table try 3.

Revision ID: 2675b518f5f3
Revises: 7115151aee2b
Create Date: 2022-06-27 16:18:39.347888

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2675b518f5f3'
down_revision = '7115151aee2b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'admin', 'user', ['user_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'admin', type_='foreignkey')
    # ### end Alembic commands ###
