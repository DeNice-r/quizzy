# Bot
from bot import *

# Telegram API
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler

# DB API
from db.engine import db_session
from db.models.Group import Group
from db.models.GroupToken import GroupToken
from db.models.User import User

# Misc.
from enum import Enum


# Константи бота
class NG(Enum):
    NAME, DESCRIPTION = range(2)


def cmd_new_group(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)

        # Можливість продовжити створення?
        user.set_data('new_group', {
            'privacy': True
        })

    keyboard = [[InlineKeyboardButton('Публічне опитування', callback_data='privacy')]]
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Введіть назву нової групи. Щоб відмінити '
                                                             'створення, введіть /cancel. Також ви можете '
                                                             'змінити налаштування публічності цієї групи, '
                                                             'натиснувши кнопку під цим повідомленням.',
                         reply_markup=InlineKeyboardMarkup(keyboard))
    return NG.NAME


def conv_ng_name(upd: Update, ctx: CallbackContext):
    name = upd.message.text
    if RE_SHORT_TEXT.fullmatch(name):
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'Назва "{upd.message.text}" просто чудова!\n'
                                  'Тепер введіть опис групи:',)
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_group']['name'] = name
            user.flag_data()
        return NG.DESCRIPTION
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
        return NG.NAME


def conv_ng_description(upd: Update, ctx: CallbackContext):
    description = upd.message.text
    if RE_SHORT_TEXT.fullmatch(description):
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'Назва "{upd.message.text}" просто чудова!\n'
                                  'Тепер введіть опис групи:', )
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_group']['description'] = description
            user.flag_data()

            #
            new_group_ref = user.data['new_group']
            group = Group(upd.effective_user.id, new_group_ref['is_public'], new_group_ref['name'],
                          new_group_ref['description'])
            s.add(group)
            s.flush()

            token = GroupToken(group.id)
            s.add(token)

            ctx.bot \
                .send_message(
                chat_id=upd.effective_chat.id,
                text=f'Групу успішно створено! Код групи - {token.token}\nЙого можна знайти за '
                     f'{"назвою або " if group.is_public else ""}цим кодом у пошуку (/group_search {token.token}'
                     f'{" або /group_search " + group.name if group.is_public else ""}) або за допомогою команди '
                     f'/join {token.token}. Цей код можна подивитися та змінити у меню групи.')
            #

        return NG.DESCRIPTION
    else:
        ctx.bot.send_message(chat_id=upd.effective_chat.id, text="Повідомлення містить недопустимі символи або занадто "
                                                                 "довге :(")
        return NG.DESCRIPTION


def privacy_callback(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = query.data
    if action == 'privacy':
        with db_session.begin() as s:
            user = s.get(User, upd.effective_user.id)
            user.data['new_group']['privacy'] = not user.data['new_group']['privacy']
            user.flag_data()
            query.edit_message_reply_markup(
                InlineKeyboardMarkup([[
                    InlineKeyboardButton(('Публічна' if user.data['new_group']['privacy'] else 'Приватна') + ' група',
                                         callback_data='privacy')]]))
    query.answer()


def conv_ng_cancel(upd: Update, ctx: CallbackContext):
    """ Видаляє всі згадки про цю групу. """
    with db_session.begin() as s:
        user = s.get(User, upd.effective_user.id)
        user.remove_data('new_group')
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='Створення групи скасовано.')
    return ConversationHandler.END


dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('new_quiz', cmd_new_group)],
    states={
        NG.NAME: [MessageHandler(Filters.text & ~Filters.command, conv_ng_name), ],
        NG.DESCRIPTION: [CallbackQueryHandler(conv_ng_description), ],
    },
    fallbacks=[CommandHandler('cancel', conv_ng_cancel),
               ],
))


dispatcher.add_handler(CommandHandler('new_group', cmd_new_group))
