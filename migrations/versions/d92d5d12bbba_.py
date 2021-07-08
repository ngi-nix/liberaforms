"""empty message

Revision ID: d92d5d12bbba
Revises: a6b48ae7220a
Create Date: 2021-06-01 20:26:10.886744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd92d5d12bbba'
down_revision = 'a6b48ae7220a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('media',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('alt_text', sa.String(), nullable=True),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('file_size', sa.String(), nullable=False),
    sa.Column('storage_name', sa.String(), nullable=False),
    sa.Column('local_filesystem', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_id'), 'media', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_media_id'), table_name='media')
    op.drop_table('media')
    # ### end Alembic commands ###
