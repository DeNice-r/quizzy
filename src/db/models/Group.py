from sqlalchemy import Column, Integer, ForeignKey, String

from db.models.User import User
from db.engine import BaseModel


class Group(BaseModel):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(500))
