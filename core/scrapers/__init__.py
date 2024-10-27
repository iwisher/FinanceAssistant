from .mp_crawler import mp_crawler
from .youtube_crawler import youtube_crawler
from .applepodcast_crawler import applepodcast_crawler

scraper_map = {
    'mp.weixin.qq.com': mp_crawler,
    'www.youtube.com': youtube_crawler,
    'podcasts.apple.com': applepodcast_crawler,    
}