import os
import subprocess
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# States
MODE, URL, NUM_CLIPS, DURATION, CUSTOM_DURATION, QUALITY, TIKTOK, TRACKING, CONFIRM = range(9)

QUALITY_MAP = {
    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
}

def get_strong_ydl_opts(quality):
    height = quality.replace("p", "")
    return {
        "format": f"bestvideo[height<={height}]+bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "merge_output_format": "mp4",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
            "Referer": "https://www.youtube.com/",
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "android", "web"],
                "player_skip": ["configs", "webpage"],
            }
        },
        "sleep_requests": 1,
        "retries": 5,
        "fragment_retries": 5,
    }

# ... (rest of the bot code remains the same, only the yt-dlp part is strengthened)

# Example usage inside the download function (you can replace the old ydl_opts with this):
# ydl_opts = get_strong_ydl_opts(quality)
