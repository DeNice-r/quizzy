# Machine APIs
import os
import re

from dotenv import load_dotenv

# Telegram API
from telegram.ext import Updater

# Misc
import logging


load_dotenv()

logging.basicConfig(format='[%(asctime)s]=>%(levelname)s] %(name)s: %(message)s', level=logging.INFO)

# consts
BOT_NAME = os.environ['BOT_NAME']

TELEGRAPH_TOKEN = os.environ['TELEGRAPH_TOKEN']

BACKUP_FOLDER = os.environ['BACKUP_FOLDER']

GOOD_SIGN = '💗'  # os.environ['GOOD_SIGN']
BAD_SIGN = '🖤'  # os.environ['BAD_SIGN']

MAX_NUMBER = 9
ITEMS_PER_PAGE = 9
palette = ['#E50000', '#FF8D00', '#FFEE00', '#008121', '#004CFF', '#760188']

# re's
__RAW_RE_SHORT_TEXT = r'[a-zа-яёіїєґ\-_,\.+=<>()*&^%#@!?\/\\\[\]0-9\'" ]{1,50}'
RE_SHORT_TEXT = re.compile(__RAW_RE_SHORT_TEXT, re.IGNORECASE | re.UNICODE)
__RAW_RE_MED_TEXT = r'[a-zа-яёіїєґ\-_,\.+=<>()*&^%#@!?\/\\\[\]0-9\'" \n]{1,256}'
RE_MED_TEXT = re.compile(__RAW_RE_SHORT_TEXT, re.IGNORECASE | re.UNICODE)
__RAW_RE_LONG_TEXT = r'[a-zа-яёіїєґ\-_,\.+=<>()*&^%#@!?\/\\\[\]0-9\'" \n]{1,512}'
RE_LONG_TEXT = re.compile(__RAW_RE_SHORT_TEXT, re.IGNORECASE | re.UNICODE)


updater = Updater(token=os.environ['TOKEN'], use_context=True)
dispatcher = updater.dispatcher
