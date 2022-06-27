from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from db.models.Quiz import Quiz
from db.engine import BaseModel, db_session
from utils import generate_token


class QuizToken(BaseModel):
    __tablename__ = 'quiz_token'

    def __init__(self, quiz_id):
        token = generate_token()
        with db_session.begin() as s:
            while s.get(QuizToken, token) is not None:
                token = generate_token()
        self.token = token
        self.quiz_id = quiz_id

    def __repr__(self):
        return f'<{self.token}: {self.quiz_id}>'

    token = Column(String(10), primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), unique=True)

