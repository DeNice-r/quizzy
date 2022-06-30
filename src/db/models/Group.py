from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref

from db.models.User import User
from db.engine import BaseModel


class Group(BaseModel):
    __tablename__ = 'group'

    def __init__(self, owner_id, is_public, name, description):
        self.owner_id = owner_id
        self.is_public = is_public
        self.name = name
        self.description = description

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    is_public = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(512), nullable=True)

    token_ref = relationship('GroupToken', backref=backref('group', lazy='select'), uselist=False,
                             cascade='all, delete, delete-orphan')
    members = relationship('GroupMember', backref=backref('group', lazy='select'),
                           cascade='all, delete, delete-orphan')
