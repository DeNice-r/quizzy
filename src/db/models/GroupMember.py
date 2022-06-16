from sqlalchemy import Column, BigInteger, ForeignKey, Integer

from db.models.User import User
from db.engine import BaseModel


class GroupMember(BaseModel):
    __tablename__ = 'group_member'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    group_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)