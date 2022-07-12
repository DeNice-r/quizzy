from sqlalchemy import Column, BigInteger, JSON
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.attributes import flag_modified

from db.engine import BaseModel


class User(BaseModel):
    __tablename__ = 'user'

    def __init__(self, user_id):
        self.id = user_id

    def flag_data(self):
        flag_modified(self, 'data')

    def set_data(self, key, value):
        self.data[key] = value
        flag_modified(self, 'data')

    def remove_data(self, key):
        del self.data[key]
        flag_modified(self, 'data')

    # May cause bugs therefore should not be used.
    # def clear_data(self):
    #     self.data.clear()
    #     flag_modified(self, 'data')

    @property
    def is_admin(self):
        print(self.admin)
        return self.admin is not None

    id = Column(BigInteger, autoincrement=False, primary_key=True)
    data = Column(JSON, default={})
    current_session = relationship('Session', backref=backref('user', lazy='select'), uselist=False,
                                   cascade='all, delete, delete-orphan')
    quizzes = relationship('Quiz', backref=backref('author', lazy='select'),
                           cascade='all, delete, delete-orphan')
    attempts = relationship('Attempt', backref=backref('user', lazy='select'),
                            cascade='all, delete, delete-orphan')
