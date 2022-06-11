import datetime

from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import Column, SmallInteger, Integer, BigInteger, Boolean, String, DateTime, ForeignKey, JSON,\
    UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY

from db.engine import db_engine, session

from utils import generate_token

BaseModel = declarative_base()


class User(BaseModel):
    __tablename__ = 'user'

    def __init__(self, user_id):
        self.id = user_id

    id = Column(BigInteger, autoincrement=False, primary_key=True)
    data = Column(JSON, default={})
    # quizzes = relationship("Quiz", cascade='all, delete, delete-orphan', passive_deletes=True)
    # session = relationship("Session", cascade='all, delete, delete-orphan', passive_deletes=True)
    # attempts = relationship("Attempt", cascade='all', passive_deletes=True)
    # groups = relationship("Group", cascade='all, delete, delete-orphan', passive_deletes=True)
    # member_of_groups = relationship("GroupMember", cascade='all, delete, delete-orphan', passive_deletes=True)

    def flag_data(self):
        flag_modified(self, 'data')

    def set_data(self, key, value):
        self.data[key] = value
        flag_modified(self, 'data')

    def remove_data(self, key):
        del self.data[key]
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
    author_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    # token = relationship("QuizToken", cascade='all, delete, delete-orphan', passive_deletes=True)
    # categories = relationship("QuizCategory", cascade='all, delete, delete-orphan', passive_deletes=True)
    # questions = relationship("QuizQuestion", cascade='all, delete, delete-orphan', passive_deletes=True)
    # sessions = relationship("Session", cascade='all, delete, delete-orphan', passive_deletes=True)
    # attempts = relationship("Attempt", cascade='all, delete, delete-orphan', passive_deletes=True)


class QuizToken(BaseModel):
    __tablename__ = 'quiz_token'

    def __init__(self, quiz_id):
        self.token = generate_token()
        self.quiz_id = quiz_id

    token = Column(String(10), primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)


class QuizCategoryType(BaseModel):
    __tablename__ = 'quiz_category_type'

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'<QuizCategoryType id: {self.id}, name: {self.name}>'

    id = Column(SmallInteger, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    # quizzes = relationship("QuizCategory", cascade='all, delete, delete-orphan', passive_deletes=True)


class QuizCategory(BaseModel):
    __tablename__ = 'quiz_category'

    def __init__(self, quiz_id, category_id):
        self.quiz_id = quiz_id
        self.category_id = category_id

    id = Column(BigInteger, primary_key=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
    category_id = Column(SmallInteger, ForeignKey(QuizCategoryType.id, ondelete='CASCADE'), nullable=False)
    UniqueConstraint(quiz_id, category_id, name='unique_cat')


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
    # answers = relationship("QuestionAnswer", cascade='all, delete, delete-orphan', passive_deletes=True)
    # session_answers = relationship("SessionAnswer", cascade='all, delete, delete-orphan', passive_deletes=True)
    # attempt_answers = relationship("AttemptAnswer", cascade='all, delete, delete-orphan', passive_deletes=True)


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
    # session_answers = relationship("SessionAnswer", cascade='all, delete, delete-orphan', passive_deletes=True)
    # attempt_answers = relationship("AttemptAnswer", cascade='all, delete, delete-orphan', passive_deletes=True)


class Session(BaseModel):
    __tablename__ = 'session'

    def __init__(self, user_id, quiz_id):
        self.user_id = user_id
        self.quiz_id = quiz_id

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
    started_on = Column(DateTime, default=datetime.datetime.now, nullable=False)
    question_number = Column(Integer, default=0, nullable=False)
    # answers = relationship("SessionAnswer", cascade='all, delete, delete-orphan', passive_deletes=True)


class SessionAnswer(BaseModel):
    __tablename__ = 'session_answer'

    def __init__(self, session_id, question_id, answer_ids: list):
        self.session_id = session_id
        self.question_id = question_id
        # TODO: чомусь не зберігаються айді
        self.answer_ids = answer_ids.copy()

    id = Column(BigInteger, primary_key=True)
    session_id = Column(BigInteger, ForeignKey(Session.id, ondelete='CASCADE'), nullable=False)
    question_id = Column(Integer, ForeignKey(QuizQuestion.id, ondelete='CASCADE'), nullable=False)
    answer_ids = Column(ARRAY(BigInteger, as_tuple=ForeignKey(QuestionAnswer.id, ondelete='CASCADE')), nullable=False)


class Attempt(BaseModel):
    __tablename__ = 'attempt'

    def __init__(self, user_id, quiz_id, started_on):
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.started_on = started_on

    @classmethod
    def from_session(cls, session: Session):
        return cls(session.user_id, session.quiz_id, session.started_on)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id, ondelete='SET NULL'), nullable=True)
    quiz_id = Column(Integer, ForeignKey(Quiz.id, ondelete='CASCADE'), nullable=False)
    started_on = Column(DateTime, nullable=False)
    finished_on = Column(DateTime, default=datetime.datetime.now, nullable=False)
    # answers = relationship("AttemptAnswer", cascade='all, delete, delete-orphan', passive_deletes=True)


class AttemptAnswer(BaseModel):
    __tablename__ = 'attempt_answer'

    def __init__(self, session_id, question_id, answer_ids: tuple):
        self.attempt_id = session_id
        self.question_id = question_id
        self.answer_ids = answer_ids

    @classmethod
    def from_session_answer(cls, session_answer: SessionAnswer):
        return cls(session_answer.session_id, session_answer.question_id, session_answer.answer_ids)

    def __repr__(self):
        return f'Id: {self.id}, attempt_id: {self.attempt_id}, question_id: {self.question_id}, ' \
               f'answer_ids: {self.answer_ids}'

    id = Column(BigInteger, primary_key=True)
    attempt_id = Column(BigInteger, ForeignKey(Attempt.id, ondelete='CASCADE'), nullable=False)
    question_id = Column(Integer, ForeignKey(QuizQuestion.id, ondelete='CASCADE'), nullable=False)
    answer_ids = Column(ARRAY(BigInteger, as_tuple=ForeignKey(QuestionAnswer.id)), nullable=False)


class Group(BaseModel):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(500))
    # members = relationship("GroupMember", cascade='all, delete, delete-orphan', passive_deletes=True)


class GroupMember(BaseModel):
    __tablename__ = 'group_member'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    group_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)


BaseModel.metadata.create_all(db_engine)
with session.begin() as __s:
    __s.query(Session).delete()
