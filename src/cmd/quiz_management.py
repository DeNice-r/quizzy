# Bot
import math
import secrets
from idlelib.query import Query
from random import choice

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
from db.models.QuizCategory import QuizCategory
from db.models.QuizCategoryType import QuizCategoryType
from db.models.Attempt import Attempt
from db.models.Session import Session
from db.models.QuestionAnswer import QuestionAnswer


# Plotting API
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
matplotlib.use('agg')

# Misc.
from enum import Enum


class MQ(Enum):
    SHOW, EDIT, RENAME, QUESTION_MODE, QUESTION_EDIT, QUESTION_EDIT_MODE, ANSWER_MODE, ANSWER_EDIT_MODE, ANSWER_DELETE,\
        ANSWER_EDIT, QUE_IS_MULTI, QUE_ANS_RIGHT, QUE_ANS, ADD_ANS, STATS, QUESTION_DELETE, DELETE, CAT_MODE, \
        BACK_TO = range(19)


def get_all_quizzes_keyboard(user_id: int):
    with db_session.begin() as s:
        user = s.get(User, user_id)
        page = user.data['my_quizzes']['page']
        quizzes = s.query(Quiz.name, Quiz.id).filter_by(author_id=user_id).offset(page * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()
        quiz_count = s.query(Quiz).filter_by(author_id=user_id).count()

        keyboard = []
        for quiz in quizzes:
            keyboard.append([
                InlineKeyboardButton(quiz[0], callback_data=str(quiz[1])),
            ])
        keyboard.append([InlineKeyboardButton('🚪/ ⇤', callback_data='start'),
                         InlineKeyboardButton('←', callback_data='prev'),
                         InlineKeyboardButton(
                             f'{page + 1} ({page * ITEMS_PER_PAGE + 1}-{page * ITEMS_PER_PAGE + len(quizzes)}/{quiz_count})',
                             callback_data='stay'),
                         InlineKeyboardButton('→', callback_data='next'),
                         InlineKeyboardButton('⇥', callback_data='end'),
                         ])
    return InlineKeyboardMarkup(keyboard)


def get_edit_quiz_keyboard(quiz: Quiz | int):
    with db_session.begin() as s:
        if isinstance(quiz, int):
            quiz = s.get(Quiz, quiz)
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton('Переіменувати', callback_data=f'{quiz.id}.rename'),
                InlineKeyboardButton('Відредагувати категорії', callback_data=f'{quiz.id}.cat_mode'),
            ],
            [
                InlineKeyboardButton('Публічне' if quiz.is_public else 'Приватне', callback_data=f'{quiz.id}.privacy'),
                InlineKeyboardButton('Активоване' if quiz.is_available else 'Деактивоване',
                                     callback_data=f'{quiz.id}.availability'),
            ],
            [
                InlineKeyboardButton('Новий токен', callback_data=f'{quiz.id}.regenerate_token'),
                InlineKeyboardButton('Проглянути статистику', callback_data=f'{quiz.id}.show_stats'),
            ],
            [
                InlineKeyboardButton('Відредагувати запитання', callback_data=f'{quiz.id}.question_mode'),
            ],
            [
                InlineKeyboardButton('Видалити опитування', callback_data=f'{quiz.id}.delete'),
            ],
            [
                InlineKeyboardButton('🚪 Назад до списку опитувань', callback_data=f'{quiz.id}.quiz_list'),
            ],
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


def get_cat_keyboard(quiz_id: int, cat_id_to_remove: int = None):
    keyboard = []
    with db_session.begin() as s:
        quiz = s.get(Quiz, quiz_id)
        if cat_id_to_remove is not None:
            cat = s.get(QuizCategory, cat_id_to_remove)
            s.delete(cat)
            s.flush()
        cats = s.query(QuizCategory).filter_by(quiz_id=quiz_id).all()
        for x in range(len(cats)):
            keyboard.append([InlineKeyboardButton(quiz.categories[x], callback_data=str(cats[x].id))])
        keyboard.append([InlineKeyboardButton('🚪 Назад', callback_data='quiz')])
        return InlineKeyboardMarkup(keyboard)


