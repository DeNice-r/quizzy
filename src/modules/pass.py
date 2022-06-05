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

# Константи бота
NQ_NAME, NQ_NEW_CATEGORY, NQ_QUE, NQ_QUE_ANS, NQ_QUE_ANS_RIGHT, NQ_PRIVACY = range(6)


def cmd_pass(upd: Update, ctx: CallbackContext):
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
    return NQ_NAME


dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('new_quiz', cmd_new_quiz)],
    states={
        NQ_NAME: [MessageHandler(Filters.text & ~Filters.command, conv_nq_name), ],
        NQ_NEW_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, conv_nq_cat),
                          CommandHandler('show', conv_nq_cat_show),
                          CommandHandler('done', conv_nq_cat_done), ],
        NQ_QUE: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que),
                 CommandHandler('done', conv_nq_success_end), ],
        NQ_QUE_ANS_RIGHT: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_right_ans),
                           CommandHandler('done', conv_nq_que_right_ans_done), ],
        NQ_QUE_ANS: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_ans),
                     CommandHandler('next', conv_nq_que_done),
                     CommandHandler('done', conv_nq_success_end),
                     ],
        NQ_PRIVACY: [
            CommandHandler('private', conv_nq_privacy),
            CommandHandler('public', conv_nq_privacy),
        ]
    },
    fallbacks=[CommandHandler('cancel', conv_nq_cancel)]
))
