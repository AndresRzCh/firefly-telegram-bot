"""
This module initializes and starts the FireFly Telegram bot.

It performs the following tasks:
1. Loads environment variables from the .env file.
2. Initializes the SQLite database if it doesn't already exist.
3. Creates an instance of the FireFlyTelegram class to manage FireFlyIII interactions.
4. Configures the Telegram bot using the TELEGRAM_API_KEY from the environment variables.
5. Registers command and message handlers to the bot.
6. Starts polling for Telegram updates, allowing the bot to interact with users.

To run this module, simply execute `python bot.py` in the terminal.
"""

import os
import logging
import telebot
from dotenv import load_dotenv
from firefly import FireFlyTelegram
from handlers import register_handlers
from database import init_db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('bot')

logger.debug("Loading environment variables from .env file")
# Load environment variables from .env file
load_dotenv()

# Initialize the database
init_db()

# Initialize FireFlyTelegram instance
telegram_api_key = os.getenv('TELEGRAM_API_KEY')
ff_bot = FireFlyTelegram()
tg_bot = telebot.TeleBot(telegram_api_key, parse_mode=None)

# Register handlers
logger.debug("Registering command and message handlers")
register_handlers(tg_bot, ff_bot)

# Start polling
logger.info("Starting bot polling")
tg_bot.infinity_polling()