def get_question_mode_keyboard(user: User | int):
    keyboard = []
    with db_session.begin() as s:
        if isinstance(user, int):
            user = s.get(User, user)

        quiz_id = user.data['quiz_mode']['quiz_id']
        page = user.data['question_mode']['page']
        question_query = s.query(QuizQuestion).filter_by(quiz_id=quiz_id)
        questions = question_query.offset(page * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()
        question_num = question_query.count()
        for que in questions:
            keyboard.append([InlineKeyboardButton(que.question, callback_data=que.id)])

        keyboard.append([InlineKeyboardButton('🚪/ ⇤', callback_data='start'),
                         InlineKeyboardButton('←', callback_data='prev'),
                         InlineKeyboardButton(
                             f'{page + 1} ({page * ITEMS_PER_PAGE + 1}-{page * ITEMS_PER_PAGE + len(questions)}/{question_num})',
                             callback_data='stay'),
                         InlineKeyboardButton('→', callback_data='next'),
                         InlineKeyboardButton('⇥', callback_data='end'),
                         ])

    return InlineKeyboardMarkup(keyboard)


def get_question_edit_mode_keyboard(question_id: int):
    keyboard = [[
            InlineKeyboardButton('Змінити запитання', callback_data=f'{question_id}.edit')
        ],
        [
            InlineKeyboardButton('Відредагувати відповіді', callback_data=f'{question_id}.answer_mode')
        ],
        [
            InlineKeyboardButton('Видалити запитання', callback_data=f'{question_id}.delete')
        ],
        [
            InlineKeyboardButton('🚪 Назад до списку запитань', callback_data=f'{question_id}.question_edit_mode')
        ], ]
    return InlineKeyboardMarkup(keyboard)


def get_question_answer_mode_keyboard(question: QuizQuestion | int):
    keyboard = []
    with db_session.begin() as s:
        if isinstance(question, int):
            question = s.get(QuizQuestion, question)
        for answer in question.answers:
            keyboard.append([
                InlineKeyboardButton((GOOD_SIGN if answer.is_right else BAD_SIGN) + ' ' + answer.answer)
            ])
        keyboard.append([
            InlineKeyboardButton('🚪 Назад до запитання', callback_data=f'back')])
        return InlineKeyboardMarkup(keyboard)


def get_answer_keyboard(question: QuizQuestion | int):
    keyboard = []
    with db_session.begin() as s:
        if isinstance(question, int):
            question = s.get(QuizQuestion, question)
        for answer in question.answers:
            keyboard.append([InlineKeyboardButton((GOOD_SIGN if answer.is_right else BAD_SIGN) + ' ' + answer.answer,
                                                  callback_data=answer.id)])
        keyboard.append([InlineKeyboardButton('🚪 Назад',
                        callback_data='question_edit_mode')]
        )
        return InlineKeyboardMarkup(keyboard)


def get_exact_answer_keyboard(answer: QuestionAnswer | int):
    # TODO: передбачити відсутність відповідей (видаляти запитання чи не давати видалити останні 2 відповіді?***
    with db_session.begin() as s:
        if isinstance(answer, int):
            answer = s.get(QuestionAnswer, answer)
        keyboard = [
            [
                InlineKeyboardButton('Змінити відповідь', callback_data=f'{answer.id}.edit'),
            ],
            [
                InlineKeyboardButton('Вірна' if answer.is_right else 'Не вірна', callback_data=f'{answer.id}.right'),
            ],
            [
                InlineKeyboardButton('Видалити', callback_data=f'{answer.id}.delete'),
            ],
            [
                InlineKeyboardButton('Назад', callback_data=f'{answer.id}.answer_edit_mode'),
            ]]
        return InlineKeyboardMarkup(keyboard)


def get_stats_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Статистика відповідей', 'answers'),
        ],
        [
            InlineKeyboardButton('Статистика відповідей'),
        ],
        [
            InlineKeyboardButton('🚪 Назад'),
            # send_statistics(upd, ctx, quiz_id)
        ],

    ])


def get_quiz_info(quiz: Quiz | int):
    with db_session.begin() as s:
        if isinstance(quiz, int):
            quiz = s.get(Quiz, quiz)
        cats = [x[0] for x in s.query(QuizCategory, QuizCategoryType).with_entities(QuizCategoryType.name).
            filter(QuizCategoryType.id == QuizCategory.category_id, QuizCategory.quiz_id == quiz.id).all()]
        attempt_count = s.query(Attempt).filter_by(quiz_id=quiz.id).count()
        session_count = s.query(Session).filter_by(quiz_id=quiz.id).count()

        return f'Опитування "{quiz.name}"\n' \
               f'Токен для проходження: {quiz.token}\n' \
               f'Кількість проходжень: {attempt_count}' \
               f'{f" (і ще {session_count} проходять прямо зараз)" if session_count > 0 else ""}\n' \
               f'Категорії: {", ".join(quiz.categories)}\n'
        # TODO: to be continued...


def send_statistics(upd, ctx, quiz_id):
    images = []
    with db_session.begin() as s:
        titles = [x[0] for x in s.query(QuizQuestion.question).filter_by(quiz_id=quiz_id).all()]
        question_ids = s.query(QuizQuestion.id).filter_by(quiz_id=quiz_id).all()

        for que_id_index in range(len(question_ids)):
            que_id = question_ids[que_id_index][0]
            title = titles[que_id_index]
            labels = [x[0] for x in s.query(QuestionAnswer.answer).filter_by(question_id=que_id).all()]
            answer_ids = [x[0] for x in s.query(QuestionAnswer.id).filter_by(question_id=que_id).all()]
            stmt = text(
                "SELECT question_answer.answer, COUNT(question_answer.id) \n"
                "FROM question_answer \n"
                "INNER JOIN attempt_answer aa on question_answer.id=ANY(aa.answer_ids) \n"
                "WHERE question_answer.id = ANY(:ans_ids) \n"
                "GROUP BY question_answer.id \n")

            counts = s.execute(stmt, {'ans_ids': answer_ids}).all()
            if len(counts) < 1:
                continue

            local_palette = palette[:len(counts)]
            while len(local_palette) > len(counts):
                local_palette.extend(palette[:len(counts) - len(local_palette)])

            fig, ax = plt.subplots()
            ax.pie([x[1] for x in counts],
                   labels=[(x[0] if len(x[0]) < 30 else x[0][:27] + '...') for x in counts],
                   radius=5,
                   center=(10, 10),
                   autopct='%1.1f%%',
                   explode=[.08 for x in range(len(counts))],
                   colors=local_palette,
                   # wedgeprops={"linewidth": 1, "edgecolor": "white"},
                   shadow=True)
            ax.axis('equal')
            plt.text(-2.3, 16.5, str(que_id_index + 1) + '. ' + (title if len(title) < 50 else title[:47] + '...'), fontsize=18, fontweight='bold')
            # plt.tight_layout()
            fig.set_size_inches(12, 7)
            out = io.BytesIO()
            FigureCanvas(fig).print_png(out)
            out.seek(0)
            images.append(InputMediaPhoto(out))
    if len(images) > 1:
        while len(images) > 1:
            ctx.bot.send_media_group(upd.effective_chat.id, images[:10])
            images = images[10:]
    if len(images) == 1:
        ctx.bot.send_photo(upd.effective_chat.id, images[0].media)


