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


class MQ(Enum):
    SHOW, B, C = range(3)


def cmd_my_quizzes(upd: Update, ctx: CallbackContext):
    with session.begin() as s:
        quizzes = s.query(Quiz).filter_by(author_id=upd.effective_user.id).all()
        keyboard = []
        for q_idx in range(0, len(quizzes), 2):
            keyboard.append([
                InlineKeyboardButton(quizzes[q_idx].name, callback_data=str(quizzes[q_idx].id)),
            ])
            if q_idx + 1 < len(quizzes):
                keyboard[-1].append(InlineKeyboardButton(quizzes[q_idx+1].name, callback_data=str(quizzes[q_idx].id)))
        ctx.bot.send_message(chat_id=upd.effective_chat.id,
                             text=f'Оберіть опитування:',
                             reply_markup=InlineKeyboardMarkup(keyboard))
    return MQ.SHOW


def quiz_edit(upd: Update, ctx: CallbackContext):
    query = upd.callback_query
    query.answer()
    action = int(query.data)
    with session.begin() as s:

        print(s.get(Quiz, action).name)



dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('my_quizzes', cmd_my_quizzes)],
    states={
        MQ.SHOW: [
            CallbackQueryHandler(quiz_edit),
                  ],
        # MQ.B: [  # MessageHandler(Filters.text & ~Filters.command, conv_pq_next_question),
    },
    fallbacks=[CommandHandler('cancel', 0), ]
))


