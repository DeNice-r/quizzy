from sqlalchemy import Column, BigInteger, Integer, ForeignKey, String, Boolean

from db.models.Quiz import Quiz
from db.engine import BaseModel


class QuizQuestion(BaseModel):
    __tablename__ = 'quiz_question'

    def __init__(self, quiz_id, question, multi):
        self.quiz_id = quiz_id
        self.question = question
        self.multi = multi

    id = Column(BigInteger, primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
    question = Column(String(256), nullable=False)
    multi = Column(Boolean, default=False, nullable=False)