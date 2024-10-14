from .mp_crawler import mp_crawler
from .youtube_crawler import youtube_crawler

scraper_map = {
    'mp.weixin.qq.com': mp_crawler,
    'www.youtube.com': youtube_crawler
}