from sqlalchemy import Column, BigInteger, ForeignKey, Integer, UniqueConstraint, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from db.models.Attempt import Attempt
from db.models.QuestionAnswer import QuestionAnswer
from db.models.QuizQuestion import QuizQuestion
from db.models.SessionAnswer import SessionAnswer
from db.engine import BaseModel


class AttemptAnswer(BaseModel):
    __tablename__ = 'attempt_answer'

    def __init__(self, attempt_id, question_id, answer_ids: tuple):
        self.attempt_id = attempt_id
        self.question_id = question_id
        self.answer_ids = answer_ids

    def __repr__(self):
        return f'Id: {self.id}, attempt_id: {self.attempt_id}, question_id: {self.question_id}, ' \
               f'answer_ids: {self.answer_ids}'

    @classmethod
    def from_session_answer(cls, attempt_id: int, session_answer: SessionAnswer):
        return cls(attempt_id, session_answer.question_id, tuple(session_answer.answer_ids))  # !!!!!!!!!!

    id = Column(BigInteger, primary_key=True)
    attempt_id = Column(BigInteger, ForeignKey(Attempt.id, ondelete='CASCADE'), nullable=False)
    question_id = Column(Integer, ForeignKey(QuizQuestion.id, ondelete='CASCADE'), nullable=False)
    answer_ids = Column(ARRAY(BigInteger, as_tuple=ForeignKey(QuestionAnswer.id)), nullable=False)
    UniqueConstraint(attempt_id, question_id, name='unique_attempt_answer')
    mark = Column(Numeric, nullable=False, server_default='0')
    # answers = relationship('QuestionAnswer', primaryjoin='QuestionAnswer.id == any(AttemptAnswer.answer_ids)')