def cmd_my_quizzes(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        user.set_data('my_quizzes', {
            'page': 0,
        })
    ctx.bot.send_message(chat_id=upd.effective_chat.id,
                         text=f'Оберіть опитування:',
                         reply_markup=get_all_quizzes_keyboard(upd.effective_user.id))

    return MQ.SHOW


def quiz_menu(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    action = query.data
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        page = user.data['my_quizzes']['page']
        page_count = math.ceil(s.query(Quiz).filter_by(author_id=user.id).count() / ITEMS_PER_PAGE)
        match action:
            case 'stay':
                return
            case 'start':
                if page == 0:
                    quiz = s.get(Quiz, user.data['quiz_mode']['quiz_id'])
                    query.delete_message()
                    return ConversationHandler.END
                user.data['question_mode']['page'] = 0
            case 'prev':
                if page > 0:
                    user.data['question_mode']['page'] -= 1
                else:
                    return
            case 'next':
                if page < page_count - 1:
                    user.data['question_mode']['page'] += 1
                else:
                    return
            case 'end':
                if page == page_count - 1:
                    return
                user.data['question_mode']['page'] += 1
            case _:
                if action.isnumeric():
                    quiz = s.get(Quiz, action)
                    user.set_data('quiz_mode', {
                        'quiz_id': quiz.id,
                        'message_id': query.message.message_id,
                    })
                    query.edit_message_text(
                        text=get_quiz_info(quiz),
                        reply_markup=get_edit_quiz_keyboard(quiz))
        user.flag_data()
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

            query.edit_message_text(
                text=f'Введіть нову назву для свого опитування:',
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton('Назад', callback_data=f'{quiz_id}.quiz')]]))
            return MQ.RENAME
        case quiz_id, 'privacy':
            with db_session.begin() as s:
                quiz = s.get(Quiz, quiz_id)
                quiz.is_public = not quiz.is_public
                s.flush()
                query.edit_message_reply_markup(get_edit_quiz_keyboard(quiz))
            return MQ.EDIT
        case quiz_id, 'availability':
            with db_session.begin() as s:
                quiz = s.get(Quiz, quiz_id)
                quiz.is_available = not quiz.is_available
                s.flush()
                query.edit_message_reply_markup(get_edit_quiz_keyboard(quiz))
            return MQ.EDIT
        case quiz_id, 'cat_mode':
            query.edit_message_text('Режим редагування категорій. Надішліть назву категорії щоб її додати або '
                                    'натисніть на категорію під цим повідомленням щоб її видалити.',
                                    reply_markup=get_cat_keyboard(quiz_id))
            with db_session.begin() as s:
                user = s.get(User, upd.effective_user.id)
            return MQ.CAT_MODE
        # case quiz_id, 'show_questions': with db_session.begin() as s: quiz = s.get(Quiz, quiz_id)
        # ctx.bot.send_message( chat_id=upd.effective_chat.id, text=str('\n\n'.join([f'{x + 1}. ' + str(
        # quiz.questions[x]) for x in range(len(quiz.questions))])))
        case quiz_id, 'regenerate_token':
            with db_session.begin() as s:
                quiz = s.query(Quiz).filter_by(quiz_id=quiz_id).one_or_none()
                quiz.regenerate_token()
            query.edit_message_text(get_quiz_info(quiz_id), reply_markup=get_edit_quiz_keyboard(quiz_id))
            return MQ.EDIT
        case quiz_id, 'show_stats':
            raise NotImplemented
            query.edit_message_text('Оберіть тип статистики, яку хочете переглянути:',
                                    reply_markup=get_stats_keyboard(quiz_id))
            send_statistics(upd, ctx, quiz_id)

            return MQ.STATS
        case quiz_id, 'question_mode':
            with db_session.begin() as s:
                user = s.get(User, upd.effective_user.id)
                user.set_data('question_mode', {
                    'page': 0,
                })
            query.edit_message_text('Оберіть запитання, яке хочете змінити або введіть нове, щоб почати створення '
                                    'нового запитання:',
                                    reply_markup=get_question_mode_keyboard(upd.effective_user.id))
            return MQ.QUESTION_MODE
        case quiz_id, 'delete':
            with db_session.begin() as s:
                quiz = s.get(Quiz, quiz_id)
                query.edit_message_text(f'Ви впевнені, що хочете видалити опитування "{quiz.name}"?',
                                        reply_markup=InlineKeyboardMarkup(
                                            [[InlineKeyboardButton('Так', callback_data=f'{quiz_id}.yes'),
                                              InlineKeyboardButton('Ні', callback_data=f'{quiz_id}.no')]]))
                return MQ.DELETE
        case quiz_id, 'quiz_list':
            query.edit_message_text('Оберіть опитування:',
                                    reply_markup=get_all_quizzes_keyboard(upd.effective_user.id))
            return MQ.SHOW


