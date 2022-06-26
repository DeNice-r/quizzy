# Ініціалізація всіх моделей (за потреби - створення відповідних таблиць у базі даних).
import logging

from sqlalchemy import text
import db.models.Attempt
import db.models.AttemptAnswer
import db.models.Group
import db.models.GroupMember
import db.models.QuestionAnswer
import db.models.Quiz
import db.models.QuizCategory
import db.models.QuizCategoryType
import db.models.QuizQuestion
import db.models.QuizToken
from db.models.Session import Session
import db.models.SessionAnswer
import db.models.User
from db.engine import db_engine, db_session, BaseModel

# Ініціалізація всіх модулів бота.
import src.cmd.new_quiz
import src.cmd.pass_
import src.cmd.my_quizzes
from bot import updater

if __name__ == '__main__':
    BaseModel.metadata.create_all(db_engine)
    with db_session.begin() as s:
        if s.query(Session).first() is not None:
            s.query(Session).delete()

        # s.execute(text("""SELECT pg_switch_wal();"""))

    # mock?
    try:
        with db_session.begin() as s:
            new_user = db.models.User.User(1)
            s.add(new_user)
    except:
        pass

    # TODO: create mock data


    updater.start_polling()
    updater.idle()
