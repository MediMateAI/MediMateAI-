import logging
import sqlite3
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from flask import Flask

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)

# Function to clear any existing webhook
def clear_webhook(token):
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    response = requests.post(url)
    if response.status_code == 200:
        print("Webhook cleared successfully.")
    else:
        print(f"Failed to clear webhook: {response.status_code}")

# Define the database for storing medication info and notes
def create_database():
    conn = sqlite3.connect('medibot.db')
    c = conn.cursor()
    
    # Create medication and notes tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS medications (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    description TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS medical_notes (
                    id INTEGER PRIMARY KEY,
                    topic TEXT,
                    content TEXT)''')
    
    conn.commit()
    conn.close()

# Fetch medication details from the database
def get_medication_info(name):
    conn = sqlite3.connect('medibot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM medications WHERE name LIKE ?", ('%' + name + '%',))
    result = c.fetchall()
    conn.close()
    return result

# Fetch medical notes from the database
def get_medical_notes(topic):
    conn = sqlite3.connect('medibot.db')
    c = conn.cursor()
    c.execute("SELECT content FROM medical_notes WHERE topic LIKE ?", ('%' + topic + '%',))
    result = c.fetchall()
    conn.close()
    return result

# Command handlers
async def start(update: Update, context: CallbackContext):
    """Handles the /start command"""
    await update.message.reply_text("Welcome to MediMateAI! Type /help for instructions.")

async def help(update: Update, context: CallbackContext):
    """Handles the /help command"""
    await update.message.reply_text(
        "I can help you with the following commands:\n"
        "/search [medication name] - Get medication details\n"
        "/notes [topic] - Get medical notes on a topic"
    )

async def search(update: Update, context: CallbackContext):
    """Handles the /search command"""
    if context.args:
        name = ' '.join(context.args)
        medication = get_medication_info(name)
        if medication:
            response = f"Medication: {medication[0][1]}\nDescription: {medication[0][2]}"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f"No information found for {name}.")
    else:
        await update.message.reply_text("Please provide a medication name after the /search command.")

async def notes(update: Update, context: CallbackContext):
    """Handles the /notes command"""
    if context.args:
        topic = ' '.join(context.args)
        notes = get_medical_notes(topic)
        if notes:
            response = f"Medical Notes on {topic}:\n"
            response += '\n'.join(note[0] for note in notes)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f"No notes found for {topic}.")
    else:
        await update.message.reply_text("Please provide a topic after the /notes command.")

# Flask route to confirm the app is running
@app.route('/')
def home():
    return "MediMateAI is running!"

# Main function to run the bot
def main():
    # Clear any existing webhooks to avoid conflicts
    token = "8026644351:AAHQxLobaOX9_a5Kt6k9k0WHX7AYVT5-c9M"
    clear_webhook(token)

    # Create database and tables
    create_database()

    # Telegram bot setup
    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))  # Ensure /start is first
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("notes", notes))

    # Start the bot in a separate thread to keep Flask running
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

# Command prompt to start both Flask and Telegram Bot
if __name__ == '__main__':
    from threading import Thread

    print("Starting MediMateAI bot...")

    # Run the Flask app in a separate thread
    flask_thread = Thread(target=lambda: app.run(debug=True, use_reloader=False))
    flask_thread.start()

    # Run the Telegram bot
    main()