def rename(upd: Update, ctx: CallbackContext):
    name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(name):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            quiz = s.get(Quiz, user.data['rename_quiz_id'])
            quiz.name = name

            msg = ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=f'Назву успішно змінено!',
                reply_markup=get_back_to_keyboard(user.id, quiz.id))
            user.data['quiz_mode']['message_id'] = msg.message_id
            user.flag_data()
        return MQ.BACK_TO
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text="Повідомлення містить недопустимі символи або занадто довге :(")
    return MQ.RENAME


def question_mode(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = query.data
    query.answer()
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        page = user.data['question_mode']['page']
        page_count = math.ceil(s.query(QuizQuestion).filter_by(quiz_id=user.data['quiz_mode']['quiz_id']).count() / ITEMS_PER_PAGE)
        match action:
            case 'stay':
                return
            case 'start':
                if page == 0:
                    quiz = s.get(Quiz, user.data['quiz_mode']['quiz_id'])
                    query.edit_message_text(get_quiz_info(quiz),
                                            reply_markup=get_edit_quiz_keyboard(quiz))
                    return MQ.EDIT
                user.data['question_mode']['page'] = 0
            case 'prev':
                if page > 0:
                    user.data['question_mode']['page'] -= 1
                else:
                    return
            case 'next':
                if page < page_count - 1:
                    user.data['question_mode']['page'] += 1
                else:
                    return
            case 'end':
                if page == page_count - 1:
                    return
                user.data['question_mode']['page'] += 1
            case _:
                if action.isnumeric():
                    user.data['question_mode']['question_id'] = int(action)
                    user.flag_data()
                    question: QuizQuestion = s.get(QuizQuestion, int(action))
                    query.edit_message_text(f'Запитання: {question.question}',  # \nВаріанти відповідей:',
                                            reply_markup=get_question_edit_mode_keyboard(question.id))
                    return MQ.QUESTION_EDIT_MODE
        user.flag_data()
        query.edit_message_text('Оберіть запитання, яке хочете змінити:',
                                reply_markup=get_question_mode_keyboard(upd.effective_user.id))
        return MQ.QUESTION_MODE


def question_edit_mode(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action_split = query.data.split('.')
    with db_session.begin() as s:
        user: User = s.get(User, upd.effective_user.id)
        match action_split:
            case question_id, 'edit':
                query.edit_message_text('Введіть змінене запитання або натисніть кнопку під цим повідомленням для '
                                        'відміни:',
                                        reply_markup=InlineKeyboardMarkup(
                                            [[InlineKeyboardButton('Назад', callback_data=f'{question_id}.question_edit_mode')]]))
                return MQ.QUESTION_EDIT
            case question_id, 'answer_mode':
                question: QuizQuestion = s.get(QuizQuestion, question_id)
                is_statistical = s.get(Quiz, question.quiz_id).is_statistical
                query.edit_message_text(
                    f'Оберіть відповідь для редагування (' + (
                        f"повинно бути кілька {'' if is_statistical else 'вірних '}відповідей" if question.is_multi else f"повинна бути лише одна {'' if is_statistical else 'вірна '}відповідь") + '):',
                    reply_markup=get_answer_keyboard(question)
                )
                return MQ.ANSWER_EDIT_MODE
            case question_id, 'delete':
                question: QuizQuestion = s.get(QuizQuestion, question_id)
                query.edit_message_text(
                    f'Ви впевнені, що хочете видалити запитання "{question.question}" із '
                    f'наступними відповідями?:\n' +
                    '\n'.join([(GOOD_SIGN if x.is_right else BAD_SIGN) + ' ' + x.answer for x in question.answers]),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton('Так', callback_data=f'{question_id}.yes'),
                          InlineKeyboardButton('Ні', callback_data=f'{question_id}.no')]]))
                return MQ.QUESTION_DELETE
            case question_id, 'question_edit_mode':
                query.edit_message_text('Оберіть запитання, яке хочете змінити:',
                                        reply_markup=get_question_mode_keyboard(upd.effective_user.id))
                return MQ.QUESTION_MODE
    query.answer()


def question_edit(upd: Update, ctx: CallbackContext):
    question_text = upd.message.text
    if RE_MED_TEXT.fullmatch(question_text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            question = s.get(QuizQuestion, user.data['question_mode']['question_id'])
            question.question = question_text
            msg = ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text="Запитання успішно змінено!",
                reply_markup=InlineKeyboardMarkup(
                             [[InlineKeyboardButton('Назад', callback_data=f'{question.id}.question_edit_mode')]]))
            user.data['quiz_mode']['message_id'] = msg.message_id
            user.flag_data()
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")


