"""
This module handles the SQLite database operations for the FireFly bot.

It performs the following tasks:
- Initialize the database and create necessary tables if they do not exist.
- Connect to the SQLite database.
- Retrieve session data for a specific user from the database.
- Save session data for a specific user to the database.
- Retrieve FireFlyIII data for a specific user from the database.
- Save FireFlyIII data for a specific user to the database.
"""

import json
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('database')

db_path = os.getenv('DATABASE_PATH')

def init_db():
    """
    Initialize the database and create necessary tables if they don't exist.
    """
    logger.debug("Initializing the database")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS session (
        user_id TEXT PRIMARY KEY,
        ff_url TEXT,
        ff_api TEXT,
        default_account TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS data (
        user_id TEXT PRIMARY KEY,
        categories TEXT,
        source_accounts TEXT,
        destination_accounts TEXT,
        asset_accounts TEXT,
        expense_accounts TEXT,
        revenue_accounts TEXT,
        account_ids TEXT
    )''')
    conn.commit()
    conn.close()
    logger.debug("Database initialized successfully")

def connect_db():
    """
    Connect to the SQLite database.

    :return: SQLite connection object
    :rtype: sqlite3.Connection
    """
    if not os.path.exists(db_path):
        logger.warning(f"Database file {db_path} does not exist. Creating it.")
        init_db()
    return sqlite3.connect(db_path)

def get_session(user_id):
    """
    Retrieve session data for a user from the database.

    :param str user_id: The ID of the user
    :return: Session data or None if not found
    :rtype: tuple or None
    """
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT ff_url, ff_api, default_account FROM session WHERE user_id = ?", (user_id,))
    session = c.fetchone()
    conn.close()
    if session:
        logger.debug(f"Session retrieved for user {user_id}")
    else:
        logger.error(f"No session found for user {user_id}")
    return session

def save_session(user_id, ff_url, ff_api, default_account):
    """
    Save session data for a user to the database.

    :param str user_id: The ID of the user
    :param str ff_url: The FireFlyIII URL
    :param str ff_api: The FireFlyIII API key
    :param str default_account: The default account
    """
    conn = connect_db()
    c = conn.cursor()
    c.execute("REPLACE INTO session (user_id, ff_url, ff_api, default_account) VALUES (?, ?, ?, ?)",
              (user_id, ff_url, ff_api, default_account))
    conn.commit()
    conn.close()
    logger.debug(f"Session saved for user {user_id}")

def get_data(user_id):
    """
    Retrieve FireFlyIII data for a user from the database.

    :param str user_id: The ID of the user
    :return: FireFlyIII data or None if not found
    :rtype: tuple or None
    """
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT categories, source_accounts, destination_accounts, asset_accounts, expense_accounts, revenue_accounts, account_ids FROM data WHERE user_id = ?", (user_id,))
    data = c.fetchone()
    conn.close()
    if data:
        logger.debug(f"Data retrieved for user {user_id}")
        return (
            json.loads(data[0]), json.loads(data[1]), json.loads(data[2]),
            json.loads(data[3]), json.loads(data[4]), json.loads(data[5]), json.loads(data[6])
        )
    else:
        logger.error(f"No data found for user {user_id}")
    return None

def save_data(user_id, categories, source_accounts, destination_accounts, asset_accounts, expense_accounts, revenue_accounts, account_ids):
    """
    Save FireFlyIII data for a user to the database.

    :param str user_id: The ID of the user
    :param list categories: The list of categories
    :param list source_accounts: The list of source accounts
    :param list destination_accounts: The list of destination accounts
    :param list asset_accounts: The list of asset accounts
    :param list expense_accounts: The list of expense accounts
    :param list revenue_accounts: The list of revenue accounts
    :param dict account_ids: The dictionary of account IDs
    """
    conn = connect_db()
    c = conn.cursor()
    c.execute("REPLACE INTO data (user_id, categories, source_accounts, destination_accounts, asset_accounts, expense_accounts, revenue_accounts, account_ids) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, json.dumps(categories), json.dumps(source_accounts), json.dumps(destination_accounts), json.dumps(asset_accounts), json.dumps(expense_accounts), json.dumps(revenue_accounts), json.dumps(account_ids)))
    conn.commit()
    conn.close()
    logger.debug(f"Data saved for user {user_id}")
