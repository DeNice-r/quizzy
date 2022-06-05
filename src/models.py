import datetime

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import Column, SmallInteger, Integer, BigInteger, Boolean, String, DateTime, ForeignKey, JSON,\
    UniqueConstraint

from cfg import db_engine

BaseModel = declarative_base()


class User(BaseModel):
    __tablename__ = 'user'

    def __init__(self, user_id):
        self.id = user_id

    id = Column(BigInteger, autoincrement=False, primary_key=True)
    data = Column(JSON, default={})

    def flag_data(self):
        flag_modified(self, 'data')

    def set_data(self, key, value):
        self.data[key] = value
        flag_modified(self, 'data')

    def clear_data(self):
        self.data.clear()
        flag_modified(self, 'data')


class Quiz(BaseModel):
    __tablename__ = 'quiz'

    def __init__(self, name, author_id, is_public):
        self.name = name
        self.author_id = author_id
        self.is_public = is_public

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    author_id = Column(Integer, ForeignKey(User.id), nullable=False)
    is_public = Column(Boolean, nullable=False, default=True)


class QuizCategoryType(BaseModel):
    __tablename__ = 'quiz_category_type'

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'<QuizCategoryType id: {self.id}, name: {self.name}>'

    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class QuizCategory(BaseModel):
    __tablename__ = 'quiz_category'

    def __init__(self, quiz_id, category_id):
        self.quiz_id = quiz_id
        self.category_id = category_id

    id = Column(BigInteger, primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id), nullable=False)
    category_id = Column(SmallInteger, ForeignKey(QuizCategoryType.id), nullable=False)

    UniqueConstraint(quiz_id, category_id, name='unique_cat')


class QuizQuestion(BaseModel):
    __tablename__ = 'quiz_question'

    def __init__(self, quiz_id, question):
        self.quiz_id = quiz_id
        self.question = question

    id = Column(BigInteger, primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id), nullable=False)
    question = Column(String(256), nullable=False)
    # order_value = Column(SmallInteger)  # Потрібно для того, аби користувач міг змінювати порядок задання питань або
    # # зробити його випадковим


class QuestionAnswer(BaseModel):
    __tablename__ = 'question_answer'

    def __init__(self, question_id, answer, is_right):
        self.question_id = question_id
        self.answer = answer
        self.is_right = is_right

    id = Column(BigInteger, primary_key=True)
    question_id = Column(Integer, ForeignKey(QuizQuestion.id), nullable=False)
    answer = Column(String(256), nullable=False)
    is_right = Column(Boolean, default=False, nullable=False)


class Session(BaseModel):
    __tablename__ = 'session'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id), nullable=False)
    quiz_id = Column(Integer, ForeignKey(Quiz.id), nullable=False)
    started_on = Column(DateTime, default=datetime.datetime.now(), nullable=False)


class SessionAnswer(BaseModel):
    __tablename__ = 'session_answer'

    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey(Session.id), nullable=False)
    question_id = Column(Integer, ForeignKey(QuizQuestion.id), nullable=False)
    answer_id = Column(BigInteger, ForeignKey(QuestionAnswer.id), nullable=False)


class Attempt(BaseModel):
    __tablename__ = 'attempt'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id), nullable=False)
    quiz_id = Column(Integer, ForeignKey(Quiz.id), nullable=False)
    started_on = Column(DateTime, nullable=False)
    finished_on = Column(DateTime, default=datetime.datetime.now(), nullable=False)


class AttemptAnswer(BaseModel):
    __tablename__ = 'attempt_answer'

    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey(Session.id), nullable=False)
    question_id = Column(Integer, ForeignKey(QuizQuestion.id), nullable=False)
    answer_id = Column(BigInteger, ForeignKey(QuestionAnswer.id), nullable=False)


class Group(BaseModel):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey(User.id), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(500))


class GroupMember(BaseModel):
    __tablename__ = 'group_member'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id), nullable=False)
    group_id = Column(Integer, ForeignKey(User.id), nullable=False)


BaseModel.metadata.create_all(db_engine)
