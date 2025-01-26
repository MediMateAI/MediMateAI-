import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request
import os
import asyncio

# Your provided Telegram Bot token
TELEGRAM_API_KEY = "8026644351:AAHQxLobaOX9_a5Kt6k9k0WHX7AYVT5-c9M"

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the Flask app
app = Flask(__name__)

# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello, welcome to MediMateAI!')

# Main function to set up the Telegram bot
async def run_telegram_bot() -> None:
    application = Application.builder().token(TELEGRAM_API_KEY).build()

    # Add the command handler for the "/start" command
    application.add_handler(CommandHandler("start", start))

    # Start the bot
    await application.run_polling()

# Flask route to handle incoming webhook requests (if any)
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    print(json_str)
    return "OK", 200

if __name__ == "__main__":
    # Start both the Flask app and the Telegram bot asynchronously
    loop = asyncio.get_event_loop