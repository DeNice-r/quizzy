import datetime

from sqlalchemy import Column, BigInteger, ForeignKey, Integer, DateTime, FLOAT

from db.models.Quiz import Quiz
from db.models.Session import Session
from db.models.User import User
from db.engine import BaseModel


class Attempt(BaseModel):
    __tablename__ = 'attempt'

    def __init__(self, user_id, quiz_id, started_on):
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.started_on = started_on

    @classmethod
    def from_session(cls, quiz_session: Session):
        return cls(quiz_session.user_id, quiz_session.quiz_id, quiz_session.started_on)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id, ondelete='SET NULL'), nullable=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
    started_on = Column(DateTime, nullable=False)
    finished_on = Column(DateTime, default=datetime.datetime.now, nullable=False)
    mark = Column(FLOAT, nullable=True)