# def question_edit_back(upd: Update, ctx: CallbackContext):
#     query = upd.callback_query
#     query.answer()
#     with db_session.begin() as s:
#         question: QuizQuestion = s.get(QuizQuestion, int(query.data.split('.')[0]))
#         query.edit_message_text(f'Запитання: {question.question}\nВаріанти відповідей:',
#                                 reply_markup=get_question_edit_mode_keyboard(question))
#     return MQ.QUESTION_EDIT_MODE


def answer_mode(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action_split = query.data.split('.')
    # action_split[0] = int(action_split[0])  # TODO: is it really needed? *** (remove everywhere if it is not)
    query.answer()
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        match action_split:
            case answer_id, 'edit':
                query.edit_message_text('Введіть змінену відповідь або натисніть кнопку під цим повідомленням для '
                                        'відміни:',
                                        reply_markup=InlineKeyboardMarkup(
                                            [[InlineKeyboardButton('Назад', callback_data=f'{answer_id}.answer_edit_mode')]]))
                return MQ.ANSWER_EDIT
            case answer_id, 'right':
                answer = s.get(QuestionAnswer, answer_id)
                answer.is_right = not answer.is_right
                query.edit_message_text(f'Відповідь: {answer.answer}', reply_markup=get_exact_answer_keyboard(answer))
                return MQ.ANSWER_MODE
            case answer_id, 'delete':
                answer: QuestionAnswer = s.get(QuestionAnswer, answer_id)
                query.edit_message_text(
                    f'Ви впевнені, що хочете видалити відповідь '
                    f'"{GOOD_SIGN if answer.is_right else BAD_SIGN} {answer.answer}"?\n',
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton('Так', callback_data=f'{answer_id}.yes'),
                          InlineKeyboardButton('Ні', callback_data=f'{answer_id}.no')]]))
                return MQ.ANSWER_DELETE
            case answer_id, 'answer_edit_mode':
                question: QuizQuestion = s.get(QuizQuestion, user.data['question_mode']['question_id'])
                is_statistical = s.get(Quiz, question.quiz_id).is_statistical
                query.edit_message_text(
                    f'Оберіть відповідь для редагування (' + (
                        f"повинно бути кілька {'' if is_statistical else 'вірних '}відповідей" if question.is_multi else f"повинна бути лише одна {'' if is_statistical else 'вірна '}відповідь") + '):',
                    reply_markup=get_answer_keyboard(question)
                )
                return MQ.ANSWER_EDIT_MODE
    return MQ.ANSWER_MODE


def answer_edit_mode(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = query.data
    query.answer()
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        if action == 'question_edit_mode':
            question = s.get(QuizQuestion, user.data['question_mode']['question_id'])
            query.edit_message_text(f'Запитання: {question.question}',
                                    reply_markup=get_question_edit_mode_keyboard(question.id))
            return MQ.QUESTION_EDIT_MODE
        elif action.isnumeric():
            answer = s.get(QuestionAnswer, action)
            user.data['question_mode']['answer_id'] = int(action)
            user.flag_data()
            query.edit_message_text(f'Відповідь: {answer.answer}',
                                    reply_markup=get_exact_answer_keyboard(answer))
            return MQ.ANSWER_MODE


def answer_edit(upd: Update, ctx: CallbackContext):
    answer_text = upd.message.text
    if RE_MED_TEXT.fullmatch(answer_text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            answer = s.get(QuestionAnswer, user.data['question_mode']['answer_id'])
            answer.answer = answer_text
            msg = ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text="Відповідь успішно змінено!",
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton('Назад', callback_data=f'{answer.id}.answer_edit_mode')]]))
            user.data['quiz_mode']['message_id'] = msg.message_id
            user.flag_data()
            return MQ.BACK_TO
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")


# def answer_edit_back(upd: Update, ctx: CallbackContext):
#     query = upd.callback_query
#     query.answer()
#     with db_session.begin() as s:
#         question: QuizQuestion = s.get(QuizQuestion, int(query.data.split('.')[0]))
#         query.edit_message_text(f'Запитання: {question.question}\nВаріанти відповідей:',
#                                 reply_markup=get_question_edit_mode_keyboard(question))
#     return MQ.QUESTION_EDIT_MODE


def answer_delete(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action_split = query.data.split('.')
    msg = "Відповідь успішно видалено!"
    ret_value = MQ.ANSWER_MODE
    match action_split:
        case answer_id, 'yes':
            with db_session.begin() as s:
                answer = s.get(QuestionAnswer, answer_id)
                s.delete(answer)
        case answer_id, 'no':
            msg = "Видалення відповіді відмінено 🎉"
            ret_value = MQ.BACK_TO
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('🚪 Повернутися до списку відповідей',
                                 callback_data=f'{user.data["quiz_mode"]["quiz_id"]}.answer_edit_mode')
        ]]))
    query.answer()
    return ret_value


