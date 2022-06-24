from sqlalchemy import Column, Integer, String, ForeignKey, Boolean

from db.models.User import User
from db.engine import BaseModel


class Quiz(BaseModel):
    __tablename__ = 'quiz'

    def __init__(self, name, author_id, is_public, is_statistical):
        self.name = name
        self.author_id = author_id
        self.is_public = is_public
        self.is_statistical = is_statistical

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    author_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    is_statistical = Column(Boolean, default=False, nullable=False)
