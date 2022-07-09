# Bot
import telebot.apihelper

from bot import *

# Telegram API
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler

# DB API
from sqlalchemy import and_, or_, between
from db.engine import db_session
from db.models.Attempt import Attempt
from db.models.AttemptAnswer import AttemptAnswer
from db.models.QuestionAnswer import QuestionAnswer
from db.models.Quiz import Quiz
from db.models.QuizQuestion import QuizQuestion
from db.models.Session import Session
from db.models.SessionAnswer import SessionAnswer
from db.models.User import User

# Misc.
from enum import Enum
from random import shuffle
from decimal import Decimal

# MPL
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
matplotlib.use('agg')

# Константи діалогу
class PQ(Enum):
    CHOOSE, START, NEXT = range(3)


def get_current_markup(user_id: int):
    with db_session.begin() as s:
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
                InlineKeyboardButton(f'{GOOD_SIGN if answers[ax].id in selection else BAD_SIGN} {answers[ax].answer}',
                                     callback_data=str(answers[ax].id))
            ])
        keyboard.append([InlineKeyboardButton('⇤', callback_data='start'),
                         InlineKeyboardButton('←', callback_data='prev'),
                         InlineKeyboardButton('✅', callback_data='finish'),
                         InlineKeyboardButton('→', callback_data='next'),
                         InlineKeyboardButton('⇥', callback_data='end'),
                         ])
        return InlineKeyboardMarkup(keyboard)


def get_search_data(user_id, term):
    markup = None
    with db_session.begin() as s:
        user = s.get(User, user_id)
        page = user.data['search']['page']
        result_query = s.query(Quiz).filter(
            and_(
                Quiz.is_available == True,
                or_(
                    and_(
                        Quiz.is_public == True,
                        Quiz.name.ilike(f'%{term}%')),
                    Quiz.token == term)))
        result_count = result_query.count()
        result = result_query.offset(user.data['search']['page'] * MAX_NUMBER).limit(MAX_NUMBER).all()
        message = f'За запитом "{term}" отримано результатів: {result_count} (натисніть для проходження тесту)'

        keyboard = []

        for x in result:
            keyboard.append([InlineKeyboardButton(x.name, callback_data=x.id)])

        if result_count == 0:
            message = f'За запитом "{term}" не знайдено жодних результатів 😢'
        else:
            keyboard.append([InlineKeyboardButton('🚪/ ⇤', callback_data='start'),
                             InlineKeyboardButton('←', callback_data='prev'),
                             InlineKeyboardButton(f'{page + 1} ({page * ITEMS_PER_PAGE + 1}-{page * ITEMS_PER_PAGE + len(result)}/{result_count})', callback_data='stay'),
                             InlineKeyboardButton('→', callback_data='next'),
                             InlineKeyboardButton('⇥', callback_data='end'),
                             ])
            markup = InlineKeyboardMarkup(keyboard)
        return message, markup


def get_answer_distribution(attempt_id: int):
    colors = []
    values = []

    with db_session.begin() as s:
        right_count = s.query(AttemptAnswer).filter(and_(
            AttemptAnswer.attempt_id == attempt_id,
            AttemptAnswer.mark == Decimal('1'))).count()
        partially_right_count = s.query(AttemptAnswer).filter(and_(
            AttemptAnswer.attempt_id == attempt_id,
            and_(AttemptAnswer.mark > Decimal('0'), AttemptAnswer.mark < Decimal('1')))).count()
        wrong_count = s.query(AttemptAnswer).filter(and_(
            AttemptAnswer.attempt_id == attempt_id,
            AttemptAnswer.mark == Decimal('0'))).count()

        if wrong_count != 0:
            values.append(wrong_count)
            colors.append('#FF0000')
        if partially_right_count != 0:
            values.append(partially_right_count)
            colors.append('#FF9900')
        if right_count != 0:
            values.append(right_count)
            colors.append('#00FF00')

        data = np.array([values])
        data_cum = data.cumsum(axis=1)

        fig, ax = plt.subplots(figsize=(50, 3))
        ax.invert_yaxis()
        ax.xaxis.set_visible(False)
        ax.set_xlim(0, np.sum(data, axis=1).max())

        for i, (color) in enumerate(colors):
            widths = data[:, i]
            starts = data_cum[:, i] - widths
            rects = ax.barh([''], widths, left=starts, height=0.5, color=color)

            ax.bar_label(rects, label_type='center', color='black', fontsize=100)

        out = io.BytesIO()
        FigureCanvas(fig).print_png(out)
        out.seek(0)
        return out


