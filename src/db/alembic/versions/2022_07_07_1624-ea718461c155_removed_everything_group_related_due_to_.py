"""Removed everything group-related due to deadlines.

Revision ID: ea718461c155
Revises: f0c0cfbd8a57
Create Date: 2022-07-07 16:24:20.025214

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea718461c155'
down_revision = 'f0c0cfbd8a57'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('group_token')
    op.drop_table('group_member')
    op.drop_table('group')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('group',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('group_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('owner_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('is_public', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['is_public'], ['user.id'], name='group_is_public_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], name='group_owner_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='group_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_table('group_token',
    sa.Column('token', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
    sa.Column('group_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['group.id'], name='group_token_group_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('token', name='group_token_pkey'),
    sa.UniqueConstraint('group_id', name='group_token_group_id_key')
    )
    op.create_table('group_member',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('group_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['group.id'], name='group_member_group_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='group_member_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='group_member_pkey')
    )
    # ### end Alembic commands ###
