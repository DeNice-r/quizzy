"""Changed Admin user_id type

Revision ID: 779ae37817c4
Revises: a0706532f208
Create Date: 2022-07-19 18:36:44.037996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '779ae37817c4'
down_revision = 'a0706532f208'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'admin', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'admin', type_='foreignkey')
    # ### end Alembic commands ###