def add_question(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.set_data('new_question', {
                'question': upd.message.text,
                'right_answers': [],
                'wrong_answers': [],
                'is_multi': False,
            })
            user.flag_data()
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text=f'{choice(["Чудове", "Гарне", "Класне"])} запитання! Тепер оберіть тип запитання по кількості '
                 'відповідей (неможливо змінити):',
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Одна відповідь', callback_data='False')],
                 [InlineKeyboardButton('Кілька відповідей', callback_data='True')]]))
        return MQ.QUE_IS_MULTI
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
        return MQ.QUESTION_MODE


def add_question_is_multi(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    is_multi = eval(query.data)
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        user.data['new_question']['is_multi'] = is_multi
        user.flag_data()
        is_stat = s.get(Quiz, user.data['quiz_mode']['quiz_id']).is_statistical
        txt = f'Обрано тип запитання: {"кілька відповідей" if is_multi else "одна відповідь"}.\nТепер '
        if is_stat:
            if is_multi:
                txt += 'надсилайте відповіді'
            else:
                txt += 'надішліть відповідь'
        elif is_multi:
            txt += 'надсилайте вірні відповіді'
        else:
            txt += 'надішліть вірну відповідь'

        query.edit_message_text(txt + ':')
    return MQ.QUE_ANS_RIGHT


def add_question_right_ans(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            is_stat = s.get(Quiz, user.data['quiz_mode']['quiz_id']).is_statistical
            is_multi = user.data['new_question']['is_multi']
            right_answer_count = len(user.data['new_question']['right_answers'])
            if is_stat and right_answer_count > MAX_NUMBER - 1:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'Нажаль, більше {MAX_NUMBER} відповідей бути не може 😢. Для переходу на наступний етап відправте '
                         f'/done.')
                return
            if is_multi and right_answer_count > MAX_NUMBER - 2:
                if not is_stat:
                    ctx.bot.send_message(
                        chat_id=upd.effective_chat.id,
                        text=f'Нажаль, більше {MAX_NUMBER - 1} вірних відповідей бути не може 😢. Для переходу на наступний етап '
                             f'відправте /done.')
                return
            user.data['new_question']['right_answers'].append(upd.message.text)
            user.flag_data()
            new_len = len(user.data['new_question']['right_answers'])
            if is_stat or is_multi:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'{choice(["Супер", "Чудово", "Блискуче"])}, '
                         f'{"" if is_stat else "вірну "}відповідь додано! Введіть наступну відповідь' +
                         ("" if new_len < 2 else (" або введіть /done для переходу до " +
                                                  (
                                                      "наступного запитання" if is_stat else "не вірних відповідей"))) + '.')
                return MQ.QUE_ANS_RIGHT
            else:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'{choice(["Супер", "Чудово", "Блискуче"])}, Вірну відповідь додано. Тепер вводьте не вірні '
                         'відповіді:')
                return MQ.QUE_ANS
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")


def add_question_right_ans_done(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        is_stat = s.get(Quiz, user.data['quiz_mode']['quiz_id']).is_statistical
        que_ref = user.data['new_question']
        if len(que_ref['right_answers']) < 2:
            if is_stat:
                ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повинно бути принаймні 2 відповіді.")
            elif que_ref['is_multi']:
                ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повинна бути принаймні 2 вірних відповіді.")
            elif len(que_ref['right_answers']) < 1:
                ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повинна бути принаймні 1 вірна відповідь.")
            else:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'{choice(["Супер", "Чудово", "Блискуче"])}, всі вірні відповіді додано. '
                                          f'Тепер вводьте не вірні.')
                return MQ.QUE_ANS
            return MQ.QUE_ANS_RIGHT
        if is_stat:
            quiz = s.get(Quiz, user.data['quiz_mode']['quiz_id'])
            que = user.data['new_question']
            question = QuizQuestion(quiz.id, que['question'], que['is_multi'])
            s.add(question)
            s.flush()

            for ans in que['right_answers']:
                answer = QuestionAnswer(question.id, ans, True)
                s.add(answer)
            for ans in que['wrong_answers']:
                answer = QuestionAnswer(question.id, ans, False)
                s.add(answer)
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text=f'Запитання успішно створено 🎉.',
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton('Назад',
                                                            callback_data=f'{user.id}.question_mode')]]))
            return MQ.BACK_TO
        else:
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text=f'{choice(["Супер", "Чудово", "Блискуче"])}, всі вірні відповіді додано. '
                                      f'Тепер вводьте не вірні.')
            return MQ.QUE_ANS


def add_question_ans(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            answer_count = len(user.data['new_question']['right_answers']) + len(user.data['new_question']['wrong_answers'])

            if answer_count > MAX_NUMBER - 1:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'Нажаль, більше 9 відповідей бути не може 😢. Для переходу на наступний етап відправте '
                         f'/done.')
                return
            user.data['new_question']['wrong_answers'].append(upd.message.text)
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f"{choice(['Супер', 'Чудово', 'Блискуче'])}, "
                                                                 "не вірну відповідь додано! Вводьте далі, або "
                                                                 "введіть /done для збереження створеного запитання.")
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
    return MQ.QUE_ANS


