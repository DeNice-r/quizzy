from sqlalchemy import Column, BigInteger, Integer, ForeignKey, String, Boolean

from db.models.QuizQuestion import QuizQuestion
from db.engine import BaseModel


class QuestionAnswer(BaseModel):
    __tablename__ = 'question_answer'

    def __init__(self, question_id, answer, is_right):
        self.question_id = question_id
        self.answer = answer
        self.is_right = is_right

    id = Column(BigInteger, primary_key=True)
    question_id = Column(Integer, ForeignKey(QuizQuestion.id, ondelete='CASCADE'), nullable=False)
    answer = Column(String(256), nullable=False)
    is_right = Column(Boolean, default=False, nullable=False)