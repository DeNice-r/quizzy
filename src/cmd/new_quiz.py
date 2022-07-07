# Bot
from bot import *

# Telegram API
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler

# DB API
from db.engine import db_session

# Misc.
from random import choice
from enum import Enum

# Константи бота
from db.models.QuestionAnswer import QuestionAnswer
from db.models.Quiz import Quiz
from db.models.QuizCategory import QuizCategory
from db.models.QuizCategoryType import QuizCategoryType
from db.models.QuizQuestion import QuizQuestion
from db.models.User import User


class NQ(Enum):
    NAME, IS_STATISTICAL, NEW_CATEGORY, QUE, QUE_IS_MULTI, QUE_ANS_RIGHT, QUE_ANS = range(7)


def get_cat_keyboard(user_id, cat_id_to_remove=None):
    keyboard = []
    with db_session.begin() as s:
        user = s.get(User, user_id)
        cats = user.data['new_quiz']['categories']
        if cat_id_to_remove is not None:
            cats.remove(cat_id_to_remove)
            user.flag_data()
        for x in range(len(cats)):
            cat = s.get(QuizCategoryType, cats[x])
            keyboard.append([InlineKeyboardButton(cat.name, callback_data=str(cat.id))])
        return InlineKeyboardMarkup(keyboard)


def privacy_callback(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = query.data
    if action == 'privacy':
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['privacy'] = not user.data['new_quiz']['privacy']
            user.flag_data()
            query.edit_message_reply_markup(
                InlineKeyboardMarkup([[
                    InlineKeyboardButton(('Публічне' if user.data['new_quiz']['privacy'] else 'Приватне') +
                                         ' опитування', callback_data='privacy')]]))
    query.answer()


def cmd_new_quiz(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)

        # Можливість продовжити створення?
        user.set_data('new_quiz', {
            'categories': [],
            'questions': [],
            'privacy': True
        })

    keyboard = [[InlineKeyboardButton('Публічне опитування', callback_data='privacy')]]
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Введіть назву нового опитування. Щоб відмінити '
                                                             'створення опитування, введіть /cancel. Також ви можете '
                                                             'змінити налаштування публічності цього опитування, '
                                                             'натиснувши кнопку під цим повідомленням.',
                         reply_markup=InlineKeyboardMarkup(keyboard))
    return NQ.NAME


def conv_nq_name(upd: Update, ctx: CallbackContext):
    name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(name):
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'Назва "{upd.message.text}" просто чудова!\n'
                                  'Тепер оберіть призначення опитування (*змінити неможливо*):',
                             reply_markup=InlineKeyboardMarkup([
                                 [
                                     InlineKeyboardButton('Для збору статистики (соціальні опитування і т. п.)',
                                                          callback_data='True')
                                 ],
                                 [
                                     InlineKeyboardButton('Для тестування (наприклад, тести з певної вивченої теми)',
                                                          callback_data='False')
                                 ],
                             ]), parse_mode='Markdown')
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['name'] = name
            user.flag_data()
        return NQ.IS_STATISTICAL
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
        return NQ.NAME


def conv_nq_is_statistical(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    action = eval(query.data)
    query.edit_message_text(f'Обрано тип опитування: {"збір статистики" if action else "тестування"}.\n'
                            'Тепер вводьте категорії цього опитування по одній. Щоб завершити введення '
                            'категорій та продовжити створення опитування - введіть /done. Ви можете переглянути '
                            'додані категорії за допомогою команди /show.')
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        user.data['new_quiz']['is_statistical'] = action
        user.flag_data()
    return NQ.NEW_CATEGORY


def conv_nq_cat(upd: Update, ctx: CallbackContext):
    cat_name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(cat_name):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            cat_ref = user.data['new_quiz']['categories']
            cat = s.query(QuizCategoryType).filter_by(name=cat_name).one_or_none()

            if cat is not None and cat.id in cat_ref:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Цю категорію вже додано. Ви можете проглянути додані категорії за '
                                          f'допомогою команди /show.')
                return NQ.NEW_CATEGORY
            if len(cat_ref) >= MAX_NUMBER:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Нажаль, не можна додати більше {MAX_NUMBER} категорій. Ви можете '
                                          f'переглянути додані категорії та видалити їх за допомогою команди /show')
                return NQ.NEW_CATEGORY

            if cat is None:
                cat = QuizCategoryType(cat_name)
                s.add(cat)
                s.flush()
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'Ви перші вказали категорію "{cat_name}". Оце так винахідливість!')

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