def add_question_done(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        que_ref = user.data['new_question']
        if (len(que_ref['right_answers']) + len(que_ref['wrong_answers'])) < 2:
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text='Правильних і неправильних відповідей повинно бути бодай 2 в сумі, тому ми '
                                      'повертаємося до введення правильних відповідей. Якщо ви хочете додати '
                                      'неправильних відповідей - надішліть /done.')
            return MQ.QUE_ANS_RIGHT
        quiz = s.get(Quiz, user.data['quiz_mode']['quiz_id'])
        que = user.data['new_question']
        question = QuizQuestion(quiz.id, que['question'], que['is_multi'])
        s.add(question)
        s.flush()

        for ans in que['right_answers']:
            answer = QuestionAnswer(question.id, ans, True)
            s.add(answer)
        for ans in que['wrong_answers']:
            answer = QuestionAnswer(question.id, ans, False)
            s.add(answer)
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'Запитання успішно створено 🎉.',
                             reply_markup=InlineKeyboardMarkup(
                                 [[InlineKeyboardButton('Назад',
                                                        callback_data=f'{user.id}.question_mode')]]))
        return MQ.BACK_TO


def add_answer(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            is_stat = s.get(Quiz, user.data['quiz_mode']['quiz_id']).is_statistical

            if s.query(QuestionAnswer).filter_by(question_id=user.data['question_mode']['question_id']).count() < \
                    MAX_NUMBER:
                if is_stat:
                        answer = QuestionAnswer(user.data['question_mode']['question_id'], upd.message.text, True)
                        s.add(answer)
                        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                             text=f'Відповідь успішно додано 🎉.',
                                             reply_markup=InlineKeyboardMarkup(
                                                 [[InlineKeyboardButton('Назад',
                                                                        callback_data=f'{user.id}.question_edit_mode')]]))
                else:
                    user.set_data('new_answer', {
                        'answer': upd.message.text,
                        'is_right': True,
                    })
                    ctx.bot.send_message(
                        chat_id=upd.effective_chat.id,
                        text=f'{choice(["Чудова", "Гарна", "Класна"])} відповідь! Тепер оберіть тип відповіді: ',
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton('Вірна', callback_data='True')],
                             [InlineKeyboardButton('Не вірна', callback_data='False')]]))
                    return MQ.ADD_ANS
            else:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Кількість відповідей на це запитання максимальна 😢. Однак ви можете '
                                          f'видалити наявну відповідь та додати замість неї іншу (або просто '
                                          f'змінити її).')
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
        return MQ.QUESTION_EDIT_MODE


def add_answer_type(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = eval(query.data)
    query.answer()
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        if s.query(QuestionAnswer).filter_by(question_id=user.data['question_mode']['question_id']).count() <\
                MAX_NUMBER:
            answer = QuestionAnswer(user.data['question_mode']['question_id'], user.data['new_answer']['answer'], action)
            s.add(answer)
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text=f'Відповідь успішно додано 🎉.',
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton('Назад',
                                                            callback_data=f'{user.id}.answer_edit_mode')]]))
            return MQ.BACK_TO
        else:
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text=f'Кількість відповідей на це запитання максимальна 😢. Однак ви можете '
                                      f'видалити наявну відповідь та додати замість неї іншу (або просто '
                                      f'змінити її).')


def question_delete(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action_split = query.data.split('.')
    msg = 'Запитання успішно видалено!'
    match action_split:
        case question_id, 'yes':
            with db_session.begin() as s:
                question = s.get(QuizQuestion, question_id)
                s.delete(question)
        case question_id, 'no':
            msg = "Видалення запитання відмінено 🎉"
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('🚪 Повернутися до списку запитань',
                                 callback_data=f'{user.data["quiz_mode"]["quiz_id"]}.question_mode')
        ]]))
    query.answer()
    return MQ.BACK_TO


def cat_delete(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = query.data
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        match action:
            case 'quiz':
                quiz = s.get(Quiz, user.data['quiz_mode']['quiz_id'])
                query.edit_message_text(get_quiz_info(quiz),
                                        reply_markup=get_edit_quiz_keyboard(quiz))
                return MQ.EDIT
        query.edit_message_reply_markup(get_cat_keyboard(user.data['quiz_mode']['quiz_id'], action))
    query.answer()
    return MQ.CAT_MODE


def quiz_delete(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action_split = query.data.split('.')
    msg = "Опитування успішно видалено!"
    match action_split:
        case quiz_id, 'yes':
            with db_session.begin() as s:
                quiz = s.get(Quiz, quiz_id)
                s.delete(quiz)
        case quiz_id, 'no':
            msg = "Видалення опитування відмінено 🎉"
    query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton('🚪 Повернутися до списку опитувань', callback_data=f'{upd.effective_user.id}.quiz_list'),
    ]]))
    query.answer()
    return MQ.BACK_TO


