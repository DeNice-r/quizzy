# Bot
from bot import *

# Telegram API
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler

# DB API
from db.engine import session

# Misc.
from random import choice
from enum import Enum


# Константи бота
class NQ(Enum):
    NAME, NEW_CATEGORY, QUE, QUE_ANS, QUE_ANS_RIGHT = range(5)


def privacy_or_multi_callback(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    split = query.data.split('.')
    action = eval(split[1])
    query.answer()
    if split[0] == 'privacy':
        query.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton(('Публічне' if action else 'Приватне') + ' опитування',
                                   callback_data='privacy.' + str(not action))]]))
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['privacy'] = action
            user.flag_data()
    elif split[0 == 'multi']:
        query.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton(('Кілька відповідей' if action else 'Одна відповідь'),
                                   callback_data='multi.' + str(not action))]]))
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['questions'][-1]['multi'] = action
            user.flag_data()



def cmd_new_quiz(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)

        # Можливість продовжити створення?
        user.data['new_quiz'] = {
            'categories': [],
            'questions': [],
            'privacy': True
        }
        user.flag_data()

    keyboard = [[InlineKeyboardButton('Публічне опитування', callback_data='privacy.False')]]
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='1. Введіть назву нового опитування. Щоб відмінити '
                                                             'створення опитування, введіть /cancel.',
                         reply_markup=InlineKeyboardMarkup(keyboard))
    return NQ.NAME


# TODO: замінити на кнопку в меню опитування
def cmd_remove_quiz(upd: Update, ctx: CallbackContext):
    split = upd.message.text.split(' ')
    if len(split) != 2:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Щоб видалити власне опитування потрібно вказати '
                                                                 'його код:\n/pass Abc123dEF4')
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
        if quiz.author_id == user.id:
            s.delete(quiz)
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text='Опитування видалено 😢.')
        else:
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text='Опитування неможливо видалити 😎.')


def conv_nq_name(upd: Update, ctx: CallbackContext):
    name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(name):
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'Назва "{upd.message.text}" просто чудова!')
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text='2. Тепер, вводьте категорії цього опитування по одній. Щоб завершити введення '
                                  'категорій та продовжити створення опитування, введіть /done. Ви можете переглянути '
                                  'додані категорії за допомогою команди /show.')
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['name'] = name
            user.flag_data()
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
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
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'Категорію "{upd.message.text}" додано. Відправте ще категорію, щоб закінчити '
                                  'додання категорій, введіть команду /done.')
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
    return NQ.NEW_CATEGORY


# def conv_nq_cat_rules(upd: Update, ctx: CallbackContext):
#    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Назва категорії повинна містити лише наступні символи:\n'
#                                                              '«a-zа-яёїієґ\-_,\.()1-9\'" »\n'
#                                                              'Та бути довжиною у 3-50 символів')
#     return NQ.NEW_CATEGORY


def get_cat_markup(user_id, cat_id_to_remove=None):
    keyboard = []
    with session.begin() as s:
        user = s.get(User, user_id)
        cats = user.data['new_quiz']['categories']
        if cat_id_to_remove is not None:
            cats.remove(cat_id_to_remove)
            user.flag_data()
        for x in range(len(cats)):
            cat = s.get(QuizCategoryType, cats[x])
            keyboard.append([InlineKeyboardButton(cat.name, callback_data=str(cat.id))])
        return InlineKeyboardMarkup(keyboard)


def conv_nq_cat_show(upd: Update, ctx: CallbackContext):
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'Категорії опитування (нажміть для видалення категорії):',
                         reply_markup=get_cat_markup(upd.effective_user.id))
    return NQ.NEW_CATEGORY


