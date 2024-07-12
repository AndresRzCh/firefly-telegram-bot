"""
This module registers and handles Telegram bot commands and messages.

The handlers perform the following tasks:
- Handle the /start command to initialize the bot for the user.
- Process the FireFlyIII URL and API key provided by the user.
- Handle the /help command to display a help message.
- Handle the /update command to refresh the user's FireFlyIII data.
- Handle the /transactions command to list recent transactions for the user.
- Handle the /balance command to display the user's account balance.
- Process transactions and other messages from the user.
- Manage inline keyboard interactions for setting account details.
"""
import logging
import telebot
from models import CategoryError, SourceError, DestinationError, StartError, safe_math_eval

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def register_handlers(tg_bot, ff_bot):
    """
    Register the command and message handlers to the Telegram bot.

    :param TeleBot tg_bot: The Telegram bot instance
    :param FireFlyTelegram ff_bot: The FireFlyTelegram instance
    """

    @tg_bot.message_handler(commands=['start'])
    def send_welcome(message):
        chat_id = message.chat.id
        user_id = str(message.from_user.id)
        logger.debug(f"Received /start command from user {chat_id}")
        # Load session and data for the user
        ff_bot.load_session(user_id)
        ff_bot.load_data(user_id)
        # Initialize the user in the bot's dictionaries if not already loaded
        if user_id not in ff_bot.ff_url:
            ff_bot.ff_url[user_id] = ''
        if user_id not in ff_bot.ff_api:
            ff_bot.ff_api[user_id] = ''
        if user_id not in ff_bot.default_accounts:
            ff_bot.default_accounts[user_id] = ''
        if user_id not in ff_bot.categories:
            ff_bot.categories[user_id] = []
        if user_id not in ff_bot.source_accounts:
            ff_bot.source_accounts[user_id] = []
        if user_id not in ff_bot.destination_accounts:
            ff_bot.destination_accounts[user_id] = []
        if user_id not in ff_bot.asset_accounts:
            ff_bot.asset_accounts[user_id] = []
        if user_id not in ff_bot.expense_accounts:
            ff_bot.expense_accounts[user_id] = []
        if user_id not in ff_bot.revenue_accounts:
            ff_bot.revenue_accounts[user_id] = []
        if user_id not in ff_bot.account_ids:
            ff_bot.account_ids[user_id] = {}
        tg_bot.send_message(chat_id, "Enter your FireFlyIII URL.")
        tg_bot.register_next_step_handler(message, process_url)
        ff_bot.clear_user_data(user_id)
        ff_bot.clear_user_session(user_id)

    def process_url(message):
        chat_id = message.chat.id
        user = str(message.from_user.id)
        ff_bot.load_session(user)
        if user not in ff_bot.ff_url:
            ff_bot.ff_url[user] = ''
        url = message.text if message.text[-1] != '/' else message.text[:-1]
        ff_bot.ff_url[user] = url + '/api/v1/'
        ff_bot.save_session(user)
        logger.debug(f"Processed URL for user {user}: {url}")
        tg_bot.send_message(chat_id, "Please enter your FireFlyIII API Key.")
        tg_bot.register_next_step_handler(message, process_api_key)
        ff_bot.clear_user_data(user)
        ff_bot.clear_user_session(user)

    def process_api_key(message):
        chat_id = message.chat.id
        user = str(message.from_user.id)
        ff_bot.load_session(user)
        if user not in ff_bot.ff_api:
            ff_bot.ff_api[user] = ''
        ff_bot.ff_api[user] = message.text
        ff_bot.save_session(user)
        logger.debug(f"Processed API key for user {user}")
        ff_bot.get_ff_data(user)
        send_account_keyboard(chat_id, ff_bot.asset_accounts[user])
        ff_bot.clear_user_data(user)
        ff_bot.clear_user_session(user)

    def send_account_keyboard(chat_id, account_list):
        markup = telebot.types.InlineKeyboardMarkup()
        for account in account_list:
            button = telebot.types.InlineKeyboardButton(text=account, callback_data=f'set_account_{account}')
            markup.add(button)
        logger.debug(f"Sending account keyboard to chat {chat_id}")
        tg_bot.send_message(chat_id, "Choose your default account:", reply_markup=markup)

    @tg_bot.message_handler(commands=['help'])
    def send_help(message):
        help_message = """
        Welcome to FireFlyIII Telegram Bot!

    Here are some available commands:
    - /start: Set URL, API Key, and account.
    - /help: Display this help message.
    - /update: Update your FireFlyIII data.
    - /transactions: View recent entries.
    - /balance: Check your account balance.

    To add an expense send a message like: 
    ``` Description 100 [Category] [AssetAccount] [ExpenseAccount]```
    To add a revenue send a message like:
    ``` Description +100 [Category] [AssetAccount] [RevenueAccount]```
    To add a transfer send a message like:
    ``` 100 Account1 Account2```

    The numbers can be simple equations too:
    ``` (100 + 5) / 2 Account 1 Account2```

    The `[Category]` field is optional.
    The `[AssetAccount]` field is optional.
    The `[AssetAccount]` field is optional.
    The `[RevenueAccount]` field is optional.
    """
        chat_id = message.chat.id
        logger.debug(f"Received /help command from user {chat_id}")
        tg_bot.send_message(chat_id, help_message, parse_mode="Markdown")

    @tg_bot.message_handler(commands=['update'])
    def update_data(message):
        user_id = str(message.from_user.id)
        ff_bot.load_session(user_id)
        ff_bot.load_data(user_id)
        logger.debug(f"Received /update command from user {user_id}")
        ff_bot.get_ff_data(user_id)
        tg_bot.reply_to(message, "Categories and accounts updated!")
        ff_bot.clear_user_data(user_id)
        ff_bot.clear_user_session(user_id)


    @tg_bot.message_handler(commands=['transactions'])
    def list_transactions(message):
        user = str(message.from_user.id)
        ff_bot.load_session(user)
        ff_bot.load_data(user)
        chat_id = message.chat.id
        logger.debug(f"Received /transactions command from user {user}")
        response = ff_bot.get_transactions(user)
        tg_bot.send_message(chat_id, response, parse_mode="Markdown")
        ff_bot.clear_user_data(user)
        ff_bot.clear_user_session(user)

    @tg_bot.message_handler(commands=['balance'])
    def show_balance(message):
        user = str(message.from_user.id)
        ff_bot.load_session(user)
        ff_bot.load_data(user)
        chat_id = message.chat.id
        logger.debug(f"Received /balance command from user {user}")
        response = ff_bot.get_balance(user)
        tg_bot.send_message(chat_id, response, parse_mode="Markdown")
        ff_bot.clear_user_data(user)
        ff_bot.clear_user_session(user)

    @tg_bot.message_handler(func=lambda message: message.text[0].isdigit())
    def echo_transfer(message):
        user = str(message.from_user.id)
        ff_bot.load_session(user)
        ff_bot.load_data(user)
        chat_id = message.chat.id
        logger.debug(f"Processing transaction input from user {user}: {message.text}")
        try:
            text = message.text.split(' ')
            if len(text) == 3:
                source = ff_bot.get_source_account(text[1], user)
                destination = ff_bot.get_destination_account(text[2], user)
                response, transaction_id = ff_bot.new_transaction({'description': 'Transfer', 'number': safe_math_eval(text[0]), 'source': source, 'destination': destination, 'type': 'transfer', 'category': None}, user)
                logger.info(f'{message.from_user.username} - {transaction_id} - {response}')
                keyboard = telebot.types.InlineKeyboardMarkup()
                delete_button = telebot.types.InlineKeyboardButton("Delete", callback_data=f"delete_{transaction_id}")
                keyboard.add(delete_button)
                tg_bot.send_message(chat_id, response, reply_markup=keyboard)
            else:
                tg_bot.send_message(chat_id, 'Invalid Input!')
        except SourceError:
            tg_bot.send_message(message, 'Add the source account to FireFlyIII and run /update before!')
        except DestinationError:
            tg_bot.send_message(message, 'Add the destination account to FireFlyIII and run /update before!')
        except StartError:
            tg_bot.send_message(message, 'Run /start first!')
        ff_bot.clear_user_data(user)
        ff_bot.clear_user_session(user)

    @tg_bot.message_handler(func=lambda message: not message.text[0].isdigit())
    def echo_all(message):
        user = str(message.from_user.id)
        ff_bot.load_session(user)
        ff_bot.load_data(user)
        chat_id = message.chat.id
        logger.debug(f"Processing message from user {user}: {message.text}")
        try:
            info = ff_bot.extract_info(message.text, user)
            if info is not None:
                response, transaction_id = ff_bot.new_transaction(info, user)
                logger.info(f'{message.from_user.username} - {transaction_id} - {response}')
                keyboard = telebot.types.InlineKeyboardMarkup()
                delete_button = telebot.types.InlineKeyboardButton("Delete", callback_data=f"delete_{transaction_id}")
                set_category_button = telebot.types.InlineKeyboardButton("Set Category", callback_data=f"set_category_{transaction_id}_{info['type']}")
                set_asset_button = telebot.types.InlineKeyboardButton("Asset Account", callback_data=f"set_asset_{transaction_id}_{info['type']}")
                if info['type'] == 'withdrawal':
                    set_account_button = telebot.types.InlineKeyboardButton("Expense Account", callback_data=f"set_expense_{transaction_id}_{info['type']}")
                else:
                    set_account_button = telebot.types.InlineKeyboardButton("Revenue Account", callback_data=f"set_revenue_{transaction_id}_{info['type']}")
                keyboard.row(delete_button, set_category_button)
                keyboard.row(set_asset_button, set_account_button)
                tg_bot.send_message(chat_id, response, reply_markup=keyboard)
            else:
                logger.error(f'Invalid Input: {message.text}')
                tg_bot.send_message(chat_id, 'Invalid Input!')
        except CategoryError:
            logger.error('Category not found. Please update before.')
            tg_bot.send_message(chat_id, 'Add the category to FireFlyIII and run /update before!')
        except SourceError:
            logger.error('Source account not found. Please update before.')
            tg_bot.send_message(chat_id, 'Add the source account to FireFlyIII and run /update before!')
        except DestinationError:
            logger.error('Destination account not found. Please update before.')
            tg_bot.send_message(chat_id, 'Add the destination account to FireFlyIII and run /update before!')
        except StartError:
            logger.error('User not found. Please initialize before.')
            tg_bot.send_message(chat_id, 'Run /start first!')
        ff_bot.clear_user_data(user)
        ff_bot.clear_user_session(user)

    @tg_bot.callback_query_handler(func=lambda call: True)
    def process_callback_query(call):
        chat_id = call.message.chat.id
        user = str(call.from_user.id)
        ff_bot.load_session(user)
        ff_bot.load_data(user)
        logger.debug(f"Processing callback query from user {user}: {call.data}")

        if call.data.startswith('delete_'):
            transaction_id = call.data.split('_')[1]
            ff_bot.delete_transaction(transaction_id, user)
            tg_bot.delete_message(chat_id, call.message.message_id)

        elif call.data.startswith('set_account_'):
            default_account = call.data.split('_')[2]
            if default_account in ff_bot.asset_accounts[user]:
                ff_bot.default_accounts[user] = default_account
                ff_bot.save_session(user)
                tg_bot.send_message(chat_id, "Configuration saved successfully! Run /help to know how to use the bot.")
            tg_bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
            for i in range(5):
                last_message_id = call.message.message_id - i
                tg_bot.delete_message(chat_id, last_message_id)
            tg_bot.send_message(chat_id, "Setup completed. Run /help to see the commands.")

        elif call.data.startswith('set_category_'):
            transaction_id, kind = call.data.split('_')[2:]
            markup = telebot.types.InlineKeyboardMarkup()
            for category in ff_bot.categories[user]:
                button = telebot.types.InlineKeyboardButton(text=category, callback_data=f"category_{transaction_id}_{category}_{kind}")
                markup.add(button)
            tg_bot.send_message(chat_id, "Select a category:", reply_markup=markup)

        elif call.data.startswith('category_'):
            _, transaction_id, category, kind = call.data.split('_')
            response = ff_bot.update_transaction_category(transaction_id, category, user)
            logger.info(f'{call.from_user.username} - {transaction_id} - {response}')
            tg_bot.delete_message(chat_id, call.message.message_id - 1)
            keyboard = telebot.types.InlineKeyboardMarkup()
            delete_button = telebot.types.InlineKeyboardButton("Delete", callback_data=f"delete_{transaction_id}")
            set_category_button = telebot.types.InlineKeyboardButton("Set Category", callback_data=f"set_category_{transaction_id}_{kind}")
            set_asset_button = telebot.types.InlineKeyboardButton("Asset Account", callback_data=f"set_asset_{transaction_id}_{kind}")
            if kind == 'withdrawal':
                set_account_button = telebot.types.InlineKeyboardButton("Expense Account", callback_data=f"set_expense_{transaction_id}_{kind}")
            else:
                set_account_button = telebot.types.InlineKeyboardButton("Revenue Account", callback_data=f"set_revenue_{transaction_id}_{kind}")
            keyboard.row(delete_button, set_category_button)
            keyboard.row(set_asset_button, set_account_button)
            tg_bot.edit_message_text(chat_id=chat_id, text=response, message_id=call.message.message_id, reply_markup=keyboard)

        elif call.data.startswith('set_asset_'):
            transaction_id, kind = call.data.split('_')[2:]
            markup = telebot.types.InlineKeyboardMarkup()
            for asset_account in ff_bot.asset_accounts[user]:
                button = telebot.types.InlineKeyboardButton(text=asset_account, callback_data=f"asset_{transaction_id}_{asset_account}_{kind}")
                markup.add(button)
            tg_bot.send_message(chat_id, "Select the asset account:", reply_markup=markup)

        elif call.data.startswith('asset_'):
            _, transaction_id, asset_account, kind = call.data.split('_')
            response = ff_bot.update_transaction_asset(transaction_id, asset_account, user)
            logger.info(f'{call.from_user.username} - {transaction_id} - {response}')
            tg_bot.delete_message(chat_id, call.message.message_id - 1)
            keyboard = telebot.types.InlineKeyboardMarkup()
            delete_button = telebot.types.InlineKeyboardButton("Delete", callback_data=f"delete_{transaction_id}")
            set_category_button = telebot.types.InlineKeyboardButton("Set Category", callback_data=f"set_category_{transaction_id}_{kind}")
            set_asset_button = telebot.types.InlineKeyboardButton("Asset Account", callback_data=f"set_asset_{transaction_id}_{kind}")
            if kind == 'withdrawal':
                set_account_button = telebot.types.InlineKeyboardButton("Expense Account", callback_data=f"set_expense_{transaction_id}_{kind}")
            else:
                set_account_button = telebot.types.InlineKeyboardButton("Revenue Account", callback_data=f"set_revenue_{transaction_id}_{kind}")
            keyboard.row(delete_button, set_category_button)
            keyboard.row(set_asset_button, set_account_button)
            tg_bot.edit_message_text(chat_id=chat_id, text=response, message_id=call.message.message_id, reply_markup=keyboard)

        elif call.data.startswith('set_expense_'):
            transaction_id, kind = call.data.split('_')[2:]
            markup = telebot.types.InlineKeyboardMarkup()
            for expense_account in ff_bot.expense_accounts[user]:
                button = telebot.types.InlineKeyboardButton(text=expense_account, callback_data=f"expense_{transaction_id}_{expense_account}_{kind}")
                markup.add(button)
            tg_bot.send_message(chat_id, "Select an expense account:", reply_markup=markup)

        elif call.data.startswith('expense_'):
            _, transaction_id, expense_account, kind = call.data.split('_')
            response = ff_bot.update_transaction_expense(transaction_id, expense_account, user)
            logger.info(f'{call.from_user.username} - {transaction_id} - {response}')
            tg_bot.delete_message(chat_id, call.message.message_id - 1)
            keyboard = telebot.types.InlineKeyboardMarkup()
            delete_button = telebot.types.InlineKeyboardButton("Delete", callback_data=f"delete_{transaction_id}")
            set_category_button = telebot.types.InlineKeyboardButton("Set Category", callback_data=f"set_category_{transaction_id}_{kind}")
            set_asset_button = telebot.types.InlineKeyboardButton("Asset Account", callback_data=f"set_asset_{transaction_id}_{kind}")
            if kind == 'withdrawal':
                set_account_button = telebot.types.InlineKeyboardButton("Expense Account", callback_data=f"set_expense_{transaction_id}_{kind}")
            else:
                set_account_button = telebot.types.InlineKeyboardButton("Revenue Account", callback_data=f"set_revenue_{transaction_id}_{kind}")
            keyboard.row(delete_button, set_category_button)
            keyboard.row(set_asset_button, set_account_button)
            tg_bot.edit_message_text(chat_id=chat_id, text=response, message_id=call.message.message_id, reply_markup=keyboard)

        elif call.data.startswith('set_revenue_'):
            transaction_id, kind = call.data.split('_')[2:]
            markup = telebot.types.InlineKeyboardMarkup()
            for revenue_account in ff_bot.revenue_accounts[user]:
                button = telebot.types.InlineKeyboardButton(text=revenue_account, callback_data=f"revenue_{transaction_id}_{revenue_account}_{kind}")
                markup.add(button)
            tg_bot.send_message(chat_id, "Select a revenue account:", reply_markup=markup)

        elif call.data.startswith('revenue_'):
            _, transaction_id, revenue_account, kind = call.data.split('_')
            response = ff_bot.update_transaction_revenue(transaction_id, revenue_account, user)
            logger.info(f'{call.from_user.username} - {transaction_id} - {response}')
            tg_bot.delete_message(chat_id, call.message.message_id - 1)
            keyboard = telebot.types.InlineKeyboardMarkup()
            delete_button = telebot.types.InlineKeyboardButton("Delete", callback_data=f"delete_{transaction_id}")
            set_category_button = telebot.types.InlineKeyboardButton("Set Category", callback_data=f"set_category_{transaction_id}_{kind}")
            set_asset_button = telebot.types.InlineKeyboardButton("Asset Account", callback_data=f"set_asset_{transaction_id}_{kind}")
            if kind == 'withdrawal':
                set_account_button = telebot.types.InlineKeyboardButton("Expense Account", callback_data=f"set_expense_{transaction_id}_{kind}")
            else:
                set_account_button = telebot.types.InlineKeyboardButton("Revenue Account", callback_data=f"set_revenue_{transaction_id}_{kind}")
            keyboard.row(delete_button, set_category_button)
            keyboard.row(set_asset_button, set_account_button)
            tg_bot.edit_message_text(chat_id=chat_id, text=response, message_id=call.message.message_id)
            tg_bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=keyboard)
        ff_bot.clear_user_data(user)
        ff_bot.clear_user_session(user)
