# bot.py

import logging
import os  # <-- Import the 'os' module
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
# We no longer import from config.py
from downloader import search_youtube, download_audio

# --- THIS IS THE CRUCIAL CHANGE ---
# Load the bot token from a secure environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables. Please set it in Codespaces secrets.")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ensure the downloads directory exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message."""
    await update.message.reply_text(
        "Welcome to the Advanced Music Bot! 🎵\n\n"
        "Just send me the name of a song, and I will find it for you."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends instructions."""
    await update.message.reply_text(
        "How to use this bot:\n\n"
        "1. Type the name of a song or artist.\n"
        "2. The bot will show you the top 5 search results.\n"
        "3. Click the button for the song you want to download.\n\n"
        "Note the 50MB Telegram file size limit."
    )

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages as search queries."""
    query = update.message.text
    if not query:
        return

    await update.message.reply_text(f"Searching for '{query}'...")
    
    search_results = search_youtube(query)
    
    if not search_results:
        await update.message.reply_text("Sorry, I couldn't find any results for that query.")
        return

    keyboard = []
    for item in search_results:
        duration = f"{item['duration'] // 60}:{item['duration'] % 60:02d}"
        button_text = f"🎵 {item['title'][:50]}... ({duration})"
        callback_data = f"download_{item['id']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Here are the top results:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button clicks for song selection."""
    query = update.callback_query
    await query.answer()

    action, video_id = query.data.split('_', 1)

    if action == "download":
        await query.edit_message_text(text=f"Downloading your selection... Please wait.")

        audio_file_path = download_audio(video_id)

        if audio_file_path == "TOO_LARGE":
            await query.edit_message_text("Sorry, the audio is >50MB and cannot be sent.")
        elif audio_file_path:
            await query.edit_message_text("Download complete. Sending audio...")
            try:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=open(audio_file_path, 'rb'),
                    write_timeout=60
                )
            finally:
                os.remove(audio_file_path)
        else:
            await query.edit_message_text("Sorry, an error occurred during download.")

def main() -> None:
    """Starts the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Advanced Music Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
