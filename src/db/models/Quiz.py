from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from db.models.User import User
from db.engine import BaseModel, db_session

from utils import generate_token


class Quiz(BaseModel):
    __tablename__ = 'quiz'

    def __init__(self, name, author_id, is_public, is_statistical):
        self.name = name
        self.author_id = author_id
        self.is_public = is_public
        self.is_statistical = is_statistical

        self.regenerate_token()

    def __repr__(self):
        return f'<Quiz: {{name: {self.name}, author_id={self.author_id}, is_public={self.is_public}, ' \
               f'is_statistical={self.is_statistical}, token={self.token}}}>'

    @hybrid_property
    def categories(self):
        return [x.name for x in self.categories_ref]

    def regenerate_token(self):
        token = generate_token()
        with db_session.begin() as s:
            while s.query(Quiz.id).filter(Quiz.token == token).one_or_none() is not None:
                token = generate_token()
        self.token = token

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    author_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    is_statistical = Column(Boolean, default=False, nullable=False)
    token = Column(String(10), unique=True, nullable=False)

    questions = relationship('QuizQuestion', backref=backref('quiz', lazy='select'),
                             cascade='all, delete, delete-orphan')
    categories_ref = relationship('QuizCategoryType',
                                  secondary='quiz_category',
                                  primaryjoin='Quiz.id==QuizCategory.quiz_id',
                                  secondaryjoin='QuizCategoryType.id==QuizCategory.category_id')