def update_question(send_message, user_id: int, action: str):
    with db_session.begin() as s:
        user = s.get(User, user_id)
        pass_ = user.data['pass']
        quiz_id = pass_['id']
        current_session = user.current_session

        match action:
            case 'start':
                if current_session.question_number == 0:
                    return True
                current_session.question_number = 0
            case 'prev':
                if current_session.question_number > 0:
                    current_session.question_number -= 1
                else:
                    return True
            case 'next':
                if current_session.question_number < user.data['pass']['question_count'] - 1:
                    current_session.question_number += 1
                else:
                    return True
            case 'finish':
                current_session.question_number += 1
            case 'end':
                if current_session.question_number == user.data['pass']['question_count'] - 1:
                    return True
                current_session.question_number = user.data['pass']['question_count'] - 1

        if len(pass_['selection']) != 0:
            session_answer = s.query(SessionAnswer).filter_by(session_id=current_session.id,
                                                              question_id=pass_['question_id']).one_or_none()
            if session_answer is None:
                __session_answer = SessionAnswer(current_session.id, pass_['question_id'], pass_['selection'])
                s.add(__session_answer)
            else:
                session_answer.answer_ids = pass_['selection'].copy()

            user.data['pass']['selection'].clear()

        question = s.query(QuizQuestion).filter_by(quiz_id=quiz_id).offset(current_session.question_number).first()
        if question is None:
            return False

        user.data['pass']['order'] = False
        pass_['question_id'] = question.id
        pass_['is_multi'] = question.is_multi
        next_session_answer = s.query(SessionAnswer).filter_by(session_id=current_session.id,
                                                               question_id=pass_['question_id']).one_or_none()
        pass_['selection'] = list(next_session_answer.answer_ids) if next_session_answer is not None else list()
        user.flag_data()

        text = f'Запитання {current_session.question_number + 1}. {question.question}\n' \
               f'{"(кілька вірних відповідей)" if question.is_multi else ""}'

    send_message(
        text=text,
        reply_markup=get_current_markup(user_id))
    return True


def session_to_attempt(user_id: int):
    with db_session.begin() as s:
        quiz_session = s.query(Session).filter_by(user_id=user_id).one_or_none()
        if quiz_session is None:
            return None
        attempt = Attempt.from_session(quiz_session)
        s.add(attempt)
        s.flush()
        attempt_id = attempt.id

        session_answers = s.query(SessionAnswer).filter_by(session_id=quiz_session.id).all()
        attempt_answers = []
        for ans in session_answers:
            attempt_answers.append(AttemptAnswer.from_session_answer(attempt_id, ans))
        s.add_all(attempt_answers)

        s.query(Session).filter_by(id=quiz_session.id).delete()
    return attempt_id


def start_quiz(upd: Update, ctx: CallbackContext, quiz: Quiz):
    if not quiz.is_available:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=f'Опитування "{quiz.name}" зараз відключено 😢.')
        return ConversationHandler.END
    with db_session.begin() as s:
        qcount = s.query(QuizQuestion).filter_by(quiz_id=quiz.id).count()
        user = s.get(User, upd.effective_user.id)
        user.set_data('pass', {
            'id': quiz.id,
            'question_id': 0,
            'selection': [],
            'order': False,
            'question_count': qcount
        })

        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=f'Опитування "{quiz.name}"',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('✅ Розпочати', callback_data='True'),
                InlineKeyboardButton('❌ Відміна', callback_data='False'),
            ]]))
    return PQ.START


def cmd_pass(upd: Update, ctx: CallbackContext):
    split = upd.message.text.split(' ')
    if len(split) != 2:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Щоб пройти опитування потрібно вказати його код:\n/pass Abc123dEF4')
        return ConversationHandler.END

    with db_session.begin() as s:
        quiz = s.query(Quiz).filter_by(token=split[1]).one_or_none()
        if quiz is None:
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text='Опитування не знайдено 😢. Можливо, ви помилилися у коді або автор опитування його змінив.')
            return ConversationHandler.END
        return start_quiz(upd, ctx, quiz)


def cmd_search(upd: Update, ctx: CallbackContext):
    split = upd.message.text.split(' ')
    if len(split) < 2:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Щоб знайти опитування потрібно вказати повністю або частково його назву (наприклад, /search '
                 'Опитування про довіру владі), також можна знайти опитування за його кодом (/search AbCD12G3hI).')
        return ConversationHandler.END

    term = ' '.join(split[1:])
    with db_session.begin() as s:
        # TODO: удосконалити пошук:
        # розбивати запит по пробілах і шукати всі збіги

        user = s.get(User, upd.effective_user.id)
        user.set_data('search', {
            'page': 0,
        })

    message, markup = get_search_data(upd.effective_user.id, term)
    ctx.bot.send_message(
        chat_id=upd.effective_chat.id,
        text=message,
        reply_markup=markup)
    return ConversationHandler.END if markup is None else PQ.CHOOSE