def conv_nq_cat_show(upd: Update, ctx: CallbackContext):
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f'Категорії опитування (нажміть для видалення категорії):',
                         reply_markup=get_cat_keyboard(upd.effective_user.id))
    return NQ.NEW_CATEGORY


def rem_cat_callback(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    query.edit_message_reply_markup(get_cat_keyboard(upd.effective_user.id, int(query.data)))


def conv_nq_cat_done(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        cats = user.data['new_quiz']['categories']
        res = ''
        for x in range(len(cats)):
            res += f'{x + 1}. {s.get(QuizCategoryType, cats[x]).name}.\n'
    ctx.bot.send_message(chat_id=upd.effective_chat.id,
                         text=f'Категорії додано:\n{res}Тепер введіть запитання (1<=X<=256 символів):')
    return NQ.QUE


def conv_nq_que(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_quiz']['questions'].append({
                'question': upd.message.text,
                'right_answers': [],
                'wrong_answers': [],
                'is_multi': False
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
        return NQ.QUE_IS_MULTI
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
        return NQ.QUE


def conv_nq_que_is_multi(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    is_multi = eval(query.data)
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        user.data['new_quiz']['questions'][-1]['is_multi'] = is_multi
        user.flag_data()
        is_stat = user.data['new_quiz']['is_statistical']
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
    return NQ.QUE_ANS_RIGHT


def conv_nq_que_right_ans(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            is_stat = user.data['new_quiz']['is_statistical']
            is_multi = user.data['new_quiz']['questions'][-1]['is_multi']
            right_answer_count = len(user.data['new_quiz']['questions'][-1]['right_answers'])
            if is_stat and right_answer_count > 8:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'Нажаль, більше 9 відповідей бути не може 😢. Для переходу на наступний етап відправте '
                         f'/done.')
                return
            if is_multi and right_answer_count > 7:
                if not is_stat:
                    ctx.bot.send_message(
                        chat_id=upd.effective_chat.id,
                        text=f'Нажаль, більше 8 вірних відповідей бути не може 😢. Для переходу на наступний етап '
                             f'відправте /done.')
                return
            user.data['new_quiz']['questions'][-1]['right_answers'].append(upd.message.text)
            user.flag_data()
            new_len = len(user.data['new_quiz']['questions'][-1]['right_answers'])
            if is_stat or is_multi:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'{choice(["Супер", "Чудово", "Блискуче"])}, '
                         f'{"" if is_stat else "вірну "}відповідь додано! Введіть наступну відповідь' +
                         ("" if new_len < 2 else (" або введіть /done для переходу до " +
                                                  (
                                                      "наступного запитання" if is_stat else "не вірних відповідей"))) + '.')
                return NQ.QUE_ANS_RIGHT
            else:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'{choice(["Супер", "Чудово", "Блискуче"])}, Вірну відповідь додано. Тепер вводьте не вірні '
                         'відповіді:')
                return NQ.QUE_ANS
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")


def conv_nq_que_right_ans_done(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        quiz_ref = user.data['new_quiz']
        que_ref = user.data['new_quiz']['questions'][-1]
        if len(que_ref['right_answers']) < 2:
            if quiz_ref['is_statistical']:
                ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повинно бути принаймні 2 відповіді.")
            elif que_ref['is_multi']:
                ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повинна бути принаймні 2 вірних відповіді.")
            elif len(que_ref['right_answers']) < 1:
                ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повинна бути принаймні 1 вірна відповідь.")
            else:
                ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                     text=f'{choice(["Супер", "Чудово", "Блискуче"])}, всі вірні відповіді додано. '
                                          f'Тепер вводьте не вірні.')
                return NQ.QUE_ANS
            return NQ.QUE_ANS_RIGHT
        if quiz_ref['is_statistical']:
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text=f'Запитання успішно створено. Тепер введіть наступне запитання:')
        else:
            ctx.bot.send_message(chat_id=upd.effective_chat.id,
                                 text=f'{choice(["Супер", "Чудово", "Блискуче"])}, всі вірні відповіді додано. '
                                      f'Тепер вводьте не вірні.')
        return NQ.QUE if quiz_ref['is_statistical'] else NQ.QUE_ANS


def conv_nq_que_ans(upd: Update, ctx: CallbackContext):
    if RE_MED_TEXT.fullmatch(upd.message.text):
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            answer_count = len(user.data['new_quiz']['questions'][-1]['wrong_answers']) +\
                           len(user.data['new_quiz']['questions'][-1]['right_answers'])
            if answer_count > MAX_NUMBER - 1:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'Нажаль, більше 9 відповідей бути не може 😢. Для переходу на наступний етап відправте '
                         f'/done.')
                return
            user.data['new_quiz']['questions'][-1]['wrong_answers'].append(upd.message.text)
            user.flag_data()
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text=f"{choice(['Супер', 'Чудово', 'Блискуче'])}, "
                                                                 "не вірну відповідь додано! Вводьте далі, або "
                                                                 "введіть /next для переходу до наступного запитання.")
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
    return NQ.QUE_ANS


