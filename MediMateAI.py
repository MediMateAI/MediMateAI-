import logging
import sqlite3
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
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

    # Create medication and notes tables with extended information
    c.execute('''CREATE TABLE IF NOT EXISTS medications (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    side_effects TEXT,
                    dosage TEXT,
                    indications TEXT,
                    contraindications TEXT,
                    pharmacokinetics TEXT,
                    interactions TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS medical_notes (
                    id INTEGER PRIMARY KEY,
                    topic TEXT,
                    content TEXT)''')

    conn.commit()
    conn.close()

# Function to fetch medication data from OpenFDA API
def fetch_medications_from_openfda():
    url = "https://api.fda.gov/drug/label.json?limit=1000"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()  # Returns the JSON data
    else:
        print(f"Error: {response.status_code}")
        return None

# Function to insert fetched medication data into the SQLite database
def insert_medications_data(data):
    conn = sqlite3.connect('medibot.db')
    c = conn.cursor()

    for medication in data['results']:  # Loop through each medication in the response
        name = medication.get('openfda', {}).get('brand_name', ['Unknown'])[0]
        description = medication.get('description', ['No description available'])[0]
        side_effects = ', '.join(medication.get('adverse_reactions', ['No side effects reported']))
        dosage = ', '.join(medication.get('dosage_and_administration', ['No dosage info available']))
        indications = ', '.join(medication.get('indications', ['No indications available']))
        contraindications = ', '.join(medication.get('contraindications', ['No contraindications available']))
        pharmacokinetics = ', '.join(medication.get('pharmacokinetics', ['No pharmacokinetics info available']))
        interactions = ', '.join(medication.get('drug_interactions', ['No interactions available']))

        # Insert the medication data into the database
        c.execute('''INSERT INTO medications (name, description, side_effects, dosage, indications, contraindications, pharmacokinetics, interactions)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                  (name, description, side_effects, dosage, indications, contraindications, pharmacokinetics, interactions))

    conn.commit()  # Commit changes to the database
    conn.close()   # Close the database connection

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
    await update.message.reply_text("Welcome to MediMateAI! Type a medication name to get details or /help for instructions.")

async def help(update: Update, context: CallbackContext):
    """Handles the /help command"""
    await update.message.reply_text(
        "I can help you with the following:\n"
        "Just type the name of a medication to get detailed information about it.\n"
        "/notes [topic] - Get medical notes on a topic"
    )

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

# Handler for any text message (search for drug info)
async def handle_message(update: Update, context: CallbackContext):
    """Handles text input as drug name query"""
    user_input = update.message.text.strip()
    medication = get_medication_info(user_input)
    if medication:
        response = f"Medication: {medication[0][1]}\nDescription: {medication[0][2]}\n"
        response += f"Side Effects: {medication[0][3]}\nDosage: {medication[0][4]}\n"
        response += f"Indications: {medication[0][5]}\nContraindications: {medication[0][6]}\n"
        response += f"Pharmacokinetics: {medication[0][7]}\nInteractions: {medication[0][8]}"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(f"No information found for {user_input}.")

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

    # Fetch medication data from OpenFDA and insert into the database
    data = fetch_medications_from_openfda()  # Fetch medication data from OpenFDA API
    if data:
        insert_medications_data(data)  # Insert data into the database
        print("Medications data inserted successfully.")
    else:
        print("Failed to fetch data from OpenFDA.")

    # Telegram bot setup
    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))  # Ensure /start is first
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("notes", notes))

    # Handler for text messages (search for drug info)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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