import sys
import os
sys.path.insert(0, os.path.abspath("./"))

from core.utils.db import create_connection, create_table, save_download_log, extract_metadata
from core.utils.utils import get_whisper
import json
from loguru import logger
import yt_dlp
from datetime import datetime
import asyncio





# from youtube_crawler import download_youtube_audio, extract_youtube_handle, youtube_crawler


# from youtube_crawler import download_youtube_audio, extract_youtube_handle, youtube_crawler


# Configure logger
logger.add(
    "log/crawler.log",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    rotation="10 MB",
)


async def download_playlist(playlist_url, download_dir='./download'):

    # use yt_dlp to download playlist's new vidoe, https://www.youtube.com/playlist?list=PL4i4RQ_PMSj6hx81G5R1in4M9oc7Iwqgb

    conn = create_connection()
    if not conn:
        return
    create_table(conn)

    # load whisper model
    whsiper_model = get_whisper()

    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        # opts link
        # https://github.com/yt-dlp/yt-dlp/blob/03c3d705778c07739e0034b51490877cffdc0983/yt_dlp/YoutubeDL.py#L187
        ydl_opts = {
            'noplaylist': False,
            'download_archive': os.path.join(download_dir, 'download_archive.log'),
            'playlistend': 300,
            # 'break_on_existing': True,
            'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
            'format': 'bestaudio/best[acodec=mp3]',
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
                        json_string, original_time = extract_metadata(
                            ydl, total_videos, i, entry)

                        audio_file_path = os.path.join(
                            download_dir, f"{entry['id']}.mp3")

                        # transcript = gemini_chat(audio_file_path)
                        transcript = whsiper_model.transcribe(
                            audio_file_path)['text']

                        transcript_file_path = os.path.join(
                            download_dir, f"{entry['id']}.txt")

                        with open(file=transcript_file_path, mode="w", encoding="UTF-8") as f:
                            f.write(transcript)
                            f.close()

                        save_download_log(
                            conn, playlist_url, entry['webpage_url'], audio_file_path, transcript_file_path, transcript, json_string, original_time)
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
        # url = "https://www.youtube.com/playlist?list=PL4i4RQ_PMSj6hx81G5R1in4M9oc7Iwqgb"
        # url = "https://www.youtube.com/@MeiTouJun/videos"
        # url = "https://www.youtube.com/@MeiTouNews/videos"
        url = "https://www.youtube.com/@JosephCarlsonShow/videos"
        await download_playlist(url)
    asyncio.run(main())
