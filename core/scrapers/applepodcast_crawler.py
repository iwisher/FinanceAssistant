# -*- coding: utf-8 -*-

from typing import Union
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import pytz
import re
import asyncio
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import yt_dlp
import unicodedata
import random
import string
from utils import extract_video_info

# @TODO Read chrome profile from env variable 
def fetch_with_selenium(url):
    # TODO remove the default value before checkin
    user_profile = os.environ.get('CHROME_USER_PROFILE','/home/rsong/.var/app/com.google.Chrome/config/google-chrome/Default')
    options = Options()
    options.add_argument(f"user-data-dir={user_profile}")
    options.add_argument('--headless=new')  # Use '--headless' for older Chrome versions
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")


    
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        # Equals to  document.getElementById('content')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "scrollable-page")))
        return driver.page_source
    finally:
        driver.quit()

async def applepodcast_crawler(url: str, logger) -> tuple[int, Union[set, dict]]:
    if not url.startswith('https://podcasts.apple.com/'):
        logger.warning(f'{url} is not a apple podcast url, you should not use this function')
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

        return 13, podcasts[1] 


def normalize_title(title):
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '').replace('*', '').replace('?',
                                                                                                                   '').replace(
        '<', '').replace('>', '').replace('|', '')
    title = re.sub(r'[^\x00-\x7f]', r'', title)                                                                                                               
    return title

def generate_random_filename(length=9):
  letters = string.ascii_letters + string.digits
  result_str = ''.join(random.choice(letters) for i in range(length))
  return result_str

def download_podcast(url, title=None, output_path=None):
    title = normalize_title(title) if title is not None else generate_random_filename()
    ydl_opts = {
            'format': 'bestaudio/best',
            'writethumbnail': False,
            'writesubtitles': False,
            'writedescription': False,
            'outtmpl':f'{title}.%(ext)s' if output_path is None else f'{output_path}/{title}.%(ext)s',
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
            try:
                info = ydl.extract_info(url, download=True)
                publish_date = datetime.fromtimestamp(info['timestamp'],tz= pytz.timezone('America/Los_Angeles'))
                #.strftime('%Y-%m-%d %H:%M:%S'
                print(f'{publish_date}')
                audio_title = normalize_title(info['title'])
                print(f"Successfully downloaded: {audio_title}")
                return f'{title}.mp3' if output_path is None else f'{output_path}/{title}.mp3'
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                return None



if __name__ == '__main__':
   
    
    logger.add(
        'wiseflow.log',
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        rotation="50 MB"
    )
    url = "https://podcasts.apple.com/us/podcast/bloomberg-surveillance/id296237493"
    channel_name = 'bloomberg-surveillance'

    async def main():
        result = await applepodcast_crawler(url, logger)
        if result[0] > 0:
            podcast = result[1]
            print(f"Latest Podcast: {podcast['title']} - {podcast['url']}")
            title = channel_name+'_'+generate_random_filename()
            downloaded_file = download_podcast(podcast['url'], title, './download')
            print(f"Downloaded to: {downloaded_file}")
        else:
            print(f"Error: {result[0]}")

    asyncio.run(main())
