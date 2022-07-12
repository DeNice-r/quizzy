import os
from dotenv import load_dotenv

# DB API
from sqlalchemy import create_engine as alch_create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy_utils import database_exists, create_database

load_dotenv()


def create_engine():
    return alch_create_engine(os.environ['DATABASE_URL'],  # echo=True,
                          future=True)


db_engine = create_engine()
db_session = sessionmaker(db_engine)
if not database_exists(db_engine.url):
    create_database(db_engine.url)
BaseModel = declarative_base()