def add_cat(upd: Update, ctx: CallbackContext):
    cat_name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(cat_name):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            quiz = s.get(Quiz, user.data['quiz_mode']['quiz_id'])
            cat = s.query(QuizCategoryType).filter_by(name=cat_name).one_or_none()

            message_id = user.data['quiz_mode']['message_id']
            quiz_id = user.data['quiz_mode']['quiz_id']

            if cat is not None and cat.name in quiz.categories:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Цю категорію вже додано.')
                return MQ.CAT_MODE
            if len(quiz.categories) >= MAX_NUMBER:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'На жаль, не можна додати більше {MAX_NUMBER} категорій. Ви можете '
                                          f'переглянути додані категорії та видалити їх, натиснувши на кнопку із '
                                          f'відповідною категорією під повідомленням вище.')
                return MQ.CAT_MODE

            if cat is None:
                cat = QuizCategoryType(cat_name)
                s.add(cat)
                s.flush()
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Ви перші вказали категорію "{cat_name}". Оце так винахідливість!')

            new_cat = QuizCategory(quiz.id, cat.id)
            s.add(new_cat)
            s.flush()

        ctx.bot.edit_message_reply_markup(upd.effective_chat.id, message_id,
                                          reply_markup=get_cat_keyboard(quiz_id))
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'Категорію "{upd.message.text}" додано.')
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
    return MQ.CAT_MODE


def back_to(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action_split = query.data.split('.')
    action_split[0] = int(action_split[0])
    query.answer()
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        match action_split:
            case quiz_id, 'quiz':
                quiz = s.get(Quiz, quiz_id)
                query.edit_message_text(get_quiz_info(quiz),
                                        reply_markup=get_edit_quiz_keyboard(quiz))
                return MQ.EDIT
            case user_id, 'quiz_list':
                query.edit_message_text('Оберіть опитування:',
                                        reply_markup=get_all_quizzes_keyboard(upd.effective_user.id))
                return MQ.SHOW
            case user_id, 'question_mode':
                query.edit_message_text('Оберіть запитання, яке хочете змінити:',
                                        reply_markup=get_question_mode_keyboard(upd.effective_user.id))
                return MQ.QUESTION_MODE
            case user_id, 'question_edit_mode':
                user.flag_data()
                question: QuizQuestion = s.get(QuizQuestion, user.data['question_mode']['question_id'])
                query.edit_message_text(f'Запитання: {question.question}\n'
                                        f'Кількість відповідей: {"кілька" if question.is_multi else "одна"}',  # \nВаріанти відповідей:',
                                        reply_markup=get_question_edit_mode_keyboard(question.id))
                return MQ.QUESTION_EDIT_MODE
            case answer_id, 'answer_edit_mode':
                question: QuizQuestion = s.get(QuizQuestion, user.data['question_mode']['question_id'])
                is_statistical = s.get(Quiz, question.quiz_id).is_statistical
                query.edit_message_text(
                    f'Оберіть відповідь для редагування (' + (
                        f"повинно бути кілька {'' if is_statistical else 'вірних '}відповідей" if question.is_multi else f"повинна бути лише одна {'' if is_statistical else 'вірна '}відповідь") + '):',
                    reply_markup=get_answer_keyboard(question)
                )
                return MQ.ANSWER_EDIT_MODE


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
            MessageHandler(Filters.text & ~Filters.command, rename),
            CallbackQueryHandler(back_to),
        ],
        MQ.QUESTION_MODE: [
            CallbackQueryHandler(question_mode),
            MessageHandler(Filters.text & ~Filters.command, add_question),
        ],
        MQ.QUE_IS_MULTI: [
            CallbackQueryHandler(add_question_is_multi),
        ],
        MQ.QUE_ANS_RIGHT: [
            MessageHandler(Filters.text & ~Filters.command, add_question_right_ans),
            CommandHandler('done', add_question_right_ans_done),
        ],
        MQ.QUE_ANS: [
            MessageHandler(Filters.text & ~Filters.command, add_question_ans),
            CommandHandler('done', add_question_done),
        ],
        MQ.QUESTION_EDIT: [
            MessageHandler(Filters.text & ~Filters.command, question_edit),
            CallbackQueryHandler(back_to),
        ],
        MQ.QUESTION_EDIT_MODE: [
            CallbackQueryHandler(question_edit_mode),
        ],
        MQ.ADD_ANS: [
            CallbackQueryHandler(add_answer_type),
        ],
        MQ.ANSWER_MODE: [
            CallbackQueryHandler(answer_mode),
        ],
        MQ.ANSWER_EDIT: [
            MessageHandler(Filters.text & ~ Filters.command, answer_edit),
            CallbackQueryHandler(back_to),
        ],
        MQ.ANSWER_EDIT_MODE: [
            MessageHandler(Filters.text & ~Filters.command, add_answer),
            CallbackQueryHandler(answer_edit_mode),
        ],
        MQ.QUESTION_DELETE: [
            CallbackQueryHandler(question_delete),
        ],
        MQ.ANSWER_DELETE: [
            CallbackQueryHandler(answer_delete),
        ],
        MQ.DELETE: [
            CallbackQueryHandler(quiz_delete),
        ],
        MQ.CAT_MODE: [
            MessageHandler(Filters.text & ~Filters.command, add_cat),
            CallbackQueryHandler(cat_delete),
        ],
        MQ.BACK_TO: [
            CallbackQueryHandler(back_to),
        ]
    },
    # TODO: better handling
    fallbacks=[CommandHandler('cancel', lambda *args: ConversationHandler.END), ],
))
