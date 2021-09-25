"""empty message

Revision ID: 64ba16324cef
Revises: a09931e35c2d
Create Date: 2021-09-23 16:36:10.837483

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

# revision identifiers, used by Alembic.
revision = '64ba16324cef'
down_revision = 'a09931e35c2d'
branch_labels = None
depends_on = None

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    admin = sa.Column(MutableDict.as_mutable(JSONB), nullable=False)

def upgrade():
    session = Session(bind=op.get_bind())
    users = session.query(User).all()
    for user in users:
        user.admin = {**user.admin, **{'forms': {}, 'users': {}, 'userforms': {}}}
    session.commit()
    session.close()

def downgrade():
    session = Session(bind=op.get_bind())
    users = session.query(User).all()
    for user in users:
        del user.admin['forms']
        del user.admin['users']
        del user.admin['userforms']
    session.commit()
    session.close()
