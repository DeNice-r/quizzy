# Bot
from bot import *

# Telegram API
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler

# DB API
from sqlalchemy.orm.attributes import flag_modified
from db.engine import session

# Misc.
from enum import Enum
from random import shuffle


# Константи бота
class PQ(Enum):
    START = 0
    NEXT = 1


def get_current_markup(user_id: int):
    with session.begin() as s:
        user = s.get(User, user_id)
        answers = s.query(QuestionAnswer).filter_by(question_id=user.data['pass']['question_id']).all()

        order = user.data['pass']['order']
        if not user.data['pass']['order']:
            user.data['pass']['order'] = [*range(len(answers))]
            order = user.data['pass']['order']
            shuffle(order)
            user.flag_data()

        selection = user.data['pass']['selection']
        keyboard = []
        for ax in order:
            keyboard.append([
                InlineKeyboardButton(f'{"♥" if answers[ax].id in selection else "🖤"} {answers[ax].answer}',
                                     callback_data=str(answers[ax].id))
            ])
        keyboard.append([InlineKeyboardButton('✅', callback_data='-1')])
        return InlineKeyboardMarkup(keyboard)


def send_next_question(chat_id: int, user_id: int, send_message):
    with session.begin() as s:
        user = s.get(User, user_id)
        pass_ = user.data['pass']
        quiz_id = pass_['id']
        quiz_session = s.query(Session).filter_by(user_id=user_id).one()

        if quiz_session.question_number != 0:
            session_answer = SessionAnswer(quiz_session.id, pass_['question_id'], pass_['selection'])
            s.add(session_answer)

            user.data['pass']['selection'].clear()
            user.data['pass']['order'] = False
            user.flag_data()

        question = s.query(QuizQuestion).filter_by(quiz_id=quiz_id).offset(quiz_session.question_number).first()
        if question is None:
            return False

        pass_['question_id'] = question.id
        pass_['multi'] = question.multi
        user.flag_data()

        quiz_session.question_number += 1

        text = f'Запитання {quiz_session.question_number}. {question.question}\n'
        f'{"(кілька вірних відповідей)" if question.multi else ""}'

    # TODO: переробити без відправки нових повідомлень
    send_message(chat_id=chat_id, text=text,
                 reply_markup=get_current_markup(user_id))
    return True


def session_to_attempt(user_id):
    with session.begin() as s:
        quiz_session = s.query(Session).filter_by(user_id=user_id).one()
        attempt = Attempt.from_session(quiz_session)
        s.add(attempt)
        s.flush()
        attempt_id = attempt.id

        # TODO: Не переносить відповіді
        session_answers = s.query(SessionAnswer).filter_by(session_id=quiz_session.id).all()
        attempt_answers = []
        for ans in session_answers:
            attempt_answers.append(AttemptAnswer.from_session_answer(ans))
        s.add_all(attempt_answers)

        quiz_session_id = quiz_session.id

    with session.begin() as s:
        s.query(Session).filter_by(id=quiz_session_id).delete()
    return attempt_id


def cmd_pass(upd: Update, ctx: CallbackContext):
    split = upd.message.text.split(' ')
    if len(split) != 2:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Щоб пройти опитування потрібно вказати його код:\n'
                                                                 '/pass Abc123dEF4')
        return

    with session.begin() as s:
        quiz_token = s.query(QuizToken).filter_by(token=split[1]).one_or_none()
        if quiz_token is None:
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text='Опитування не знайдено 😢. Можливо, ви помилилися у коді або автор опитування '
                                      'його змінив.')
            return

        quiz = s.get(Quiz, quiz_token.quiz_id)
        user = s.get(User, upd.effective_user.id)
        user.set_data('pass', {
            'id': quiz.id,
            'question_id': -1,
            'selection': [],
            'order': False,
        })

        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'Опитування "{quiz.name}". Щоб розпочати проходження надішліть /ready, для відміни '
                                  f'надішліть /cancel.')
    return PQ.START


def conv_pq_next_question(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        quiz = s.get(Quiz, user.data['pass']['id'])

        quiz_session = Session(user.id, quiz.id)
        s.add(quiz_session)
        s.commit()
    send_next_question(upd.effective_chat.id, upd.effective_user.id, ctx.bot.send_message)

    return PQ.NEXT


def answer_callback(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    action = int(query.data)
    if action == -1:
        user_id = upd.effective_user.id
        if not send_next_question(upd.effective_chat.id, user_id, ctx.bot.send_message):
            with session.begin() as s:
                attempt = s.get(Attempt, session_to_attempt(user_id))
                answers = s.query(AttemptAnswer).filter_by(attempt_id=attempt.id).all()
                print(answers)
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Результати тестування: {attempt.finished_on - attempt.started_on}')
            return ConversationHandler.END
    else:
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            multi = user.data['pass']['multi']
            selection = user.data['pass']['selection']
            if action in selection:
                selection.remove(action)
            else:
                if not multi:
                    selection.clear()
                selection.append(action)
            user.flag_data()
        query.edit_message_reply_markup(get_current_markup(upd.effective_user.id))


def conv_pq_cancel(upd: Update, ctx: CallbackContext):
    session_to_attempt(upd.effective_user.id)
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        user.remove_data('pass_quiz')
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Проходження опитування відмінено 😒')
    return ConversationHandler.END


# TODO: опитування у одному повідомленні із заміною наповнення
dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('pass', cmd_pass)],
    states={
        PQ.START: [CommandHandler('ready', conv_pq_next_question), ],
        PQ.NEXT: [  # MessageHandler(Filters.text & ~Filters.command, conv_pq_next_question),
                  CallbackQueryHandler(answer_callback),
                  ],
    },
    fallbacks=[CommandHandler('cancel', conv_pq_cancel), ]
))
