# FireFlyIII Telegram Bot

This bot lets you create [FireFlyIII](https://www.firefly-iii.org/) transactions from Telegram with simple messages.

## Disclaimer
This bot has been tested with FireFlyIII v6.1.16 and may not work with other versions. Use it at your own risk.

## Prerequisites
Before setting up the bot, ensure you have:
- A FireFlyIII instance running
- A Telegram Bot token obtained through [BotFather](https://core.telegram.org/bots/tutorial#obtain-your-bot-token)

## Features
- Create transactions by sending simple messages through Telegram
- Supports expenses, revenues, and transfers
- Update and fetch transactions and balances

## Setup Instructions

### Using Docker

1. **Clone the repository:**
   ```
   git clone https://github.com/AndresRzCh/firefly-telegram-bot.git
   cd firefly-telegram-bot
   ```

2. **Create a `.env` file:**
   ```
   TELEGRAM_API_KEY=your_telegram_api_key
   DATABASE_PATH=data/firefly_bot.db
   REQUEST_TIMEOUT=10
   ```

3. **Build and run the Docker container:**
   ```
   docker build -t firefly-telegram-bot .
   docker run -d --name firefly_bot --env-file .env -v $(pwd)/data:/app/data firefly-telegram-bot
   ```

### Using Docker Compose (Recommended)

1. **Clone the repository:**
   ```
   git clone https://github.com/AndresRzCh/firefly-telegram-bot.git
   cd firefly-telegram-bot
   ```

2. **Create a `.env` file:**
   ```
   TELEGRAM_API_KEY=your_telegram_api_key
   DATABASE_PATH=data/firefly_bot.db
   REQUEST_TIMEOUT=10
   ```

3. **Run Docker Compose:**
   ```
   docker-compose up -d --build
   ```

### Manual Setup

1. **Clone the repository:**
   ```
   git clone https://github.com/AndresRzCh/firefly-telegram-bot.git
   cd firefly-telegram-bot
   ```

2. **Create and activate a Python virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install the required packages:**
   ```
   pip install -r bot/requirements.txt
   ```

4. **Create a `.env` file:**
   ```
   TELEGRAM_API_KEY=your_telegram_api_key
   DATABASE_PATH=data/firefly_bot.db
   REQUEST_TIMEOUT=10
   ```

5. **Run the bot:**
   ```
   python bot/bot.py
   ```

## Usage Instructions

### Available Commands
- **/start**: Set URL, API Key, and account.
- **/help**: Display the help message.
- **/update**: Update your FireFlyIII data.
- **/transactions**: View recent entries.
- **/balance**: Check your account balance.

### Adding Transactions
- To add an expense, send a message like:
  ```
  Description 100 [Category] [AssetAccount] [ExpenseAccount]
  ```
- To add a revenue, send a message like:
  ```
  Description +100 [Category] [AssetAccount] [RevenueAccount]
  ```
- To add a transfer, send a message like:
  ```
  100 Account1 Account2
  ```

### Complex Transactions
The numbers can be simple equations too:
```
(100 + 5) / 2 Account1 Account2
```

### Note
- The `[Category]` field is optional.
- The `[AssetAccount]` field is optional.
- The `[ExpenseAccount]` or `[RevenueAccount]` fields are required based on the type of transaction.

## Acknowledgements
This project was inspired by other existing FireFlyIII Telegram bots:
- [cyxou/firefly-iii-telegram-bot](https://github.com/cyxou/firefly-iii-telegram-bot)
- [vjFaLk/firefly-bot](https://github.com/vjFaLk/firefly-bot)
