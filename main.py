# main.py

import logging
import os
import traceback
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if not BOT_TOKEN:
    logger.critical("FATAL ERROR: No TELEGRAM_BOT_TOKEN found.")
    exit()

# --- YOUTUBE FUNCTIONS ---

def search_youtube(query: str) -> list | None:
    """
    Searches YouTube using a cookies file to bypass bot detection.
    """
    logger.info(f"--- Starting YouTube Search with cookies for query: '{query}' ---")
    
    search_query = f"ytsearch5:{query}"
    
    ydl_opts = {
        'ignoreerrors': True,
        'quiet': True,
        'noplaylist': True,
        'cookiefile': 'cookies.txt',  # The most important line for the fix
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
    }

    if not os.path.exists('cookies.txt'):
        logger.error("CRITICAL: cookies.txt file not found! The bot cannot authenticate and will fail.")
        return None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(search_query, download=False)

            if search_results and 'entries' in search_results and len(search_results['entries']) > 0:
                valid_entries = [entry for entry in search_results['entries'] if entry]
                logger.info(f"SUCCESS: Found {len(valid_entries)} results using cookies.")
                return [{'id': e['id'], 'title': e['title'], 'duration': e.get('duration', 0)} for e in valid_entries]
            else:
                logger.warning("FAILURE: Search with cookies returned no 'entries'. Your cookies might be expired.")
                return None
    except Exception:
        logger.error(f"CRITICAL: An exception occurred in search_youtube (with cookies).\n{traceback.format_exc()}")
        return None

def download_audio(video_id: str) -> str | None:
    """Downloads a specific YouTube video ID as an MP3, using cookies."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = f"downloads/{video_id}.%(ext)s"
    final_mp3_path = f"downloads/{video_id}.mp3"
    ffmpeg_path = "/usr/bin/ffmpeg"

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': output_template,
        'noplaylist': True,
        'ffmpeg_location': ffmpeg_path,
        'cookiefile': 'cookies.txt' # Use cookies for downloading as well
    }

    try:
        if os.path.exists(final_mp3_path): os.remove(final_mp3_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if (info.get('filesize_approx') or (info.get('duration', 0) * 24000)) > 50 * 1024 * 1024:
                return "TOO_LARGE"
            ydl.download([url])
            if os.path.exists(final_mp3_path): return final_mp3_path
            return None
    except Exception:
        logger.error(f"CRITICAL: An exception during download.\n{traceback.format_exc()}")
        return None

# --- TELEGRAM BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if os..path.exists('cookies.txt'):
        await update.message.reply_text("Bot is running with authentication cookies! Send a song name to search.")
    else:
        await update.message.reply_text("WARNING: `cookies.txt` not found. The bot will fail to search. Please upload it.")

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text
    await update.message.reply_text(f"Searching for '{query}'...")
    
    search_results = search_youtube(query)
    
    if not search_results:
        await update.message.reply_text("Sorry, I couldn't find any results. This may be due to expired cookies or YouTube blocking.")
        return

    keyboard = [[InlineKeyboardButton(f"🎵 {item['title'][:50]}... ({item['duration']//60}:{item['duration']%60:02d})", callback_data=f"download_{item['id']}")] for item in search_results]
    await update.message.reply_text("Here are the top results:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action, video_id = query.data.split('_', 1)

    if action == "download":
        await query.edit_message_text(text="Downloading...")
        path = download_audio(video_id)
        if path == "TOO_LARGE":
            await query.edit_message_text("Sorry, this song is >50MB.")
        elif path:
            await query.edit_message_text("Download complete. Sending audio...")
            try:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=open(path, 'rb'), write_timeout=60)
            finally:
                os.remove(path)
        else:
            await query.edit_message_text("Sorry, an error occurred during download.")

def main() -> None:
    if not os.path.exists("downloads"): os.makedirs("downloads")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot is starting with the final COOKIE fix... Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()
