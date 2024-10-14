# -*- coding: utf-8 -*-

from typing import Union
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "content")))
        return driver.page_source
    finally:
        driver.quit()

async def youtube_crawler(url: str, logger) -> tuple[int, Union[set, dict]]:
    if not url.startswith('https://www.youtube.com/@') and not url.startswith('http://www.youtube.com/@'):
        logger.warning(f'{url} is not a youtube channel url, you should not use this function')
        return -5, {}


    async with httpx.AsyncClient() as client:
        for retry in range(2):
            try:
                response = fetch_with_selenium(url) 
                soup = BeautifulSoup(response, 'html.parser')
                #client.get(url, headers=header, timeout=30)
                #response.raise_for_status()
                break
            except Exception as e:
                if retry < 1:
                    logger.info(f"{e}\nwaiting 1min")
                    await asyncio.sleep(60)
                else:
                    logger.warning(e)
                    return -7, {}


        # Return code 1 means adding ULR to queue
        # Return code < 0 means errors
        # Return 11 means final results
        # 文章目录
        # ytv = {ytv for ytv in soup.find_all('ytd-grid-video-renderer', class_='style-scope yt-horizontal-list-renderer')}
        ytv_links = [lnk for lnk in soup.find_all('a',id='video-title-link')]
        
        #find a tag with id video-title-link
        '''
        <a id="video-title-link" class="yt-simple-endpoint focus-on-expand style-scope ytd-rich-grid-media" aria-label="美联储传声筒的最新警告！OpenAI正在分崩离析，彻底成为赚钱机器；政坛突变，日本股市又熔断了！成本一万美元，Meta公布首款天价AR眼镜 by 美投侃新闻 62,132 views 1 day ago 20 minutes" title="美联储传声筒的最新警告！OpenAI正在分崩离析，彻底成为赚钱机器；政坛突变，日本股市又熔断了！成本一万美元，Meta公布首款天价AR眼镜" href="/watch?v=R4nFt47ZSmo&amp;t=683s"><yt-formatted-string id="video-title" class="style-scope ytd-rich-grid-media">美联储传声筒的最新警告！OpenAI正在分崩离析，彻底成为赚钱机器；政坛突变，日本股市又熔断了！成本一万美元，Meta公布首款天价AR眼镜</yt-formatted-string></a>
        https://www.youtube.com/watch?v=R4nFt47ZSmo&t=683s
        '''
        expiration_days = 2
        videos = []
        for link in ytv_links:
            video_link = f"https://www.youtube.com{link.get('href')}"
            desc = link.get('aria-label')
            title = link.get('title')
            # Get the original release date first
            ago = extract_video_info(desc)
            if ago is not None:
                days = int(ago['days'])
                hours = int(ago['hours'])
                minutes = int(ago['minutes'])
                publish_time = datetime.now() - timedelta(days=days,hours=hours, minutes=minutes)
            else:
                #datetime.strftime(datetime.today(), "%Y%m%d")
                publish_time = datetime.now() #- timedelta(days=expiration_days)
            
            videos.append({
                'title': title,
                'url': video_link,
                'desc': desc,
                'publish_time': publish_time
            })

        # Sort videos by publish_time in descending order
        videos.sort(key=lambda x: x['publish_time'], reverse=True)
        
        #print(videos)
        
        # TODO filter video longer than 1 days
        # TODO parsing the video transcript and merge the same channels together
        
        # return 13 as video, videos
        return 13, videos[0]
    

'''
The main issue with the provided code is that the `youtube_crawler` function is an asynchronous function, but it is being called in a synchronous manner. To fix this, we need to use the `asyncio` library to run the asynchronous function.

Here's the rewritten code:
'''
import asyncio

def normalize_title(title):
    # Normalize the string to 'NFKD' form and encode to 'ascii' ignoring non-ascii characters
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '').replace('*', '').replace('?',
                                                                                                                   '').replace(
        '<', '').replace('>', '').replace('|', '')
    # remove the non-ascii code in title
    title = re.sub(r'[^\x00-\x7f]', r'', title)                                                                                                               
    return title

def generate_random_filename(length=9):
  """
  Generates a random filename with the specified length and extension.

  Args:
    length: The desired length of the filename (excluding extension).
    extension: The file extension (e.g., ".txt", ".pdf"). 
              Include the leading dot.

  Returns:
    A random filename string.
  """
  letters = string.ascii_letters + string.digits  # Alphanumeric characters
  result_str = ''.join(random.choice(letters) for i in range(length))
  return result_str

def download_youtube_video(url, title=None,output_path=None):
  """
  Downloads a YouTube video using yt-dlp.

  Args:
      url: The URL of the YouTube video.
      output_path: (Optional) The directory to save the video. 
                   Defaults to the current working directory.
    """
  title = normalize_title(title) if title is not None else generate_random_filename()
  ydl_opts = {
        'format': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[ext=mp4]/best', # Download best MP4, or best quality if MP4 not available
        'merge_output_format': 'mp4',
        'outtmpl': f'{title}.%(ext)s' if output_path is None else f'{output_path}/{title}.%(ext)s',  # Output file name template
    }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            video_title = info['title']
            print(f"Successfully downloaded: {video_title}")
            return f'{title}.mp4' if output_path is None else f'{output_path}/{title}.mp4'
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None
        
        
def download_youtube_audio(url, title=None, output_path=None):
  """
  Downloads a YouTube video using yt-dlp.

  Args:
      url: The URL of the YouTube video.
      output_path: (Optional) The directory to save the video. 
                   Defaults to the current working directory.
    """
  title = normalize_title(title) if title is not None else generate_random_filename()
  ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '48', #64
        }],
        'outtmpl': f'{title}.%(ext)s' if output_path is None else f'{output_path}/{title}.%(ext)s',
    }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
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
    #url = "https://www.youtube.com/@NaNaShuoMeiGu/videos"
    url = "https://www.youtube.com/@allin/videos"
    # res = fetch_with_selenium(url)
    # print(res)
    # bo = BeautifulSoup(res, 'html.parser')

    # print(bo)

    async def main():
        result = await youtube_crawler(url, logger)
        print(result)
        print(result[1]['url'])
        file= download_youtube_audio(result[1]['url'], result[1]['title'],'./download/')
        print(f'Download file path {file}') 

    asyncio.run(main())