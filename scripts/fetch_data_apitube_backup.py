# BACKUP: Newsdesk Fetch Data Script
# Provider: APITube.io
# API Key: api_live_IwXRgSchCxnO3GxwhQ6xSASdqTEaMTePLzOmAUL46zjC1Q8xxkS3F
# Saved: 2026-03-01

import requests
import json
import re
import os
import shutil
from datetime import datetime

# CONFIG
API_KEY = 'api_live_IwXRgSchCxnO3GxwhQ6xSASdqTEaMTePLzOmAUL46zjC1Q8xxkS3F'
DATA_DIR = '/root/.openclaw/workspace/privat/projects/newsdesk/data'
IMG_DIR = os.path.join(DATA_DIR, 'images')
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def fetch_safe_news():
    news_list = []
    if os.path.exists(IMG_DIR): shutil.rmtree(IMG_DIR)
    os.makedirs(IMG_DIR, exist_ok=True)
    try:
        url_se = f'https://api.apitube.io/v1/news?api_key={API_KEY}&country=se&language=sv&limit=10'
        articles = requests.get(url_se, timeout=10).json().get('results', [])
        for art in articles:
            if len(news_list) >= 3: break
            img_url = art.get('image_url')
            if img_url:
                local_fn = f"news_{1 + len(news_list)}.jpg"
                with open(os.path.join(IMG_DIR, local_fn), 'wb') as f: f.write(requests.get(img_url, headers=HEADERS).content)
                news_list.append({"title": art.get('title'), "desc": str(art.get('description'))[:85], "source": "SVERIGE", "image": f"data/images/{local_fn}", "url": art.get('url')})
    except: pass
    try:
        r = requests.get('http://feeds.bbci.co.uk/news/world/rss.xml', headers=HEADERS, timeout=10)
        matches = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)[:10]
        for m in matches:
            if len(news_list) >= 6: break
            img_match = re.search(r'url="(https?://.*?\.jpg.*?)"', m)
            if img_match:
                local_fn = f"news_{1 + len(news_list)}.jpg"
                with open(os.path.join(IMG_DIR, local_fn), 'wb') as f: f.write(requests.get(img_match.group(1), headers=HEADERS).content)
                news_list.append({"title": "BBC NEWS", "desc": "International World News", "source": "BBC", "image": f"data/images/{local_fn}", "url": "#"})
    except: pass
    return news_list[:6]

# ... existing get_data logic would follow here for a full standalone backup ...
