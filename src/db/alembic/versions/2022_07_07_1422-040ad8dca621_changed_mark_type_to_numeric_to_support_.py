"""Changed mark type to numeric (to support db-side rounding)

Revision ID: 040ad8dca621
Revises: 390db3fea026
Create Date: 2022-07-07 14:22:39.912530

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '040ad8dca621'
down_revision = '390db3fea026'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('unique_attempt_answer', 'attempt_answer', ['attempt_id', 'question_id'])
    op.alter_column('attempt', 'mark', type_=sa.Numeric)
    op.alter_column('attempt_answer', 'mark', type_=sa.Numeric)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_attempt_answer', 'attempt_answer', type_='unique')
    op.alter_column('attempt', 'mark', type_=sa.Float)
    op.alter_column('attempt_answer', 'mark', type_=sa.Float)
    # ### end Alembic commands ###