# Bot
from bot import *

# Telegram API
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler

# DB API
from db.engine import db_session
from db.models.Group import Group
from db.models.GroupMember import GroupMember
from db.models.GroupToken import GroupToken
from db.models.User import User

# Misc.
from enum import Enum


# Константи бота
class MG(Enum):
    CHOICE = range(1)


def cmd_join(upd: Update, ctx: CallbackContext):
    split = upd.message.text.split(' ')
    if len(split) != 2:
        ctx.bot.send_message(
            chat_id=upd.effective_chat.id,
            text='Щоб стати членом групи потрібно вказати її код:\n/join Abc123dEF4')
        return

    with db_session.begin() as s:
        group_token = s.query(GroupToken).filter_by(token=split[1]).one_or_none()
        if group_token is None:
            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text='Опитування не знайдено 😢. Можливо, ви помилилися у коді або автор опитування його змінив.')
        else:
            try:
                group_member = GroupMember(upd.effective_user.id, group_token.group_id)
                s.add(group_member)
                s.flush()
            except:
                ctx.bot.send_message(
                    chat_id=upd.effective_chat.id,
                    text=f'Ви вже є учасником цієї групи 😉.')
                return

            ctx.bot.send_message(
                chat_id=upd.effective_chat.id,
                text=f'Тепер ви учасник групи "{group_token.group.name}".')


def cmd_my_groups(upd: Update, ctx: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton('Групи, учасником яких ви є', callback_data=f'member_of'),
        ],
        [
            InlineKeyboardButton('Групи, що належать вам', callback_data=f'owner_of'),
        ],
    ]
    ctx.bot.send_message(chat_id=upd.effective_chat.id,
                         text=f'Оберіть опитування:',
                         reply_markup=InlineKeyboardMarkup(keyboard))
    return MG.CHOICE


def conv_mg_choice(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    action = query.data
    if action == 'member_of':
        with db_session.begin() as s:
            pass
    elif action == 'owner_of':
        with db_session.begin() as s:
            pass
    query.answer()


def conv_mg_cancel(upd: Update, ctx: CallbackContext):
    return ConversationHandler.END


dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('my_groups', cmd_my_groups)],
    states={
        MG.CHOICE: [CallbackQueryHandler(conv_mg_choice), ],
    },
    fallbacks=[CommandHandler('cancel', conv_mg_cancel),
               ],
))


dispatcher.add_handler(CommandHandler('join', cmd_join))
