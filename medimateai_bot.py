from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Use your bot token here
TOKEN = "7936422196:AAHT-0KhkrKpACritjzhnToGaXAFWTCeS4s"

# Start function to send a welcome message when a user starts the bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! I am MediMateAI, your pharmaceutical assistant.")

# Function to handle the /help command
def help(update: Update, context: CallbackContext):
    update.message.reply_text("Use /search [medication_name] to get information about a drug.\nUse /notes [topic] to get medical notes.")

# Function to handle the /search command for medications
def search(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Please provide a medication name to search for.")
        return

    medication_name = " ".join(context.args)  # Join the medication name
    # Here, you can implement the logic to search the medication's information
    update.message.reply_text(f"Searching information for: {medication_name}")

# Function to handle the /notes command for medical notes
def notes(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Please provide a topic to search for medical notes.")
        return

    topic = " ".join(context.args)  # Join the topic name
    # Here, you can implement the logic to fetch medical notes related to the topic
    update.message.reply_text(f"Fetching medical notes for: {topic}")

def main():
    # Set up the Updater and dispatcher
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Add handlers for the commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("search", search))
    dispatcher.add_handler(CommandHandler("notes", notes))

    # Start polling and keep the bot running
    updater.start_polling()
    print("Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()