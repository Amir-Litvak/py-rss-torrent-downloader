import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import rss_downloader

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("start", callback_data="/start"),
            InlineKeyboardButton("help", callback_data="/help"),
        ],
        [InlineKeyboardButton("Option 3", callback_data="3")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please choose:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    
    await query.edit_message_text(text=f"Selected option: {query.data}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    downloader = rss_downloader.RSSDownloader()
    downloader.single_run()

    #print(f"Unpacked list: {*a,}")
    await update.message.reply_text(f"{*downloader.get_downloaded_items(),} Added to qBittorrent")





def main():
    TOKEN = rss_downloader.RSSDownloader().get_telegram_token()

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == '__main__':
    main()