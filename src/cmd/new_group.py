# Bot
from bot import *

# Telegram API
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler

# DB API
from db.engine import db_session
from db.models.QuestionAnswer import QuestionAnswer
from db.models.Quiz import Quiz
from db.models.QuizCategory import QuizCategory
from db.models.QuizCategoryType import QuizCategoryType
from db.models.QuizQuestion import QuizQuestion
from db.models.QuizToken import QuizToken
from db.models.User import User

# Misc.
from enum import Enum


# Константи бота
class NG(Enum):
    NAME, IS_STATISTICAL, NEW_CATEGORY, QUE, QUE_IS_MULTI, QUE_ANS_RIGHT, QUE_ANS = range(7)


def cmd_new_group(upd: Update, ctx: CallbackContext):
    raise NotImplemented


# dispatcher.add_handler(ConversationHandler(
#     entry_points=[CommandHandler('new_quiz', cmd_new_quiz)],
#     states={
#         NQ.NAME: [MessageHandler(Filters.text & ~Filters.command, conv_nq_name), ],
#         NQ.IS_STATISTICAL: [CallbackQueryHandler(conv_nq_is_statistical), ],
#         NQ.NEW_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, conv_nq_cat),
#                           CommandHandler('show', conv_nq_cat_show),
#                           CallbackQueryHandler(rem_cat_callback),
#                           CommandHandler('done', conv_nq_cat_done), ],
#         NQ.QUE: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que),
#                  CommandHandler('done', conv_nq_success_end), ],
#         NQ.QUE_IS_MULTI: [CallbackQueryHandler(conv_nq_que_is_multi), ],
#         NQ.QUE_ANS_RIGHT: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_right_ans),
#                            CommandHandler('done', conv_nq_que_right_ans_done), ],
#         NQ.QUE_ANS: [MessageHandler(Filters.text & ~Filters.command, conv_nq_que_ans),
#                      CommandHandler('next', conv_nq_que_done),
#                      CommandHandler('done', conv_nq_success_end),
#                      ],
#     },
#     fallbacks=[CommandHandler('cancel', conv_nq_cancel),
#                CallbackQueryHandler(privacy_callback),
#                ]
# ))


dispatcher.add_handler(CommandHandler('new_group', cmd_new_group))
