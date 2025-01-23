import asyncio
import sqlite3
import os
from datetime import datetime
import yt_dlp
from loguru import logger
from gemini_parse_audio import gemini_chat
from youtube_crawler import download_youtube_audio, extract_youtube_handle, youtube_crawler
import json

# Configure logger
logger.add(
    "youtube_transcript_crawler.log",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    rotation="50 MB",
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
                metadata TEXT,
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
            INSERT INTO youtube_downloads (channel_url, video_url, audio_file_path, transcript_file_path, transcript_text)
            VALUES (?, ?, ?, ?, ?,?)
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
    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        ydl_opts = {
            'noplaylist': False,
            'download_archive': os.path.join(download_dir, 'download_archive.log'),
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
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
                        logger.info(
                            f"Downloading video {i+1} of {total_videos}: {entry['title']}")
                        # Download each video individually
                        d_info = ydl.download([entry['webpage_url']])
                        # entry['title']
                        logger.info(f"Downloaded Title: {entry['title']}")
                        logger.info(f"Video Tags: {entry['tags']}")
                        logger.info(f"Video Categories: {entry['categories']}")
                        logger.info(
                            f"Video Descriptions: {entry['description']}")
                        logger.info(f"Video Channel ID: {entry['channel_id']}")
                        
                        metadata = {
                            "title": entry['title'],
                            "tags":str(entry['tags']),
                            "categories": str(entry['categories']),
                            "descriptions": str(entry['description']),
                            "channel_id": entry['channel_id'],
                        }

                        json_string = json.dumps(metadata, indent=4)

                        audio_file_path = os.path.join(download_dir, f"{entry['title']}.mp3"),

                        transcript = gemini_chat(audio_file_path)

                        transcript_file_path = os.path.join(
                            download_dir, f"{entry['title']}.txt")

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
