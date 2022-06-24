from sqlalchemy import Column, String, Integer, ForeignKey

from db.models.Quiz import Quiz
from db.engine import BaseModel
from utils import generate_token


class QuizToken(BaseModel):
    __tablename__ = 'quiz_token'

    def __init__(self, quiz_id):
        self.token = generate_token()
        self.quiz_id = quiz_id

    token = Column(String(10), primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
