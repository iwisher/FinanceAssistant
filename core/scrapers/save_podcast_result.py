import asyncio
import sqlite3
import os
from datetime import datetime
import yt_dlp
from loguru import logger
from gemini_parse_audio import gemini_chat
from youtube_crawler import download_youtube_audio, extract_youtube_handle, youtube_crawler
import json
import unicodedata
import re
import random
import string
import pytz  # Import pytz for timezone handling


# Configure logger
logger.add(
    "log/podcast_transcript_crawler.log",  # Changed log file name
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    rotation="50 MB",
)


def create_connection():
    """Create a database connection to a SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect('db/downloads.db')
        logger.info(f"Successfully connected to database: db/downloads.db")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        if conn:
            conn.close()
        return None


"""Create a table to store podcast download logs"""  # Changed description
"""
    SELECT id, json_extract(metadata, '$.title') as title
    FROM content_downloads cd
"""


def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_url TEXT,
                video_url TEXT,  # Changed to video_url, keeping consistent with db schema
                audio_file_path TEXT,
                transcript_file_path TEXT,
                transcript_text TEXT,
                metadata JSON,
                download_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
        logger.info("Successfully created table: content_downloads")  # Changed log message
    except sqlite3.Error as e:
        logger.error(f"Error creating table: {e}")


"""Save the podcast download log to the database"""  # Changed description


def save_download_log(
    conn,
    channel_url,
    video_url,
    audio_file_path,
    transcript_file_path,
    transcript_text,
    meta_data,
):  # Keeping video_url for db consistency
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO content_downloads (channel_url, video_url, audio_file_path, transcript_file_path, transcript_text, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                channel_url,
                video_url,
                audio_file_path,
                transcript_file_path,
                transcript_text,
                meta_data,
            ),
        )  # Keeping video_url for db consistency
        conn.commit()
        logger.info(
            f"Successfully saved download log for podcast episode: {video_url}"
        )  # Changed log message
    except sqlite3.Error as e:
        logger.error(f"Error saving download log: {e}")


def normalize_title(title):
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    title = (
        title.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace('"', "")
        .replace("*", "")
        .replace("?", "")
        .replace("<", "")
        .replace(">", "")
        .replace("|", "")
    )
    title = re.sub(r"[^\x00-\x7f]", r"", title)
    return title


def generate_random_filename(length=9):
    letters = string.ascii_letters + string.digits
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


"""Downloads podcast, generates transcript and saves log to database"""  # Changed description


async def download_podcast_and_save_transcript(podcast_url, download_dir="./download"):
    conn = create_connection()
    if not conn:
        return
    create_table(conn)

    title = generate_random_filename()
    ydl_opts = {
        "format": "bestaudio/best",
        "writethumbnail": False,
        "writesubtitles": False,
        "writedescription": False,
        "outtmpl": f"{download_dir}/{title}.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "48",
            },
            {"key": "FFmpegMetadata"},
        ],
        "ignoreerrors": True,
        "continuedl": True,
        "quiet": False,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(podcast_url, download=True)
            audio_file_path = f"{download_dir}/{title}.mp3"
            transcript = gemini_chat(audio_file_path)

            transcript_file_path = os.path.join(download_dir, f"{title}.txt")

            with open(transcript_file_path, "w") as f:
                f.write(transcript)
                f.close()

            publish_date = datetime.fromtimestamp(
                info["timestamp"], tz=pytz.timezone("America/Los_Angeles")
            ).strftime("%Y-%m-%d %H:%M:%S")  # Added timezone conversion
            metadata = {
                "id": info["id"],
                "title": info["title"],
                "publish_date": publish_date,
                "description": info["description"],
                "uploader": info["uploader"],
                "uploader_url": info["uploader_url"],
                "webpage_url": info["webpage_url"],
            }
            json_string = json.dumps(metadata, indent=4)

            save_download_log(
                conn,
                podcast_url,
                podcast_url,
                audio_file_path,
                transcript_file_path,
                transcript,
                json_string,
            )
            logger.info(f"Successfully processed podcast episode: {podcast_url}")

        except Exception as e:
            error_message = f"An unexpected error occurred while downloading podcast from {podcast_url}: {e}"
            logger.error(error_message)
            error_message

        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    async def main():
        podcast_url = "https://podcasts.apple.com/us/podcast/bloomberg-surveillance/id296237493"
        await download_podcast_and_save_transcript(podcast_url)

    asyncio.run(main())
