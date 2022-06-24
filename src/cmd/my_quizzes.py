# Bot
from bot import *

# Telegram API
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, \
    Filters

# DB API
from db.engine import db_session
# Models
from db.models.Quiz import Quiz
from db.models.QuizQuestion import QuizQuestion
from db.models.QuizToken import QuizToken
from db.models.QuizCategory import QuizCategory
from db.models.QuizCategoryType import QuizCategoryType

# Misc.
from enum import Enum


class MQ(Enum):
    SHOW, EDIT, RENAME, EDIT_QUESTION, BACK_TO = range(5)


def get_all_quizzes_keyboard(user_id: int):
    # TODO: "ви ще не створити опитувань("
    # TODO: "cancel щоб вийти із цього меню" **
    with db_session.begin() as s:
        quizzes = s.query(Quiz).filter_by(author_id=user_id).all()
        keyboard = []
        for q_idx in range(0, len(quizzes), 2):
            keyboard.append([
                InlineKeyboardButton(quizzes[q_idx].name, callback_data=str(quizzes[q_idx].id)),
            ])
            if q_idx + 1 < len(quizzes):
                keyboard[-1].append(InlineKeyboardButton(quizzes[q_idx + 1].name, callback_data=str(quizzes[q_idx].id)))
    return InlineKeyboardMarkup(keyboard)


def get_edit_quiz_keyboard(quiz: Quiz):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Переіменувати', callback_data=f'{quiz.id}.rename'),
            InlineKeyboardButton('Публічне' if quiz.is_public else 'Приватне', callback_data=f'{quiz.id}.privacy'),
        ],
        [
            InlineKeyboardButton('Проглянути всі запитання', callback_data=f'{quiz.id}.show_questions'),
            InlineKeyboardButton('Змінити запитання', callback_data=f'{quiz.id}.edit_question'),
        ],
        [
            # TODO: регенерація токена
            # TODO: кнопка відображення статистики
        ],
        [
            InlineKeyboardButton('Видалити опитування', callback_data=f'{quiz.id}.delete'),
        ],
        [
            InlineKeyboardButton('🚪 Назад до списку опитувань', callback_data=f'{quiz.id}.back'),
        ]
    ])


def get_back_to_keyboard(user_id: int, quiz_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('🚪 Повернутися до опитування', callback_data=f'{quiz_id}.quiz')
        ],
        [
            InlineKeyboardButton('🚪 Повернутися до списку опитувань', callback_data=f'{user_id}.quiz_list'),
        ]
    ])


def get_quiz_info(quiz: Quiz | int):
    with db_session.begin() as s:
        if isinstance(quiz, int):
            quiz = s.get(Quiz, quiz)
        tok: QuizToken = s.query(QuizToken).filter_by(quiz_id=quiz.id).one()
        cats = [x[0] for x in s.query(QuizCategory, QuizCategoryType).with_entities(QuizCategoryType.name).
            filter(QuizCategoryType.id == QuizCategory.category_id, QuizCategory.quiz_id == quiz.id).all()]

        return f'Опитування "{quiz.name}"\n' \
               f'Токен для проходження: {tok.token}\n' \
               f'Категорії: {", ".join(cats)}\n'
        # TODO: to be continued...


def cmd_my_quizzes(upd: Update, ctx: CallbackContext):
    ctx.bot.send_message(chat_id=upd.effective_chat.id,
                         text=f'Оберіть опитування:',
                         reply_markup=get_all_quizzes_keyboard(upd.effective_user.id))
    return MQ.SHOW


def quiz_menu(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    action = int(query.data.split('.')[0])
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        quiz = s.get(Quiz, action)
        query.edit_message_text(
            text=get_quiz_info(quiz),
            reply_markup=get_edit_quiz_keyboard(quiz))
    return MQ.EDIT


def quiz_edit(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action_split = query.data.split('.')
    action_split[0] = int(action_split[0])
    query.answer()
    match action_split:
        case quiz_id, 'rename':
            with db_session.begin() as s:
                user = s.get(User, upd.effective_user.id)
                user.set_data('rename_quiz_id', quiz_id)

            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=f'Введіть нову назву для свого опитування:')
            return MQ.RENAME

        case quiz_id, 'privacy':
            with db_session.begin() as s:
                quiz = s.get(Quiz, quiz_id)
                quiz.is_public = not quiz.is_public
                s.flush()
                query.edit_message_reply_markup(get_edit_quiz_keyboard(quiz))
            return MQ.EDIT

        case quiz_id, 'show_questions':
            raise NotImplemented
        case quiz_id, 'regenerate_token':
            raise NotImplemented
        case quiz_id, 'show_stats':
            raise NotImplemented
        case quiz_id, 'edit_question':
            qs = 'Запитання у цьому опитуванні:\n'
            with db_session.begin() as s:
                questions = s.query(QuizQuestion).filter_by(quiz_id=quiz_id).all()
                for q_idx in range(len(questions)):
                    qs += f'{q_idx + 1}. {questions[q_idx].question}\n'
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=qs)
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=f'Введіть номер запитання, яке хочете змінити:')
            return MQ.EDIT_QUESTION

        case quiz_id, 'delete':
            # TODO: are you sure?
            raise NotImplemented

        case quiz_id, 'back':
            query.edit_message_text(get_quiz_info(quiz_id),
                                    reply_markup=get_all_quizzes_keyboard(upd.effective_user.id))
            return MQ.SHOW


def rename(upd: Update, ctx: CallbackContext):
    name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(name):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            quiz = s.get(Quiz, user.data['rename_quiz_id'])
            quiz.name = name

            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=f'Назву успішно змінено!',
                reply_markup=get_back_to_keyboard(user.id, quiz.id))

        return MQ.BACK_TO
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text="Повідомлення містить недопустимі символи або занадто довге :(")
    return MQ.RENAME


def edit_question(upd: Update, ctx: CallbackContext):
    raise NotImplemented


def back_to(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action_split = query.data.split('.')
    action_split[0] = int(action_split[0])
    query.answer()
    match action_split:
        case quiz_id, 'quiz':
            with db_session.begin() as s:
                quiz = s.get(Quiz, quiz_id)
                query.edit_message_text(get_quiz_info(quiz),
                                        reply_markup=get_edit_quiz_keyboard(quiz))
            return MQ.EDIT
        case user_id, 'quiz_list':
            query.edit_message_text('Оберіть опитування:',
                                    reply_markup=get_all_quizzes_keyboard(user_id))
            return MQ.SHOW


dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('my_quizzes', cmd_my_quizzes)],
    states={
        MQ.SHOW: [
            CallbackQueryHandler(quiz_menu),
        ],
        MQ.EDIT: [
            CallbackQueryHandler(quiz_edit),
        ],
        MQ.RENAME: [
            MessageHandler(Filters.text, rename)
        ],
        MQ.EDIT_QUESTION: [
            MessageHandler(Filters.text, edit_question)
        ],
        MQ.BACK_TO: [
            CallbackQueryHandler(back_to),
        ]
    },
    fallbacks=[CommandHandler('cancel', lambda *args: ConversationHandler.END), ]
))
