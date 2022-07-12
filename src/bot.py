import io
import random
import subprocess
import sys

from cfg import *
from db.models.User import User

# Telegram API
from telegram import Update, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext

# DB API
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from db.engine import db_session, db_engine, create_engine
from db.models.Admin import Admin

# System API for backup
import datetime
from subprocess import Popen

from utils import generate_token


def cmd_start(upd: Update, ctx: CallbackContext):
    """
        Записуємо дані про нового (?) користувача в бд
        відображуємо йому підказки щодо роботи з ботом,
    """
    msg = f'Ви успішно авторизувалися у {BOT_NAME}.'
    try:
        with db_session.begin() as s:
            new_user = User(upd.effective_user.id)
            s.add(new_user)
    except IntegrityError as e:
        msg = f'Ви вже авторизовані у {BOT_NAME}!'

    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=msg)


# def cmd_backup(upd: Update, ctx: CallbackContext):
#     # Maybe try to copy instead of archiving?
#     if upd.effective_user.id != 408526329:
#         return
#     backup_folder = "D:/PostgreSQL/BaseBackup"
#     backup_dt = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
#     current_backup_path = backup_folder + f'/{backup_dt}_backup'
#
#     # p = Popen(["D:\\PostgreSQL\\14\\bin\pg_basebackup.exe", "-U", "postgres", "-D", backup_folder, "-Ft", "-R"],
#     #           stdout=sys.stdout, stdin=sys.stdin)
#     # p.communicate()
#
#     message_data = ctx.bot.send_message(upd.effective_chat.id, 'Резервне копіювання...')
#     dt_start = datetime.datetime.now()
#
#     with db_session.begin() as s:
#         s.execute(text("""SELECT pg_start_backup('label', false, false);"""))
#
#     p = Popen(["7z", "a", "-t7z", "-mx=9",
#                current_backup_path, 'D:/PostgreSQL/14/data/', '-xr!data/pg_wal/0*', '-x!data/postmaster*',
#                '-xr!data/pg_wal/archive_status/*', '-xr!data/pg_replslot/*', '-xr!data/pg_dynshmem/*',
#                '-xr!data/pg_notify/*', '-xr!data/pg_serial/*', '-xr!data/pg_snapshots/*', '-xr!data/pg_stat_tmp/*',
#                '-xr!data/pg_subtrans/*', '-xr!pgsql_tmp*', '-xr!pg_internal.init'])
#     p.communicate()
#     with db_session.begin() as s:
#         res = s.execute(text("""SELECT * FROM pg_stop_backup(false, false);"""))
#         s.execute(text("""SELECT pg_switch_wal();"""))
#         for r in res:
#             with open(f"{backup_folder}/{backup_dt}_backup_label", mode='w') as f:
#                 f.write(r[1])
#             if r[2] != '':
#                 with open(f"{backup_folder}/{backup_dt}_tablespace_map", mode='w') as f:
#                     f.write(r[2])
#
#             dt_end = datetime.datetime.now()
#             # print('RESULT:', r)
#             ctx.bot.edit_message_text('Резервне копіювання успішно завершено!\n'
#                                       f'Шлях до копії: {current_backup_path}.7z\n'
#                                       f'Часу знадобилося на копіювання: {dt_end - dt_start}\n',
#                                       message_data.chat_id,
#                                       message_data.message_id)


def cmd_backup(upd: Update, ctx: CallbackContext):
    with db_session.begin() as s:
        if s.get(Admin, upd.effective_user.id) is None:
            return
    message_data = ctx.bot.send_message(upd.effective_chat.id, 'Резервне копіювання...')
    dt_start = datetime.datetime.now()
    backup_folder = BACKUP_FOLDER
    backup_dt = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    backup_path = backup_folder + f'/{backup_dt}_{generate_token(3)}_backup.sql'
    process = Popen(f'pg_dump.exe --file {backup_path} --host localhost --port 5432 '
                    f'--quote-all-identifiers --format=p --create --clean --section=pre-data '
                    f'--section=data --section=post-data quizzy'.split(' '), stdout=subprocess.PIPE)
    process.wait()
    dt_end = datetime.datetime.now()
    ctx.bot.edit_message_text('Резервне копіювання успішно завершено!\n'
                              f'Шлях до копії: {backup_path}\n'
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


dispatcher.add_handler(CommandHandler('backup', cmd_backup))
dispatcher.add_handler(CommandHandler('restore', cmd_restore))
dispatcher.add_handler(CommandHandler('start', cmd_start))
