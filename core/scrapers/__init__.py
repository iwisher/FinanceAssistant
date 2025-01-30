from .mp_crawler import mp_crawler
from .youtube_crawler import youtube_crawler
from .youtbue_podcast_crawler import applepodcast_crawler
from .gemini_parse_audio import gemini_chat
from .youtube_crawler import download_youtube_audio, extract_youtube_handle

scraper_map = {
    'mp.weixin.qq.com': mp_crawler,
    'www.youtube.com': youtube_crawler,
    'podcasts.apple.com': youtbue_podcast_crawler,    
}