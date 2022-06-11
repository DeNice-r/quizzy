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

bot_name = os.environ['BOT_NAME']

# consts
MAX_CATEGORY_NUMBER = 10

# re's
_RAW_RE_SHORT_TEXT = r'[a-zа-яёіїєґ\-_,\.+=<>()*&^%#@!?\/\\\[\]1-9\'" ]{1,50}'
RE_SHORT_TEXT = re.compile(_RAW_RE_SHORT_TEXT, re.IGNORECASE | re.UNICODE)
_RAW_RE_MED_TEXT = r'[a-zа-яёіїєґ\-_,\.+=<>()*&^%#@!?\/\\\[\]1-9\'" \n]{1,256}'
RE_MED_TEXT = re.compile(_RAW_RE_SHORT_TEXT, re.IGNORECASE | re.UNICODE)


updater = Updater(token=os.environ['TOKEN'], use_context=True)
dispatcher = updater.dispatcher