def conv_nq_que_done(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
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
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)

        quiz_ref = user.data['new_quiz']
        cats_ref = quiz_ref['categories']
        que_ref = quiz_ref['questions']

        if len(que_ref) < 1:
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=f'Опитування без запитань? Навіть звучить чудернацьки 😅\nБудь-ласка, введіть запитання:')
            return NQ.QUE

        quiz = Quiz(quiz_ref['name'], user.id, quiz_ref['privacy'], quiz_ref['is_statistical'])
        s.add(quiz)
        s.flush()

        for cat in cats_ref:
            kitten = QuizCategory(quiz.id, cat)
            s.add(kitten)

        for que in que_ref:
            question = QuizQuestion(quiz.id, que['question'], que['is_multi'])
            s.add(question)
            s.flush()

            for ans in que['right_answers']:
                answer = QuestionAnswer(question.id, ans, True)
                s.add(answer)
            for ans in que['wrong_answers']:
                answer = QuestionAnswer(question.id, ans, False)
                s.add(answer)
        ctx.bot \
            .send_message(
            chat_id=upd.effective_chat.id,
            text=f'Опитування успішно створено! Код опитування - {quiz.token}\nЙого можна знайти за '
                 f'{"назвою або " if quiz.is_public else ""}цим кодом у пошуку (/search {quiz.token}'
                 f'{" або /search " + quiz.name if quiz.is_public else ""}) або за допомогою команди '
                 f'/pass {quiz.token}. Цей код можна подивитися та змінити у меню опитування.')
        user.clear_data()
    return ConversationHandler.END


def conv_nq_cancel(upd: Update, ctx: CallbackContext):
    """ Видаляє всі згадки про це опитування. """
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        user.remove_data('new_quiz')
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Створення опитування скасовано.')
    return ConversationHandler.END


# Створення нового опитування.
dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('new_quiz', cmd_new_quiz)],
    states={
        NQ.NAME: [MessageHandler(Filters.text & ~Filters.command, conv_nq_name), ],
        NQ.IS_STATISTICAL: [CallbackQueryHandler(conv_nq_is_statistical), ],
        NQ.NEW_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, conv_nq_cat),
                          CommandHandler('show', conv_nq_cat_show),
                          CallbackQueryHandler(rem_cat_callback),
                          CommandHandler('done', conv_nq_cat_done), ],
        NQ.QUE: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que),
                 CommandHandler('done', conv_nq_success_end), ],
        NQ.QUE_IS_MULTI: [CallbackQueryHandler(conv_nq_que_is_multi), ],
        NQ.QUE_ANS_RIGHT: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_right_ans),
                           CommandHandler('done', conv_nq_que_right_ans_done), ],
        NQ.QUE_ANS: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_ans),
                     CommandHandler('next', conv_nq_que_done),
                     CommandHandler('done', conv_nq_success_end),
                     ],
    },
    fallbacks=[CommandHandler('cancel', conv_nq_cancel),
               CallbackQueryHandler(privacy_callback),
               ],
))
