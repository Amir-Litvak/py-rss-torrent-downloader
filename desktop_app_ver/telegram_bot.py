import logging
import os
import datetime
import sys
from telegram import Update
from telegram.ext import filters, Application, CommandHandler, ContextTypes, MessageHandler
import asyncio


import rss_downloader

logging.basicConfig(filename=f'{os.path.dirname(os.path.abspath(__file__))}/.logs/{datetime.date.today()}.log',
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S',
                        level=logging.INFO)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("""Please choose one of the following commands:
    /start - Shows available commands.
    
    /help - Points to start function.
    
    /download - Download new items from RSS.
    
    /watchlist - See wathclist
   
    /additem - Add item to watchlist,
               must provide an item name after command.
    
    /remove - Remove item from watchlist,
               must provide an item name after command.
    
    /exit - Stops bot.""")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to see all commands this bot can execute.")

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    downloaded_item_list = rss_downloader.RSSDownloader().download()
    output = "No items"
    
    if downloaded_item_list:
        output = '\n'.join(downloaded_item_list)

    await update.message.reply_text(f"{output} Added to qBittorrent")

async def add_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    downloader = rss_downloader.RSSDownloader()
    if not context.args:
        await update.message.reply_text("Please provide an item name after /additem")
    else:
        downloader.add_item_to_watchlist(item=' '.join(context.args))
        await update.message.reply_text(f"Added {' '.join(context.args)} to watchlist")
    
async def remove_item_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    downloader = rss_downloader.RSSDownloader()
    if not context.args:
        await update.message.reply_text("Please provide an item name after /remove")
    elif downloader.remove_item_from_watchlist(item=' '.join(context.args)):
        await update.message.reply_text(f"Removed {' '.join(context.args)} from watchlist")
    else:
        await update.message.reply_text(f"{' '.join(context.args)} is not in watchlist")

async def get_wathclist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    watchlist = '\n'.join(rss_downloader.RSSDownloader().get_watchlist())
    await update.message.reply_text(f"{watchlist}")

async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sys.exit()

async def general_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am a bot. Bip boop.")

def bot():
    TOKEN = rss_downloader.RSSDownloader().get_telegram_token()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download_command))
    application.add_handler(CommandHandler("additem",add_item_command))
    application.add_handler(CommandHandler("remove",remove_item_command))
    application.add_handler(CommandHandler("watchlist",get_wathclist_command))
    application.add_handler(CommandHandler("exit", exit_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), general_text))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
   bot()