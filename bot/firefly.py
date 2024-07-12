"""
This module defines the FireFlyTelegram class that manages interactions with the FireFlyIII API.

The FireFlyTelegram class provides methods for:
- Loading and saving user sessions and data
- Fetching categories and accounts from FireFlyIII
- Handling transactions (creation, deletion, updating)
- Extracting transaction information from input strings

It also includes utility functions for loading and clearing user data from memory.
"""

import os
import re
import datetime
import logging
import requests
from slugify import slugify
from models import CategoryError, SourceError, DestinationError, StartError, safe_math_eval
from database import get_session, save_session, get_data, save_data

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class FireFlyTelegram:
    """
    A class to handle interactions with the FireFlyIII API.
    """

    def __init__(self):
        """
        Initialize the FireFlyTelegram instance.
        """
        logger.debug("Initializing FireFlyTelegram")
        self.telegram_api = os.getenv('TELEGRAM_API_KEY')
        self.timeout = int(os.getenv('REQUEST_TIMEOUT'))
        if not self.telegram_api:
            logger.error("TELEGRAM_API_KEY is not set in the environment variables")
        else:
            logger.debug("TELEGRAM_API_KEY successfully retrieved")
        self.ff_url = {}
        self.ff_api = {}
        self.default_accounts = {}
        self.categories = {}
        self.source_accounts = {}
        self.destination_accounts = {}
        self.asset_accounts = {}
        self.expense_accounts = {}
        self.revenue_accounts = {}
        self.account_ids = {}

    def clear_user_session(self, user_id):
        """
        Clear session data for a user from the database.

        :param str user_id: The ID of the user
        """
        if user_id in self.ff_url:
            del self.ff_url[user_id]
        if user_id in self.ff_api:
            del self.ff_api[user_id]
        if user_id in self.default_accounts:
            del self.default_accounts[user_id]

    def clear_user_data(self, user_id):
        """
        Load FireFlyIII data for a user from the database.

        :param str user_id: The ID of the user
        """
        if user_id in self.categories:
            del self.categories[user_id]
        if user_id in self.source_accounts:
            del self.source_accounts[user_id]
        if user_id in self.destination_accounts:
            del self.destination_accounts[user_id]
        if user_id in self.asset_accounts:
            del self.asset_accounts[user_id]
        if user_id in self.expense_accounts:
            del self.expense_accounts[user_id]
        if user_id in self.revenue_accounts:
            del self.revenue_accounts[user_id]
        if user_id in self.account_ids:
            del self.account_ids[user_id]

    def load_session(self, user_id):
        """
        Load session data for a user from the database.

        :param str user_id: The ID of the user
        """
        session = get_session(user_id)
        if session:
            self.ff_url[user_id], self.ff_api[user_id], self.default_accounts[user_id] = session

    def load_data(self, user_id):
        """
        Load FireFlyIII data for a user from the database.

        :param str user_id: The ID of the user
        """
        data = get_data(user_id)
        if data:
            self.categories[user_id], self.source_accounts[user_id], self.destination_accounts[user_id], self.asset_accounts[user_id], self.expense_accounts[user_id], self.revenue_accounts[user_id], self.account_ids[user_id] = data

    def save_session(self, user_id):
        """
        Save session data for a user to the database.

        :param str user_id: The ID of the user
        """
        if user_id not in self.ff_url:
            self.ff_url[user_id] = ''
        if user_id not in self.ff_api:
            self.ff_api[user_id] = ''
        if user_id not in self.default_accounts:
            self.default_accounts[user_id] = ''
        save_session(user_id, self.ff_url[user_id], self.ff_api[user_id], self.default_accounts[user_id])

    def save_data(self, user_id):
        """
        Save FireFlyIII data for a user to the database.

        :param str user_id: The ID of the user
        """
        save_data(user_id, self.categories[user_id], self.source_accounts[user_id], self.destination_accounts[user_id], self.asset_accounts[user_id], self.expense_accounts[user_id], self.revenue_accounts[user_id], self.account_ids[user_id])

    def get_ff_data(self, user):
        """
        Fetch FireFlyIII data for a user from the FireFlyIII API.

        :param str user: The ID of the user
        """
        logger.debug(f"Fetching FireFlyIII data for user {user}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}

        def fetch_all_pages(url):
            logger.debug(f"Fetching all pages from URL: {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout).json()
            data = response['data']
            total_pages = response['meta']['pagination']['total_pages']
            for page in range(2, total_pages + 1):
                logger.debug(f"Fetching page {page} of {total_pages}")
                data += requests.get(url, headers=headers, params={"page": page}, timeout=self.timeout).json()['data']
            return data

        def extract_attributes(data, attribute_name):
            logger.debug(f"Extracting attribute '{attribute_name}' from data")
            return [item['attributes'][attribute_name] for item in data]

        try:
            categories_data = fetch_all_pages(self.ff_url[user] + 'categories')
            self.categories[user] = extract_attributes(categories_data, 'name')
            logger.debug(f"Fetched and stored categories for user {user}")

            accounts_data = fetch_all_pages(self.ff_url[user] + 'accounts')
            self.account_ids[user] = {acc['attributes']['name']: acc['id'] for acc in accounts_data}
            logger.debug(f"Fetched and stored account IDs for user {user}")

            self.source_accounts[user] = [acc['attributes']['name'] for acc in accounts_data if acc['attributes']['type'] in ['revenue', 'asset']]
            self.destination_accounts[user] = [acc['attributes']['name'] for acc in accounts_data if acc['attributes']['type'] in ['expense', 'asset']]
            self.asset_accounts[user] = [acc['attributes']['name'] for acc in accounts_data if acc['attributes']['type'] == 'asset']
            self.expense_accounts[user] = [acc['attributes']['name'] for acc in accounts_data if acc['attributes']['type'] == 'expense']
            self.revenue_accounts[user] = [acc['attributes']['name'] for acc in accounts_data if acc['attributes']['type'] == 'revenue']
            logger.debug(f"Stored account information for user {user}")

            self.save_data(user)
            logger.debug(f"Data saved for user {user}")
        except Exception as e:
            logger.error(f"Error fetching FireFlyIII data for user {user}: {e}")

    def get_category(self, category, user):
        """
        Get the category name for a user.

        :param str category: The category to retrieve
        :param str user: The ID of the user
        :raises CategoryError: If the category is not defined
        :raises StartError: If the bot is not started for the user
        :return: The category name
        :rtype: str
        """
        try:
            return self.categories[user][[slugify(i) for i in self.categories[user]].index(slugify(category))]
        except ValueError as e:
            raise CategoryError('Category not defined!') from e
        except KeyError as e:
            raise StartError('Start the bot first!') from e

    def get_source_account(self, account, user):
        """
        Get the source account name for a user.

        :param str account: The account to retrieve
        :param str user: The ID of the user
        :raises SourceError: If the source account is not defined
        :raises StartError: If the bot is not started for the user
        :return: The source account name
        :rtype: str
        """
        try:
            return self.source_accounts[user][[slugify(i) for i in self.source_accounts[user]].index(slugify(account))]
        except ValueError as e:
            raise SourceError('Source account not defined!') from e
        except KeyError as e:
            raise StartError('Start the bot first!') from e

    def get_destination_account(self, account, user):
        """
        Get the destination account name for a user.

        :param str account: The account to retrieve
        :param str user: The ID of the user
        :raises DestinationError: If the destination account is not defined
        :raises StartError: If the bot is not started for the user
        :return: The destination account name
        :rtype: str
        """
        try:
            return self.destination_accounts[user][[slugify(i) for i in self.destination_accounts[user]].index(slugify(account))]
        except ValueError as e:
            raise DestinationError('Destination account not defined!') from e
        except KeyError as e:
            raise StartError('Start the bot first!') from e

    def new_transaction(self, info, user):
        """
        Create a new transaction for a user.

        :param dict info: The transaction information
        :param str user: The ID of the user
        :return: The transaction response and ID
        :rtype: tuple
        """
        logger.info(f"Creating new transaction for user {user} with info: {info}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}
        data = {'transactions': [{'type': info['type'],
                                'amount': info['number'], 
                                'source_name': info['source'], 
                                'destination_name': info['destination'], 
                                'description': info['description'], 
                                'category_name': info['category'],
                                'date': datetime.datetime.now().isoformat()}]}
        response = requests.post(self.ff_url[user] + 'transactions', headers=headers, json=data, timeout=self.timeout)
        if response.status_code != 200:
            logger.error(f'Error creating transaction. Response: {response.json()}')
            return None
        tid = response.json()['data']['id']
        transaction = requests.get(self.ff_url[user] + 'transactions/' + tid, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        response_message = f'{float(transaction["amount"]):.2f}{transaction["currency_symbol"]} {transaction["source_name"]} → {transaction["destination_name"]} ({transaction["category_name"]})'
        return response_message, tid

    def delete_transaction(self, transaction_id, user):
        """
        Delete a transaction for a user.

        :param str transaction_id: The ID of the transaction to delete
        :param str user: The ID of the user
        """
        logger.info(f"Deleting transaction {transaction_id} for user {user}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}
        response = requests.delete(self.ff_url[user] + 'transactions/' + str(transaction_id), headers=headers, timeout=self.timeout)
        if response.status_code != 204:
            logger.error('Error deleting transaction.')
            return None
        logger.info(f'Transaction Deleted: {transaction_id}')
        return None

    def extract_info(self, input_string, user):
        """
        Extract transaction information from an input string.

        :param str input_string: The input string containing transaction details
        :param str user: The ID of the user
        :return: A dictionary with the extracted transaction information or None
        :rtype: dict or None
        """
        logger.debug(f"Extracting info from input string: {input_string}")
        pattern = re.compile(r'^([a-zA-ZÀ-ÿñÑ\s]+)\s+([0-9-.\+\*\/\(\)]+)(?:\s+([a-zA-ZÀ-ÿñÑ]+))?(?:\s+([a-zA-ZÀ-ÿñÑ]+))?(?:\s+([a-zA-ZÀ-ÿñÑ]+))?$')
        match = pattern.match(input_string)
        if match:
            description = match.group(1).strip()
            if match.group(2)[0] == '+':
                destination = self.get_destination_account(match.group(4), user) if match.group(4) is not None else self.default_accounts[user]
                source = self.get_source_account(match.group(5), user) if match.group(5) is not None else None
            else:
                source = self.get_source_account(match.group(4), user) if match.group(4) is not None else self.default_accounts[user]
                destination = self.get_destination_account(match.group(5), user) if match.group(5) is not None else None

            number = safe_math_eval(match.group(2))
            category = self.get_category(match.group(3), user) if match.group(3) is not None else None

            if source in self.asset_accounts[user] and destination not in self.asset_accounts[user]:
                kind = 'withdrawal'
            elif source not in self.asset_accounts[user] and destination in self.asset_accounts[user]:
                kind = 'deposit'
            else:
                kind = 'transfer'
            return {'description': description, 'number': number, 'category': category, 'source': source, 'destination': destination, 'type': kind}
        else:
            return None

    def get_transactions(self, user):
        """
        Get recent transactions for a user.

        :param str user: The ID of the user
        :return: A formatted string of recent transactions
        :rtype: str
        """
        logger.info(f"Getting transactions for user {user}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        transactions = requests.get(self.ff_url[user] + f'transactions?start={start_date}&end={end_date}', headers=headers, timeout=self.timeout).json()['data']
        response = ''
        for transaction in transactions[::-1]:
            t = transaction['attributes']['transactions'][0]
            response += f'``` {t["date"].split("T")[0][2:]} {t["source_name"]} → {t["destination_name"]} \n {float(t["amount"]):.2f} {t["description"]} ({t["category_name"]}) ```\n'
        return response[:-1]

    def get_balance(self, user):
        """
        Get the account balance for a user.

        :param str user: The ID of the user
        :return: A formatted string of the account balance
        :rtype: str
        """
        logger.info(f"Getting balance for user {user}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}
        total_balance = 0
        response = '```\n'
        for account in requests.get(self.ff_url[user] + 'accounts', headers=headers, timeout=self.timeout).json()['data']:
            if account['attributes']['type'] == 'asset' and account['attributes']['include_net_worth'] and account['attributes']['active']:
                balance = float(account['attributes']['current_balance'])
                total_balance += balance
                spaces = 10 - len(account['attributes']['name'])
                response += f"{account['attributes']['name']}: {' '*spaces} {balance:.2f}€\n"
        spaces = 10 - 5
        response += f'TOTAL: {" "*spaces} {total_balance:.2f}€'
        return response + '```'

    def update_transaction_category(self, transaction_id, category, user):
        """
        Update the category of a transaction for a user.

        :param str transaction_id: The ID of the transaction
        :param str category: The new category
        :param str user: The ID of the user
        :return: A formatted string of the updated transaction
        :rtype: str
        """
        logger.info(f"Updating category for transaction {transaction_id} to {category} for user {user}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}
        transaction = requests.get(self.ff_url[user] + 'transactions/' + transaction_id, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        data = {'transactions': [{'type': transaction['type'],
                                'amount': transaction['amount'], 
                                'source_name': transaction['source_name'], 
                                'destination_name': transaction['destination_name'], 
                                'description': transaction['description'], 
                                'category_name': category,
                                'date': transaction['date']}]}
        response = requests.put(self.ff_url[user] + f'transactions/{transaction_id}', headers=headers, json=data, timeout=self.timeout)
        if response.status_code != 200:
            logger.error(f'Error updating transaction category. Response: {response.json()}')
        transaction = requests.get(self.ff_url[user] + 'transactions/' + transaction_id, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        response_message = f'{float(transaction["amount"]):.2f}{transaction["currency_symbol"]} {transaction["source_name"]} → {transaction["destination_name"]} ({transaction["category_name"]})'
        return response_message

    def update_transaction_asset(self, transaction_id, asset_account, user):
        """
        Update the asset account of a transaction for a user.

        :param str transaction_id: The ID of the transaction
        :param str asset_account: The new asset account
        :param str user: The ID of the user
        :return: A formatted string of the updated transaction
        :rtype: str
        """
        logger.info(f"Updating asset account for transaction {transaction_id} to {asset_account} for user {user}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}
        transaction = requests.get(self.ff_url[user] + 'transactions/' + transaction_id, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        data = {'transactions': [{'type': transaction['type'],
                                    'amount': transaction['amount'], 
                                    'source_id': self.account_ids[user][asset_account], 
                                    'destination_id': transaction['destination_id'], 
                                    'description': transaction['description'], 
                                    'category_name': transaction['category_name'],
                                    'date': transaction['date']}]}
        response = requests.put(self.ff_url[user] + f'transactions/{transaction_id}', headers=headers, json=data, timeout=self.timeout)
        if response.status_code != 200:
            logger.error(f'Error updating transaction asset. Response: {response.json()}')
        transaction = requests.get(self.ff_url[user] + 'transactions/' + transaction_id, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        response_message = f'{float(transaction["amount"]):.2f}{transaction["currency_symbol"]} {transaction["source_name"]} → {transaction["destination_name"]} ({transaction["category_name"]})'
        return response_message

    def update_transaction_expense(self, transaction_id, expense_account, user):
        """
        Update the expense account of a transaction for a user.

        :param str transaction_id: The ID of the transaction
        :param str expense_account: The new expense account
        :param str user: The ID of the user
        :return: A formatted string of the updated transaction
        :rtype: str
        """
        logger.info(f"Updating expense account for transaction {transaction_id} to {expense_account} for user {user}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}
        transaction = requests.get(self.ff_url[user] + 'transactions/' + transaction_id, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        data = {'transactions': [{'type': transaction['type'],
                                'amount': transaction['amount'], 
                                'source_id': transaction['source_id'], 
                                'destination_id': self.account_ids[user][expense_account], 
                                'description': transaction['description'], 
                                'category_name': transaction['category_name'],
                                'date': transaction['date']}]}
        response = requests.put(self.ff_url[user] + f'transactions/{transaction_id}', headers=headers, json=data, timeout=self.timeout)
        if response.status_code != 200:
            logger.error(f'Error updating transaction expense. Response: {response.json()}')
        transaction = requests.get(self.ff_url[user] + 'transactions/' + transaction_id, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        response_message = f'{float(transaction["amount"]):.2f}{transaction["currency_symbol"]} {transaction["source_name"]} → {transaction["destination_name"]} ({transaction["category_name"]})'
        return response_message

    def update_transaction_revenue(self, transaction_id, revenue_account, user):
        """
        Update the revenue account of a transaction for a user.

        :param str transaction_id: The ID of the transaction
        :param str revenue_account: The new revenue account
        :param str user: The ID of the user
        :return: A formatted string of the updated transaction
        :rtype: str
        """
        logger.info(f"Updating revenue account for transaction {transaction_id} to {revenue_account} for user {user}")
        headers = {'Authorization': f'Bearer {self.ff_api[user]}', 'Accept': 'application/json'}
        transaction = requests.get(self.ff_url[user] + 'transactions/' + transaction_id, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        data = {'transactions': [{'type': transaction['type'],
                                'amount': transaction['amount'], 
                                'source_id': self.account_ids[user][revenue_account], 
                                'destination_id': transaction['destination_id'], 
                                'description': transaction['description'], 
                                'category_name': transaction['category_name'],
                                'date': transaction['date']}]}
        response = requests.put(self.ff_url[user] + f'transactions/{transaction_id}', headers=headers, json=data, timeout=self.timeout)
        if response.status_code != 200:
            logger.error(f'Error updating transaction revenue. Response: {response.json()}')
        transaction = requests.get(self.ff_url[user] + 'transactions/' + transaction_id, headers=headers, timeout=self.timeout).json()['data']['attributes']['transactions'][0]
        response_message = f'{float(transaction["amount"]):.2f}{transaction["currency_symbol"]} {transaction["source_name"]} → {transaction["destination_name"]} ({transaction["category_name"]})'
        return response_message
