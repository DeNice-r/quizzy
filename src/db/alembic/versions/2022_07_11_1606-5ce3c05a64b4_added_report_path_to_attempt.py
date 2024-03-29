"""Added report path to attempt.

Revision ID: 5ce3c05a64b4
Revises: b229616e9fc6
Create Date: 2022-07-11 16:06:05.636602

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ce3c05a64b4'
down_revision = 'b229616e9fc6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('attempt', sa.Column('report_path', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('attempt', 'report_path')
    # ### end Alembic commands ###
