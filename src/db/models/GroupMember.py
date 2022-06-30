from sqlalchemy import Column, BigInteger, ForeignKey, Integer

from db.models.User import User
from db.models.Group import Group
from db.engine import BaseModel


class GroupMember(BaseModel):
    __tablename__ = 'group_member'

    def __init__(self, user_id: int, group_id: int):
        self.user_id = user_id
        self.group_id = group_id

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    group_id = Column(Integer, ForeignKey(Group.id, ondelete='CASCADE'), nullable=False)
