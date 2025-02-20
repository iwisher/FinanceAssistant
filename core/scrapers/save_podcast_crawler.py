# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.abspath("./"))



from typing import Union
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import asyncio
from loguru import logger

import os
import yt_dlp
from save_crawler_result import save_download_log, create_connection
from core.utils.utils import get_whisper
from core.utils.db import create_connection, create_table, save_download_log, extract_metadata


# Configure logger
logger.add(
    "log/crawler.log",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    rotation="10 MB",
)

'''
def fetch_with_selenium(url):
    # TODO remove the default value before checkin
    user_profile = os.environ.get(
        'CHROME_USER_PROFILE','/home/rongsong/.config/google-chrome/Default')
    options = Options()
    options.add_argument(f"user-data-dir={user_profile}")
    # Use '--headless' for older Chrome versions
    options.add_argument('--headless=new')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")



    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        # Equals to  document.getElementById('content')
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "scrollable-page")))
        return driver.page_source
    finally:
        driver.quit()

async def applepodcast_crawler(url: str, logger) -> tuple[int, Union[set, dict]]:
    if not url.startswith('https://podcasts.apple.com/'):
        logger.warning(
            f'{url} is not a apple podcast url, you should not use this function')
        return -5, {}


    async with httpx.AsyncClient() as client:
        for retry in range(2):
            try:
                response = fetch_with_selenium(url)
                soup = BeautifulSoup(response, 'html.parser')
                break
            except Exception as e:
                if retry < 1:
                    logger.info(f"{e}\nwaiting 1min")
                    await asyncio.sleep(60)
                else:
                    logger.warning(e)
                    return -7, {}


        podcast_links = soup.find_all('a', class_='link-action')

        podcasts = []
        for link in podcast_links:
            podcast_link = link.get('href').strip()
            if podcast_link == url:
                continue
            if podcast_link:
                title = link.get('title') or link.text.strip()
                desc = link.get('aria-label')
                podcasts.append({
                    'title': title,
                    'url': podcast_link,
                    'desc': desc,
                })

        if not podcasts:
            return -1, {}

        return podcasts


def normalize_title(title):
    title = unicodedata.normalize('NFKD', title).encode(
        'ascii', 'ignore').decode('ascii')
    title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '').replace('*', '').replace('?',
                                                                                                                   '').replace(
        '<', '').replace('>', '').replace('|', '')
    title = re.sub(r'[^\x00-\x7f]', r'', title)
    return title

def generate_random_filename(length=9):
  letters = string.ascii_letters + string.digits
  result_str = ''.join(random.choice(letters) for i in range(length))
  return result_str
'''

# TODO Get cookie from browser
# ref: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp


async def download_podcast(url, download_dir='./download'):
    # title = normalize_title(title) if title is not None else generate_random_filename()
    ydl_opts = {
        'noplaylist': False,
        'extractaudio': True,       # Only extract audio
        'download_archive': os.path.join(download_dir, 'podcast_download_archive.log'),
        'playlistend': 300,
        # Prioritize MP3 audio if availables
        'format': 'bestaudio/best[acodec=mp3]',
        'writethumbnail': False,
        'writesubtitles': False,
        'writedescription': False,
        'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '48',
        }, {
            'key': 'FFmpegMetadata',
        }],
        'ignoreerrors': True,
        'continuedl': True,
        'quiet': False,
        'no_warnings': False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(
            url, download=False)  # Extract info first
        entries = info_dict.get('entries', [])
        total_podcast = len(entries)
        logger.info(f"Found {total_podcast} podcasts in the playlist.")

        # load whisper model
        whsiper_model = get_whisper()

        print("Whisper model loaded.")

        for i, entry in enumerate(entries):
            try:
                if entry is None:
                    continue

                logger.info(
                    f"Downloading video {i+1} of {len(entries)}: {entry['title']}")

                json_string, original_time = extract_metadata(
                    ydl, entry)
                

                audio_file_path = os.path.join(
                    download_dir, f"{entry['id']}.mp3")

                # transcript = gemini_chat(audio_file_path)
                transcript = whsiper_model.transcribe(audio_file_path)['text']

                transcript_file_path = os.path.join(
                    download_dir, f"{entry['id']}.txt")

                with open(file=transcript_file_path, mode="w", encoding="UTF-8") as f:
                    f.write(transcript)
                    f.close()

                conn = create_connection()

                save_download_log(
                    conn, url, entry['webpage_url'], audio_file_path, transcript_file_path, transcript, json_string, original_time)
                logger.info(
                    f"Successfully processed youtube video: {entry['webpage_url']}")

            except yt_dlp.utils.DownloadError as e:
                error_message = f"Error downloading {entry.get('title', 'a podcast')}: {e}"
                logger.error(error_message)  # Print to console
                error_message  # Yield the error message
            except Exception as e:
                error_message = f"An unexpected error occurred while downloading {entry.get('title', 'a podcast')}: {e}"
                logger.error(error_message)
                error_message


if __name__ == '__main__':

    url = "https://www.youtube.com/playlist?list=PLoYXhWL_Ra8VTl7OvaH1imyfBletgmz0L"
    # Yahoo stocks in translation
    url = "https://www.youtube.com/playlist?list=PLx28zU8ctIRr6cdseGsQLidX7r0Jq44td"
    # channel_name = 'bloomberg-surveillance'

    async def main():
        result = await download_podcast(url)

    asyncio.run(main())