def rem_cat_callback(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    query.edit_message_reply_markup(get_cat_markup(upd.effective_user.id, int(query.data)))


def conv_nq_cat_done(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        cats = user.data['new_quiz']['categories']
        res = ''
        for x in range(len(cats)):
            res += f'{x + 1}. {s.get(QuizCategoryType, cats[x]).name}.\n'
    ctx.bot.send_message(chat_id=upd.effective_chat.id,
                         text=f'Категорії додано:\n{res}Тепер, введіть запитання (1<=X<=256 символів).')
    return NQ.QUE


def conv_nq_que(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['questions'].append({
                'question': upd.message.text,
                'right_answers': [],
                'wrong_answers': [],
                'multi': False
            })
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'{choice(["Чудове", "Гарне", "Класне"])} запитання! Тепер вводьте правильні '
                                  'відповіді. Якщо опитування не передбачає правильності відповідей - пропустіть '
                                  'введення неправильних відповідей.',
                             reply_markup=InlineKeyboardMarkup(
                                 [[InlineKeyboardButton('Одна відповідь',
                                   callback_data='multi.True')]]))
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
        return NQ.QUE
    return NQ.QUE_ANS_RIGHT


def conv_nq_que_right_ans(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['questions'][-1]['right_answers'].append(upd.message.text)
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'{choice(["Супер", "Чудово", "Блискуче"])}, вірну відповідь додано! Вводьте далі, '
                                  'або введіть /done для переходу до невірних відповідей.')
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
    return NQ.QUE_ANS_RIGHT


def conv_nq_que_right_ans_done(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        cur_que_ref = user.data['new_quiz']['questions'][-1]
        if len(cur_que_ref['right_answers']) < 1:
            ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повинна бути бодай одна вірна відповідь.")
            return NQ.QUE_ANS_RIGHT
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'{choice(["Супер", "Чудово", "Блискуче"])}, '
                                                             'всі вірні відповіді додано. Тепер вводьте невірні.')
    return NQ.QUE_ANS


def conv_nq_que_ans(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['questions'][-1]['wrong_answers'].append(upd.message.text)
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f"{choice(['Супер', 'Чудово', 'Блискуче'])}, "
                                                                 "невірну відповідь додано! Вводьте далі, або "
                                                                 "введіть /next для переходу до наступного запитання.")
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
    return NQ.QUE_ANS


def conv_nq_que_done(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        cur_que_ref = user.data['new_quiz']['questions'][-1]
        if (len(cur_que_ref['right_answers']) + len(cur_que_ref['right_answers'])) < 2:
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text='Правильних і неправильних відповідей повинно бути бодай 2 в сумі, тому ми '
                                      'повертаємося до введення правильних відповідей. Якщо ви хочете додати '
                                      'неправильних відповідей - надішліть /done.')
            return NQ.QUE_ANS_RIGHT
    ctx.bot.send_message(chat_id=upd.effective_chat.id,
                         text=f'Запитання додано. Тепер введіть нове запитання або завершіть створення опитування, '
                              f'ввівши команду /done.')
    return NQ.QUE


def conv_nq_success_end(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)

        quiz_ref = user.data['new_quiz']
        cats_ref = quiz_ref['categories']
        que_ref = quiz_ref['questions']

        quiz = Quiz(quiz_ref['name'], user.id, quiz_ref['privacy'])

        s.add(quiz)
        s.flush()

        for cat in cats_ref:
            kitten = QuizCategory(quiz.id, cat)
            s.add(kitten)

        for que in que_ref:
            question = QuizQuestion(quiz.id, que['question'], user.data['new_quiz']['multi'])
            s.add(question)
            s.flush()

            for ans in que['right_answers']:
                answer = QuestionAnswer(question.id, ans, True)
                s.add(answer)
            for ans in que['wrong_answers']:
                answer = QuestionAnswer(question.id, ans, False)
                s.add(answer)
        tok = QuizToken(quiz.id)
        s.add(tok)
        ctx.bot\
            .send_message(
            chat_id=upd.effective_chat.id,
            text=f'Опитування успішно створено! Код опитування - {tok.token}. Його можна знайти за'
                 f' {"назвою або " if quiz.is_public else ""}цим кодом у пошуку (/search {tok.token}'
                 f'{" або /search " + quiz.name if quiz.is_public else ""}) або за допомогою команди '
                 f'/pass {tok.token}. Цей код можна подивитися та змінити у меню опитування.')
        user.clear_data()
    return ConversationHandler.END


def conv_nq_cancel(upd: Update, ctx: CallbackContext):
    """ Видаляє всі згадки про це опитування. """
    with session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        del user.data['new_quiz']
        user.flag_data()
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Створення опитування скасовано.')
    return ConversationHandler.END


# Створення нового опитування.
# TODO: при створенні опитування та запитання додати налаштування за допомогою кнопок
dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('new_quiz', cmd_new_quiz)],
    states={
        NQ.NAME: [MessageHandler(Filters.text & ~Filters.command, conv_nq_name), ],
        NQ.NEW_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, conv_nq_cat),
                          CommandHandler('show', conv_nq_cat_show),
                          CallbackQueryHandler(rem_cat_callback),
                          CommandHandler('done', conv_nq_cat_done), ],
        NQ.QUE: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que),
                 CommandHandler('done', conv_nq_success_end), ],
        NQ.QUE_ANS_RIGHT: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_right_ans),
                           CommandHandler('done', conv_nq_que_right_ans_done), ],
        NQ.QUE_ANS: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_ans),
                     CommandHandler('next', conv_nq_que_done),
                     CommandHandler('done', conv_nq_success_end),
                     ],
    },
    fallbacks=[CommandHandler('cancel', conv_nq_cancel),
               CallbackQueryHandler(privacy_or_multi_callback),
               ]
))

dispatcher.add_handler(CommandHandler('remove_quiz', cmd_remove_quiz))
