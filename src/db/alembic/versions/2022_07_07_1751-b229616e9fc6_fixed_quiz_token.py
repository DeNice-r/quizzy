"""Fixed Quiz.token.

Revision ID: b229616e9fc6
Revises: fb1e3dfad45a
Create Date: 2022-07-07 17:51:55.719393

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b229616e9fc6'
down_revision = 'fb1e3dfad45a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'quiz', ['token'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'quiz', type_='unique')
    # ### end Alembic commands ###
