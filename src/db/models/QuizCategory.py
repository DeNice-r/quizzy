from sqlalchemy import Column, BigInteger, Integer, ForeignKey, SmallInteger, UniqueConstraint

from db.models.Quiz import Quiz
from db.models.QuizCategoryType import QuizCategoryType
from db.engine import BaseModel


class QuizCategory(BaseModel):
    __tablename__ = 'quiz_category'

    def __init__(self, quiz_id, category_id):
        self.quiz_id = quiz_id
        self.category_id = category_id

    id = Column(BigInteger, primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
    category_id = Column(SmallInteger, ForeignKey(QuizCategoryType.id, ondelete='CASCADE'), nullable=False)
    UniqueConstraint(quiz_id, category_id, name='unique_cat')