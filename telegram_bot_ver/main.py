import logging
import os
import datetime
import sys
from telegram import Update
from telegram.ext import filters, Application, CommandHandler, ContextTypes, MessageHandler

import rss_downloader

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Enable logging
logging.basicConfig(filename=f'{os.path.dirname(os.path.abspath(__file__))}/.logs/{datetime.date.today()}.log',
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S',
                        level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("""Please choose one of the following commands:
    /start - Shows available commands.
    /help - Points to start function.
    /download - Download new items from RSS.
    /additem - Add item to watchlist,
               must provide an item name after command.
    /exit - Stops bot.""")



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to see all commands this bot can execute.")

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    downloader = rss_downloader.RSSDownloader()
    downloader.single_run()
    downloaded_item_list = downloader.get_downloaded_items()

    if not downloaded_item_list:
        downloaded_item_list = "No items"
    await update.message.reply_text(f"{downloaded_item_list} Added to qBittorrent")

async def add_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    downloader = rss_downloader.RSSDownloader()
    if not context.args:
        await update.message.reply_text("Please provide an item name after /additem")
    else:
        downloader.add_item_to_watchlist(item=' '.join(context.args))

async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sys.exit()

async def general_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am a bot. Bip boop.")

def main():
    TOKEN = rss_downloader.RSSDownloader().get_telegram_token()
    application = Application.builder().token(TOKEN).build()

    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download_command))
    application.add_handler(CommandHandler("additem",add_item_command))
    application.add_handler(CommandHandler("exit", exit_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), general_text))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == '__main__':
    main()