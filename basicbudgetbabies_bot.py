import telegram
import os, datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
import gspread
from google.oauth2.service_account import Credentials

# Telegram bot token
TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Google Sheets credentials
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = os.environ.get('JSON_FILENAME')
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')

# Initialize Telegram bot
bot = telegram.Bot(token=TOKEN)

# Initialize Google Sheets client
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Function to send inline keyboard with Summation button
def send_inline_keyboard(update, context):
    keyboard = [[telegram.InlineKeyboardButton("Summation", callback_data='summation')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Expense added. Click Summation to view total expenses.', reply_markup=reply_markup)

# Handler for /expense command
def expense(update, context):
    user_id = update.effective_user.id
    expense_text = context.args

    # Parse the expense text to separate amount and description/category
    amount = None
    description = 'N.A.'
    for word in expense_text:
        if word.startswith('$'):
            amount = word
            description = ' '.join(expense_text[expense_text.index(word)+1:])
            break
        elif word.isdigit():
            amount = f'${word}'
            description = ' '.join(expense_text[expense_text.index(word)+1:])
            break
    
    # If amount is not found, assume 'N.A.' for description
    if not amount:
        description = 'N.A.'
        amount = 'N.A.'

    # Get the current month
    current_month = datetime.datetime.now().strftime("%B %Y")

    # Update spreadsheet with expense data
    sheet.append_row([user_id, amount, description, current_month])

    # Send message with inline keyboard after adding expense
    send_inline_keyboard(update, context)


# Handler for inline keyboard button
def button(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'summation':
        # Get current month
        current_month = datetime.datetime.now().strftime("%B %Y")
        # Get all expenses from the sheet
        all_values = sheet.get_all_values()
        # Filter expenses for the current month and sum them up
        total_expenses = sum(float(row[1].replace('$', '')) for row in all_values[1:] if row[3] == current_month and row[1].replace('$', '').replace('.', '').isdigit())

        #total_expenses = sum(float(row[1].replace('$', '')) for row in all_values[1:] if row[3] == current_month)  # Assuming expenses are in the second column
        query.message.reply_text(f'Total expenses for {current_month}: {total_expenses}')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("expense", expense, pass_args=True))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
