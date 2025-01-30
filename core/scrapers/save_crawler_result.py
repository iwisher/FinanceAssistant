import asyncio
import sqlite3
import os
from datetime import datetime
import yt_dlp
from loguru import logger
from gemini_parse_audio import gemini_chat
from youtube_crawler import download_youtube_audio, extract_youtube_handle, youtube_crawler
import json
import whisper
import torch

# Configure logger
logger.add(
    "crawler.log",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    rotation="10 MB",
)


def create_connection():
    """ Create a database connection to a SQLite database """
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


""" Create a table to store youtube download logs """
"""
    SELECT id, json_extract(metadata, '$.title') as title
    FROM content_downloads cd 
"""


def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_url TEXT,
                video_url TEXT,
                audio_file_path TEXT,
                transcript_file_path TEXT,
                transcript_text TEXT,
                metadata JSON,
                download_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("Successfully created table: youtube_downloads")
    except sqlite3.Error as e:
        logger.error(f"Error creating table: {e}")


""" Save the youtube download log to the database """


def save_download_log(conn, channel_url, video_url, audio_file_path, transcript_file_path, transcript_text, meta_data):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO content_downloads (channel_url, video_url, audio_file_path, transcript_file_path, transcript_text, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (channel_url, video_url, audio_file_path, transcript_file_path, transcript_text, meta_data))
        conn.commit()
        logger.info(f"Successfully saved download log for video: {video_url}")
    except sqlite3.Error as e:
        logger.error(f"Error saving download log: {e}")


""" Download youtube video, generate transcript and save log to database """


async def download_playlist(playlist_url, download_dir='./download'):

    # use yt_dlp to download playlist's new vidoe, https://www.youtube.com/playlist?list=PL4i4RQ_PMSj6hx81G5R1in4M9oc7Iwqgb

    conn = create_connection()
    if not conn:
        return
    create_table(conn)

    # load whisper model
    # You can choose different models like "small", "medium", "large" for different accuracy/speed tradeoffs
    device = torch.device(
        'cuda') if torch.cuda.is_available() else torch.device('cpu')
    whsiper_model = whisper.load_model("base", device=device)
    print("Whisper model loaded.")

    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        ydl_opts = {
            'noplaylist': False,
            'download_archive': os.path.join(download_dir, 'download_archive.log'),
            'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
            'format': 'bestaudio/best',
            'embedthumbnail': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '48',  # 64
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(
                    playlist_url, download=False)  # Extract info first
                entries = info_dict.get('entries', [])
                total_videos = len(entries)
                logger.info(f"Found {total_videos} videos in the playlist.")

                for i, entry in enumerate(entries):
                    try:
                        if entry is None:
                            continue

                        logger.info(
                            f"Downloading video {i+1} of {total_videos}: {entry['title']}")
                        # Download each video individually
                        d_info = ydl.extract_info(
                            entry['webpage_url'], download=True)
                        # entry['title']
                        logger.info(f"Downloaded Title: {entry['title']}")
                        logger.info(f"Video Tags: {entry['tags']}")
                        logger.info(f"Video Categories: {entry['categories']}")
                        logger.info(
                            f"Video Descriptions: {entry['description']}")
                        logger.info(f"Video Channel ID: {entry['channel_id']}")

                        metadata = {
                            "id": entry['id'],
                            "title": entry['title'],
                            "tags": str(entry['tags']),
                            "categories": str(entry['categories']),
                            "descriptions": str(entry['description']),
                            "channel_id": entry['channel_id'],
                        }

                        # json_string = json.dumps(metadata, indent=4)

                        json_string = json.dumps(
                            ydl.sanitize_info(d_info), indent=3)

                        audio_file_path = os.path.join(
                            download_dir, f"{entry['id']}.mp3")

                        # transcript = gemini_chat(audio_file_path)
                        transcript = whsiper_model.transcribe()['text']

                        transcript_file_path = os.path.join(
                            download_dir, f"{entry['id']}.txt")

                        with open(transcript_file_path, "w") as f:
                            f.write(transcript)
                            f.close()

                        save_download_log(
                            conn, playlist_url, entry['webpage_url'], audio_file_path, transcript_file_path, transcript, json_string)
                        logger.info(
                            f"Successfully processed youtube video: {entry['webpage_url']}")

                    except yt_dlp.utils.DownloadError as e:
                        error_message = f"Error downloading {entry.get('title', 'a video')}: {e}"
                        logger.error(error_message)  # Print to console
                        error_message  # Yield the error message
                    except Exception as e:
                        error_message = f"An unexpected error occurred while downloading {entry.get('title', 'a video')}: {e}"
                        logger.error(error_message)
                        error_message

            except yt_dlp.utils.DownloadError as e:
                f"Error with playlist URL: {e}"
            except Exception as e:
                f"An unexpected error occurred: {e}"

    except Exception as e:
        logger.error(f"Error processing playlist video: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    async def main():
        url = "https://www.youtube.com/playlist?list=PL4i4RQ_PMSj6hx81G5R1in4M9oc7Iwqgb"
        await download_playlist(url)
    asyncio.run(main())
