from cfg import *
from models import *
from utils import *

# Telegram API
from telegram import Update
from telegram.ext import MessageHandler, CommandHandler, Filters, CallbackContext, ConversationHandler

# DB API
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified

# Misc.
from random import choice


def cmd_start(upd: Update, ctx: CallbackContext):
    """
        Записуємо дані про нового (?) користувача в бд
        відображуємо йому підказки щодо роботи з ботом,
    """
    msg = f'Ви успішно авторизувалися у {bot_name}.'
    new_user = User(upd.effective_user.id)
    try:
        with session.begin() as s:
            s.add(new_user)
    except IntegrityError as e:
        msg = f'Ви вже авторизовані у {bot_name}!'

    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=msg)


def cmd_new_group(upd: Update, ctx: CallbackContext):
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='New group placeholder OMEGALUL')


""" Команди """
""" Загальні """
# Розпочати роботу з ботом
dispatcher.add_handler(CommandHandler('start', cmd_start))

""" Групи """
# Створити нову групу
dispatcher.add_handler(CommandHandler('new_group', cmd_new_group))

""" Статистика (Відділити чи внести у вже наявні розділи?) """
# dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, bot_answer))
