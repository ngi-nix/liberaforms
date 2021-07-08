"""empty message

Revision ID: 9bda3a5366a0
Revises: abc23f54d93c
Create Date: 2021-06-26 14:05:01.546906

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9bda3a5366a0'
down_revision = 'abc23f54d93c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('site', sa.Column('email_footer', sa.String(), nullable=True))
    op.alter_column('site', 'menuColor', new_column_name='primary_color')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('site', 'email_footer')
    op.alter_column('site', 'primary_color', new_column_name='menuColor')
    # ### end Alembic commands ###
