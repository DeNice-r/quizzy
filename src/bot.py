import io
import random
import subprocess
import sys

from cfg import *
from db.models.User import User

# Telegram API
from telegram import Update, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters

# DB API
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from db.engine import db_session, db_engine, create_engine
from db.models.Admin import Admin

# System API for backup
import datetime
from subprocess import Popen
import shutil

from utils import generate_token
from enum import Enum


def cmd_start(upd: Update, ctx: CallbackContext):
    msg = f'Ви успішно авторизувалися у {BOT_NAME}.'
    try:
        with db_session.begin() as s:
            new_user = User(upd.effective_user.id)
            s.add(new_user)
    except IntegrityError as e:
        msg = f'Ви вже авторизовані у {BOT_NAME}!'

    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=msg)


def cmd_backup(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        if s.get(Admin, upd.effective_user.id) is None:
            return
    message_data = ctx.bot.send_message(upd.effective_chat.id, 'Резервне копіювання...')
    dt_start = datetime.datetime.now()
    backup_folder = BACKUP_FOLDER
    backup_dt = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    db_name = os.environ["DATABASE_URL"].split("/")[-1]
    backup_path = backup_folder + f'/{db_name}_{backup_dt}_{generate_token(3)}_backup.sql'
    process = Popen(f'pg_dump.exe --file {backup_path} --host localhost --port 5432 '
                    f'--quote-all-identifiers --format=p --create --clean --section=pre-data '
                    f'--section=data --section=post-data {db_name}'.split(' '), stdout=subprocess.PIPE)
    process.wait()
    dt_end = datetime.datetime.now()
    ctx.bot.edit_message_text('Резервне копіювання успішно завершено!\n'
                              f'Шлях до копії: {backup_path}\n'
                              f'Часу знадобилося на копіювання: {dt_end - dt_start}\n',
                              message_data.chat_id,
                              message_data.message_id)


def cmd_base_backup(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        if s.get(Admin, upd.effective_user.id) is None:
            return
    message_data = ctx.bot.send_message(upd.effective_chat.id, 'Резервне копіювання...')
    dt_start = datetime.datetime.now()
    backup_folder = BACKUP_FOLDER + '/BaseBackup'
    try:
        shutil.rmtree(backup_folder)
    except:
        pass
    process = Popen(f'pg_basebackup.exe -X stream -D {backup_folder}'.split(' '), stdout=subprocess.PIPE)
    process.wait()
    dt_end = datetime.datetime.now()
    ctx.bot.edit_message_text('Резервне копіювання успішно завершено!\n'
                              f'Шлях до копії: {backup_folder}\n'
                              f'Часу знадобилося на копіювання: {dt_end - dt_start}\n',
                              message_data.chat_id,
                              message_data.message_id)


def cmd_restore(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        if s.get(Admin, upd.effective_user.id) is None:
            return
    message_data = ctx.bot.send_message(upd.effective_chat.id, 'Відновлення...')
    global db_engine
    db_engine.dispose()
    dt_start = datetime.datetime.now()
    backup_path = upd.message.text.split(' ')[1]
    process = Popen(f'psql -f {backup_path}'.split(' '), stdout=subprocess.PIPE)
    process.communicate()
    db_engine = create_engine()
    dt_end = datetime.datetime.now()
    ctx.bot.edit_message_text('Резервне копіювання успішно завершено!\n'
                              f'Часу знадобилося на відновлення: {dt_end - dt_start}\n',
                              message_data.chat_id,
                              message_data.message_id)


def cmd_add_admin(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        if s.get(Admin, upd.effective_user.id) is None:
            return
        user_id = upd.message.text.split(' ')[1]
        try:
            if s.get(User, user_id) is not None:
                admin = Admin(user_id)
                s.add(admin)
            else:
                ctx.bot.send_message(upd.effective_chat.id, 'Цей користувач не авторизувався у боті.')
                return
        except:
            ctx.bot.send_message(upd.effective_chat.id, 'Цей користувач вже є адміністратором.')
            return
    ctx.bot.send_message(upd.effective_chat.id, 'Адміністратора успішно додано!')


def cmd_remove_admin(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        if s.get(Admin, upd.effective_user.id) is None:
            return
        user_id = upd.message.text.split(' ')[1]
        try:
            admin = s.get(Admin, user_id)
            if admin is not None:
                s.remove(admin)
            else:
                ctx.bot.send_message(upd.effective_chat.id, 'Цей користувач не є адміністратором.')
        except:
            ctx.bot.send_message(upd.effective_chat.id, 'Цей користувач не є адміністратором.')
            return
    ctx.bot.send_message(upd.effective_chat.id, 'Адміністратора успішно видалено!')


def cmd_get_user_id(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        if s.get(Admin, upd.effective_user.id) is None:
            return
    ctx.bot.send_message(upd.effective_chat.id, 'Перешліть сюди повідомлення користувача щоб отримати його ID. Щоб '
                                                'відмінити цю операцію - надішліть /cancel')
    return 0


def get_user_id(upd: Update, ctx: CallbackContext):
    ctx.bot.send_message(upd.effective_chat.id, f'ID користувача: {upd.message.forward_from.id}')
    return ConversationHandler.END


dispatcher.add_handler(ConversationHandler(
    entry_points=[CommandHandler('get_user_id', cmd_get_user_id)],
    states={
        0: [MessageHandler(Filters.text & ~Filters.command, get_user_id)]
    },
    fallbacks=[CommandHandler('cancel', lambda *args: ConversationHandler.END)]
))
dispatcher.add_handler(CommandHandler('add_admin', cmd_add_admin))
dispatcher.add_handler(CommandHandler('remove_admin', cmd_remove_admin))
dispatcher.add_handler(CommandHandler('backup', cmd_backup))
dispatcher.add_handler(CommandHandler('base_backup', cmd_base_backup))
dispatcher.add_handler(CommandHandler('restore', cmd_restore))
dispatcher.add_handler(CommandHandler('start', cmd_start))
