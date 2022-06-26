import datetime
import subprocess
import sys

from cfg import *
from db.models.User import User

# Telegram API
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

# DB API
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from db.engine import db_session

# System API for backup
from subprocess import Popen
from sys import stdout


# Misc.


def cmd_start(upd: Update, ctx: CallbackContext):
    """
        Записуємо дані про нового (?) користувача в бд
        відображуємо йому підказки щодо роботи з ботом,
    """
    msg = f'Ви успішно авторизувалися у {bot_name}.'
    try:
        with db_session.begin() as s:
            new_user = User(upd.effective_user.id)
            s.add(new_user)
    except IntegrityError as e:
        msg = f'Ви вже авторизовані у {bot_name}!'

    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=msg)


def cmd_new_group(upd: Update, ctx: CallbackContext):
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text='New group placeholder OMEGALUL')


def cmd_backup(upd: Update, ctx: CallbackContext):
    backup_folder = "D:/PostgreSQL/BaseBackup"
    backup_dt = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    current_backup_path = backup_folder + f'/{backup_dt}_backup'

    # p = Popen(["D:\\PostgreSQL\\14\\bin\pg_basebackup.exe", "-U", "postgres", "-D", backup_folder, "-Ft", "-R"],
    #           stdout=sys.stdout, stdin=sys.stdin)
    # p.communicate()

    message_data = ctx.bot.send_message(upd.effective_chat.id, 'Резервне копіювання...')
    dt_start = datetime.datetime.now()

    with db_session.begin() as s:
        s.execute(text("""SELECT pg_start_backup('label', false, false);"""))

    p = Popen(["7z", "a", "-t7z", "-mx=9",
               current_backup_path, 'D:/PostgreSQL/14/data/', '-xr!data/pg_wal/0*', '-x!data/postmaster*',
               '-xr!data/pg_wal/archive_status/*' ])#, '-xr!data/pg_replslot/*', '-xr!data/pg_dynshmem/*',
               # '-xr!data/pg_notify/*', '-xr!data/pg_serial/*', '-xr!data/pg_snapshots/*', '-xr!data/pg_stat_tmp/*',
               # '-xr!data/pg_subtrans/*', '-xr!pgsql_tmp*', '-xr!pg_internal.init'])
    p.communicate()
    with db_session.begin() as s:
        res = s.execute(text("""SELECT * FROM pg_stop_backup(false, false);"""))
        s.execute(text("""SELECT pg_switch_wal();"""))
        for r in res:
            with open(f"{backup_folder}/{backup_dt}_backup_label", mode='w') as f:
                f.write(r[1])
            if r[2] != '':
                with open(f"{backup_folder}/{backup_dt}_tablespace_map", mode='w') as f:
                    f.write(r[2])

            dt_end = datetime.datetime.now()
            # print('RESULT:', r)
            ctx.bot.edit_message_text('Резервне копіювання успішно завершено!\n'
                                      f'Шлях до копії: {current_backup_path}.7z\n'
                                      f'Часу знадобилося на копіювання: {dt_end - dt_start}\n',
                                      message_data.chat_id,
                                      message_data.message_id)


""" Команди """
""" Загальні """
# Розпочати роботу з ботом
dispatcher.add_handler(CommandHandler('start', cmd_start))

""" Групи """
# Створити нову групу
dispatcher.add_handler(CommandHandler('new_group', cmd_new_group))

""" Статистика (Відділити чи внести у вже наявні розділи?) """
# dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, bot_answer))
""" Бекап """
dispatcher.add_handler(CommandHandler('backup', cmd_backup))
