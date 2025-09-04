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
    """Searches YouTube and returns the top 5 results."""
    
    # --- THIS IS THE FIX ---
    # We are using a minimal set of options specifically for searching,
    # removing downloader-specific options like 'format'.
    ydl_opts = {
        'default_search': 'ytsearch5',
        'quiet': True,
        'nocheckcertificate': True,  # Can help in some cloud environments
    }
    
    logger.info(f"Starting YouTube search with query: '{query}'")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # We don't need to specify ytsearch5 in the query string itself
            # when using 'default_search'
            search_results = ydl.extract_info(query, download=False)
            
            if 'entries' in search_results and len(search_results['entries']) > 0:
                logger.info(f"Found {len(search_results['entries'])} results for '{query}'")
                return [
                    {
                        'id': entry['id'],
                        'title': entry['title'],
                        'duration': entry.get('duration', 0)
                    }
                    for entry in search_results['entries']
                ]
            
            logger.warning(f"Search for '{query}' returned no entries.")
            return None
            
    except Exception as e:
        logger.error(f"An error occurred during YouTube search for query: {query}")
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
        'logger': logger,
        'ffmpeg_location': ffmpeg_path
    }

    try:
        if os.path.exists(final_mp3_path):
            os.remove(final_mp3_path)
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            
            estimated_filesize = info_dict.get('filesize_approx') or (info_dict.get('duration', 0) * 192 * 1024 / 8)
            if estimated_filesize > TELEGRAM_FILE_SIZE_LIMIT:
                logger.warning(f"Estimated file size ({estimated_filesize} bytes) exceeds limit.")
                return "TOO_LARGE"

            logger.info(f"Downloading: {info_dict.get('title')}")
            ydl.download([url])
            
            if os.path.exists(final_mp3_path):
                return final_mp3_path
            else:
                return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in download_audio for video_id {video_id}.")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return None```
  