def cmd_show(upd: Update, ctx: CallbackContext):
    attempt_uuid = upd.message.text.split()[1]

    with db_session.begin() as s:
        attempt_id = s.query(Attempt.id).filter_by(uuid=attempt_uuid).scalar()
        if attempt_id is not None:
            attempt = s.get(Attempt, attempt_id)
            quiz = s.get(Quiz, attempt.quiz_id)
            tg_user = ctx.bot.get_chat(attempt.user_id)
            retry_number = s.query(Attempt).filter_by(user_id=attempt.user_id, quiz_id=attempt.quiz_id).count()
            ctx.bot.send_photo(
                upd.effective_chat.id,
                get_answer_distribution(attempt_id),
                f'Результати тестування:\n'
                f'Тег користувача: @{tg_user.username if tg_user.username is not None else "-"}\n'
                f'Повне ім\'я користувача: {tg_user.full_name}\n'
                f'Назва опитування: {quiz.name}\n'
                f'Код опитування: {quiz.token}\n'
                f'Час проходження: {(attempt.finished_on - attempt.started_on)}\n'
                f'Спроба №: {retry_number}\n'
                f'Оцінка: {attempt.mark}/100.00\n')


def conv_pq_next_question(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = eval(query.data)
    if not action:
        query.edit_message_text("Проходження опитування відмінено.")
        return ConversationHandler.END
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        quiz = s.get(Quiz, user.data['pass']['id'])

        quiz_session = Session(user.id, quiz.id)
        s.add(quiz_session)
    update_question(query.edit_message_text, upd.effective_user.id, 'next')
    query.answer()

    return PQ.NEXT


def answer_callback(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = query.data
    query.answer()
    if action.isnumeric():
        action = int(action)
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            is_multi = user.data['pass']['is_multi']
            selection = user.data['pass']['selection']
            if action in selection:
                selection.remove(action)
            else:
                if not is_multi:
                    selection.clear()
                selection.append(action)
            user.flag_data()
        query.edit_message_reply_markup(get_current_markup(upd.effective_user.id))
    else:
        user_id = upd.effective_user.id
        if not update_question(query.edit_message_text, user_id, action):
            with db_session.begin() as s:
                attempt_id = session_to_attempt(user_id)
                attempt = s.get(Attempt, attempt_id)
                quiz = s.get(Quiz, attempt.quiz_id)
                if not quiz.is_statistical:
                    retry_number = s.query(Attempt).filter_by(user_id=user_id, quiz_id=attempt.quiz_id).count()
                    query.edit_message_text(f'Обрахування результатів тестування...')
                    query.delete_message()
                    ctx.bot.send_photo(
                        upd.effective_chat.id,
                        get_answer_distribution(attempt_id),
                        f'Результати тестування:\n'
                        f'Унікальний код: {attempt.uuid}\n'
                        f'Назва: {quiz.name}\n'
                        f'Код опитування: {quiz.token}\n'
                        f'Час проходження: {(attempt.finished_on - attempt.started_on)}\n'
                        f'Спроба №: {retry_number}\n'
                        f'Оцінка: {attempt.mark}/100\n'
                        f'Переглянути цю спробу можна надіславши боту команду:\n'
                        f'/show {attempt.uuid}')
                else:
                    query.edit_message_text('Опитування пройдено, ваші відповіді успішно записано. Дякуємо за участь!')
            return ConversationHandler.END


def choose_callback(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = query.data
    query.answer()
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        match action:
            case 'stay':
                return
            case 'start':
                if user.data['search']['page'] == 0:
                    query.delete_message()
                    return ConversationHandler.END
                user.data['search']['page'] = 0
            case 'prev':
                if user.data['search']['page'] > 0:
                    user.data['search']['page'] -= 1
                else:
                    return
            case 'next':
                if user.data['search']['page'] < user.data['pass']['question_count'] - 1:
                    user.data['search']['page'] += 1
                else:
                    return
            case 'end':
                if user.data['search']['page'] == user.data['pass']['question_count'] - 1:
                    return
                user.data['search']['page'] = user.data['pass']['question_count'] - 1
            case _:
                if action.isnumeric():
                    action = int(action)
                    quiz = s.get(Quiz, action)
                    query.edit_message_text(f'Обрано тестування "{quiz.name}".')
                    return start_quiz(upd, ctx, quiz)
        user.flag_data()
    return PQ.CHOOSE


def conv_pq_cancel(upd: Update, ctx: CallbackContext):
    session_to_attempt(upd.effective_user.id)
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        user.remove_data('pass_quiz')
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Проходження опитування відмінено 😒')
    return ConversationHandler.END


dispatcher.add_handler(CommandHandler('show', cmd_show))


dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('pass', cmd_pass),
                  CommandHandler('search', cmd_search),
                  ],
    states={
        PQ.CHOOSE: [CallbackQueryHandler(choose_callback)],
        PQ.START: [CallbackQueryHandler(conv_pq_next_question), ],
        PQ.NEXT: [  # MessageHandler(Filters.text & ~Filters.command, conv_pq_next_question),
            CallbackQueryHandler(answer_callback),
        ],
    },
    fallbacks=[CommandHandler('cancel', conv_pq_cancel), ],
))
