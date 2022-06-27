from sqlalchemy import Column, BigInteger, SmallInteger, ForeignKey

from db.engine import BaseModel
from db.models.User import User


class Admin(BaseModel):
    __tablename__ = 'admin'

    def __init__(self, user_id):
        self.user_id = user_id

    id = Column(SmallInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id, ondelete='CASCADE'), nullable=False, unique=True)
