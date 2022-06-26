from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from db.models.Attempt import Attempt
# from db.models.AttemptAnswer import AttemptAnswer
# from db.models.Group import Group
# from db.models.GroupMember import GroupMember
# from db.models.QuestionAnswer import QuestionAnswer
# from db.models.Quiz import Quiz
# from db.models.QuizCategory import QuizCategory
# from db.models.QuizCategoryType import QuizCategoryType
# from db.models.QuizQuestion import QuizQuestion
# from db.models.QuizToken import QuizToken
# from db.models.Session import Session
# from db.models.SessionAnswer import SessionAnswer
# from db.models.User import User
# target_metadata = [Attempt.Base.metadata, AttemptAnswer.Base.metadata,
#                    Group.Base.metadata, GroupMember.Base.metadata,
#                    QuestionAnswer.Base.metadata, Quiz.Base.metadata,
#                    QuizCategory.Base.metadata, QuizCategoryType.Base.metadata,
#                    QuizQuestion.Base.metadata, QuizToken.Base.metadata,
#                    Session.Base.metadata, SessionAnswer.Base.metadata,
#                    User.Base.metadata,
#                    ]

import sys
from os.path import dirname, abspath
sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from run import BaseModel
target_metadata = BaseModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
