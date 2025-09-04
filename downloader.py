# downloader.py

import yt_dlp
import os
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_FILE_SIZE_LIMIT = 50 * 1024 * 1024

def search_youtube(query: str) -> list | None:
    """
    Searches YouTube by forcing the query format that is known to work.
    """
    # --- THIS IS THE FINAL FIX ---
    # We are using the most basic options possible.
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'ignoreerrors': True, # Ignore non-fatal errors
    }

    # We are forcing the search string to be in the format that
    # worked on the command line, which is more reliable.
    search_query = f"ytsearch5:{query}"

    logger.info(f"Attempting to search with the string: '{search_query}'")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Pass the constructed search query directly
            search_results = ydl.extract_info(search_query, download=False)

            if search_results and 'entries' in search_results and len(search_results['entries']) > 0:
                logger.info(f"SUCCESS: Found {len(search_results['entries'])} results.")
                return [
                    {
                        'id': entry['id'],
                        'title': entry['title'],
                        'duration': entry.get('duration', 0)
                    }
                    for entry in search_results['entries'] if entry # Filter out None entries
                ]
            else:
                logger.warning(f"FAILURE: Search for '{query}' returned no results or an invalid structure.")
                return None
    except Exception:
        logger.error("CRITICAL: An exception occurred during the yt-dlp search call.")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return None

def download_audio(video_id: str) -> str | None:
    """Downloads a specific YouTube video ID as an MP3."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = f"downloads/{video_id}.%(ext)s"
    final_mp3_path = f"downloads/{video_id}.mp3"
    ffmpeg_path = "/usr/bin/ffmpeg"

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'noplaylist': True,
        'ffmpeg_location': ffmpeg_path
    }

    try:
        if os.path.exists(final_mp3_path):
            os.remove(final_mp3_path)
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            estimated_filesize = info_dict.get('filesize_approx') or (info_dict.get('duration', 0) * 192 * 1024 / 8)
            if estimated_filesize > TELEGRAM_FILE_SIZE_LIMIT:
                return "TOO_LARGE"

            ydl.download([url])
            
            if os.path.exists(final_mp3_path):
                return final_mp3_path
            return None
    except Exception:
        logger.error(f"CRITICAL: An exception occurred during download for video_id {video_id}.")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return None
