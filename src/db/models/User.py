from sqlalchemy import Column, BigInteger, JSON
from sqlalchemy.orm.attributes import flag_modified

from db.engine import BaseModel


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

    def remove_data(self, key):
        del self.data[key]
        flag_modified(self, 'data')

    def clear_data(self):
        self.data.clear()
        flag_modified(self, 'data')