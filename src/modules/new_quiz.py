from cfg import *
from models import *

# Bot
from bot import *

# Telegram API
from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackContext, ConversationHandler

# DB API
from sqlalchemy.orm.attributes import flag_modified

# Misc.
from random import choice
from enum import Enum

# Константи бота
class NQ(Enum):
    NAME = 0
    NEW_CATEGORY = 1
    QUE = 2
    QUE_ANS = 3
    QUE_ANS_RIGHT = 4
    PRIVACY = 5


def cmd_new_quiz(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)

        # Можливість продовжити створення?
        user.data['new_quiz'] = {
            'categories': [],
            'questions': [],
        }
        flag_modified(user, 'data')

    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='1. Введіть назву нового опитування. Щоб відмінити '
                                                             'створення опитування, введіть /cancel.')
    return NQ.NAME


def conv_nq_name(upd: Update, ctx: CallbackContext):
    name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(name):
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['name'] = name
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'Назва "{upd.message.text}" просто чудова!')
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text='2. Тепер, вводьте категорії цього опитування по '
                                                                 'одній. Щоб завершити введення категорій та продовжити'
                                                                 'створення опитування, введіть /done. '
                                                                 'Ви можете переглянути додані категорії за допомогою'
                                                                 'команди /show.')
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Ця назва не пасує вашому опитуванню :(\n'
                                                                 'Оберіть, будь-ласка, іншу (●\'◡\'●)')
        return NQ.NAME
    return NQ.NEW_CATEGORY


def conv_nq_cat(upd: Update, ctx: CallbackContext):
    cat_name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(cat_name):
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            cat_ref = user.data['new_quiz']['categories']
            cat = s.query(QuizCategoryType).filter_by(name=cat_name).one_or_none()

            if cat is not None and cat.id in cat_ref:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Цю категорію вже додано. Ви можете проглянути додані категорії за '
                                          f'допомогою команди /show.')
                return NQ.NEW_CATEGORY
            if len(cat_ref) >= MAX_CATEGORY_NUMBER:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Нажаль, не можна додати більше {MAX_CATEGORY_NUMBER} категорій. Ви можете '
                                          f'переглянути додані категорії та видалити їх за допомогою команди /show')
                return NQ.NEW_CATEGORY

            if cat is None:
                cat = QuizCategoryType(cat_name)
                s.add(cat)
                s.flush()
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Ви перші вказали категорію {cat_name}. Оце так винахідливість!')

            cat_ref.append(cat.id)
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'Категорію "{upd.message.text}" додано. '
                                                                 'Відправте ще категорію, щоб закінчити додання '
                                                                 'категорій, введіть команду /done.')
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Така назва категорії неприйнятна, або спробуйте '
                                                                 'ввести іншу. (●\'◡\'●)')
    return NQ.NEW_CATEGORY


# def conv_nq_cat_rules(upd: Update, ctx: CallbackContext):
#    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Назва категорії повинна містити лише наступні символи:\n'
#                                                              '«a-zа-яёїієґ\-_,\.()1-9\'" »\n'
#                                                              'Та бути довжиною у 3-50 символів')
#     return NQ.NEW_CATEGORY


def conv_nq_cat_show(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        cats = user.data['new_quiz']['categories']
        res = ''
        for x in range(len(cats)):
            res += f'{x + 1}. {s.get(QuizCategoryType, cats[x]).name}.\n'
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'Категорії опитування:\n{res}')
    # TODO: видалення категорій за доп. кнопок.
    return NQ.NEW_CATEGORY


def conv_nq_cat_done(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        cats = user.data['new_quiz']['categories']
        res = ''
        for x in range(len(cats)):
            res += f'{x + 1}. {s.get(QuizCategoryType, cats[x]).name}.\n'
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'Категорії додано:\n{res}'
                                                             f'Тепер, введіть запитання (1<=X<=256 символів).')
    return NQ.QUE


def conv_nq_que(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['questions'].append({
                'question': upd.message.text,
                'right_answers': [],
                'wrong_answers': [],
            })
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f"{choice(['Чудове', 'Гарне', 'Класне'])} запитання! "
                                                                 f"Тепер вводьте правильні відповіді. Якщо опитування "
                                                                 f"не передбачає правильності відповідей - пропустіть "
                                                                 f"введення неправильних відповідей.")
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f"Запитання містить неприйнятні символи, або занадто "
                                                                 "довге. Спробуйте його змінити.")
        return NQ.QUE
    return NQ.QUE_ANS_RIGHT


