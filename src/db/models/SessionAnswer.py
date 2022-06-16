from sqlalchemy import Column, BigInteger, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY

from db.models.QuestionAnswer import QuestionAnswer
from db.models.QuizQuestion import QuizQuestion
from db.models.Session import Session
from db.engine import BaseModel


class SessionAnswer(BaseModel):
    __tablename__ = 'session_answer'

    def __init__(self, session_id, question_id, answer_ids: list):
        self.session_id = session_id
        self.question_id = question_id
        self.answer_ids = answer_ids.copy()

    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey(Session.id, ondelete='CASCADE'), nullable=False)
    question_id = Column(Integer, ForeignKey(QuizQuestion.id, ondelete='CASCADE'), nullable=False)
    answer_ids = Column(ARRAY(BigInteger, as_tuple=ForeignKey(QuestionAnswer.id, ondelete='CASCADE')), nullable=False)