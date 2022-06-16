import datetime

from sqlalchemy import Column, BigInteger, ForeignKey, Integer, DateTime

from db.models.Quiz import Quiz
from db.models.User import User
from db.engine import db_session, BaseModel


class Session(BaseModel):
    __tablename__ = 'session'

    def __init__(self, user_id, quiz_id):
        self.user_id = user_id
        self.quiz_id = quiz_id

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
    started_on = Column(DateTime, default=datetime.datetime.now, nullable=False)
    question_number = Column(Integer, default=0, nullable=False)