def conv_nq_que_right_ans(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['questions'][-1]['right_answers'].append(upd.message.text)
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f"{choice(['Супер', 'Чудово', 'Блискуче'])}, "
                                                                 f"вірну відповідь додано! Вводьте далі, або "
                                                                 f"введіть /done для переходу до невірних "
                                                                 f"відповідей.")
    return NQ.QUE_ANS_RIGHT


def conv_nq_que_right_ans_done(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        cur_que_ref = user.data['new_quiz']['questions'][-1]
        if len(cur_que_ref['right_answers']) < 1:
            ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повинна бути бодай одна вірна відповідь.")
            return NQ.QUE_ANS_RIGHT
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f"{choice(['Супер', 'Чудово', 'Блискуче'])}, "
                                                             "всі вірні відповіді додано. Тепер вводьте "
                                                             "невірні.")
    return NQ.QUE_ANS


def conv_nq_que_ans(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['questions'][-1]['wrong_answers'].append(upd.message.text)
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f"{choice(['Супер', 'Чудово', 'Блискуче'])}, "
                                                                 "невірну відповідь додано! Вводьте далі, або "
                                                                 "введіть /done для переходу до наступного запитання.")
    return NQ.QUE_ANS


def conv_nq_que_done(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        cur_que_ref = user.data['new_quiz']['questions'][-1]
        if (len(cur_que_ref['right_answers']) + len(cur_que_ref['right_answers'])) < 2:
            ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Правильних і неправильних відповідей повинно "
                                                                     "бути бодай 2 в сумі, тому ми повертаємося до "
                                                                     "введення правильних відповідей. Якщо ви хочете "
                                                                     "додати неправильних відповідей - надішліть "
                                                                     "/done.")
            return NQ.QUE_ANS_RIGHT
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'Запитання додано. Тепер введіть нове запитання '
                                                             'Або завершіть створення опитування, ввівши команду /done '
                                                             'ще раз.')
    return NQ.QUE


def conv_nq_success_end(upd: Update, ctx: CallbackContext):
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Опитування успішно складено. Тепер оберіть приватність '
                                                             'опитування:\n'
                                                             '/private - приватне опитування, доступне лише за '
                                                             'спеціальним кодом.\n'
                                                             '/public - публічне опитування, доступне за пошуком та '
                                                             'може потрапити у списки найпопулярніших і тому подібне.')
    return NQ.PRIVACY


def conv_nq_privacy(upd: Update, ctx: CallbackContext):
    privacy = upd.message.text[1:] == 'public'
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)

        quiz_ref = user.data['new_quiz']
        cats_ref = quiz_ref['categories']
        que_ref = quiz_ref['questions']

        quiz = Quiz(quiz_ref['name'], user.id, privacy)
        s.add(quiz)
        s.flush()

        for cat in cats_ref:
            kitten = QuizCategory(quiz.id, cat)
            s.add(kitten)

        for que in que_ref:
            question = QuizQuestion(quiz.id, que['question'])
            s.add(question)
            s.flush()

            for ans in que['right_answers']:
                answer = QuestionAnswer(question.id, ans, True)
                s.add(answer)
            for ans in que['wrong_answers']:
                answer = QuestionAnswer(question.id, ans, False)
                s.add(answer)

        user.clear_data()
    return ConversationHandler.END


def conv_nq_cancel(upd: Update, ctx: CallbackContext):
    """ Видаляє всі згадки про це опитування. """
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        del user.data['new_quiz']
        flag_modified(user, 'data')
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Створення опитування скасовано.')
    return ConversationHandler.END


# Створення нового опитування.
dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('new_quiz', cmd_new_quiz)],
    states={
        NQ.NAME: [MessageHandler(Filters.text & ~Filters.command, conv_nq_name), ],
        NQ.NEW_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, conv_nq_cat),
                          CommandHandler('show', conv_nq_cat_show),
                          CommandHandler('done', conv_nq_cat_done), ],
        NQ.QUE: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que),
                 CommandHandler('done', conv_nq_success_end), ],
        NQ.QUE_ANS_RIGHT: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_right_ans),
                           CommandHandler('done', conv_nq_que_right_ans_done), ],
        NQ.QUE_ANS: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_ans),
                     CommandHandler('next', conv_nq_que_done),
                     CommandHandler('done', conv_nq_success_end),
                     ],
        NQ.PRIVACY: [
            CommandHandler('private', conv_nq_privacy),
            CommandHandler('public', conv_nq_privacy),
        ]
    },
    fallbacks=[CommandHandler('cancel', conv_nq_cancel)]
))

