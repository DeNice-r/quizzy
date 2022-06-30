from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from db.models.Group import Group
from db.engine import BaseModel, db_session
from utils import generate_token


class GroupToken(BaseModel):
    __tablename__ = 'group_token'

    def __init__(self, group_id):
        token = generate_token()
        with db_session.begin() as s:
            while s.get(GroupToken, token) is not None:
                token = generate_token()
        self.token = token
        self.group_id = group_id

    def __repr__(self):
        return f'<{self.token}: {self.group_id}>'

    token = Column(String(10), primary_key=True)
    group_id = Column(Integer, ForeignKey(Group.id, ondelete='CASCADE'), unique=True)
