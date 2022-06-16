from sqlalchemy import Column, SmallInteger, String

from db.engine import BaseModel


class QuizCategoryType(BaseModel):
    __tablename__ = 'quiz_category_type'

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'<QuizCategoryType id: {self.id}, name: {self.name}>'

    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)