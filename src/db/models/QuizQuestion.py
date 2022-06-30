from sqlalchemy import Column, BigInteger, Integer, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship, backref

from db.models.Quiz import Quiz
from db.engine import BaseModel


class QuizQuestion(BaseModel):
    __tablename__ = 'quiz_question'

    def __init__(self, quiz_id, question, multi):
        self.quiz_id = quiz_id
        self.question = question
        self.is_multi = multi

    def __repr__(self):
        return f'<QuizQuestion: {{id: {self.id}, quiz_id: {self.quiz_id}, question: {self.question}, ' \
               f'is_multi: {self.is_multi}}}>'

    def __str__(self):
        return f'Запитання: {self.question}\n' + \
               f'Відповіді:\n' + \
               '\n'.join([str(x) for x in self.answers])

    id = Column(BigInteger, primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
    question = Column(String(256), nullable=False)
    is_multi = Column(Boolean, default=False, nullable=False)

    answers = relationship('QuestionAnswer', backref=backref('question', lazy='select'),
                           cascade='all, delete, delete-orphan')
