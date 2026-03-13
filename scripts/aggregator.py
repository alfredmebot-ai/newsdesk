import requests
import xml.etree.ElementTree as ET
import json
import re
from collections import Counter
import urllib.parse
import time
import os
from datetime import datetime, date, timedelta
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor

DATA_DIR = '/var/www/html/newsdesk/data'
IMG_DIR = os.path.join(DATA_DIR, 'images')
os.makedirs(IMG_DIR, exist_ok=True)

FEEDS_SE = {
    'Aftonbladet': 'https://www.aftonbladet.se/rss.xml',
    'Expressen': 'https://www.expressen.se/rss/nyheter/',
    'DN': 'https://www.dn.se/nyheter/rss/',
    'SvD': 'https://www.svd.se/?service=rss',
    'SVT': 'https://www.svt.se/nyheter/rss.xml'
}

FEEDS_INT = {
    'BBC': 'http://feeds.bbci.co.uk/news/rss.xml',
    'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    'CNN': 'http://rss.cnn.com/rss/edition.rss'
}

SPORT_KEYWORDS = {'sport', 'fotboll', 'hockey', 'match', 'vinst', 'curling',
                  'os-guld', 'cup', 'league', 'football', 'soccer',
                  'skidskytte', 'slalom', 'allsvenskan', 'premier league'}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
FALLBACK_IMG = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800'

def clean_html(h):
    if not h: return ''
    return re.sub('<.*?>', '', h).strip()

def extract_img_from_html(html_str):
    if not html_str: return None
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_str)
    if m:
        url = m.group(1)
        if 'bonniernews.se' in url:
            url = re.sub(r'/\d+@\d+\.', '/1200@70.', url)
        return url
    return None

def fetch_og_image(article_url):
    try:
        r = requests.get(article_url, headers=HEADERS, timeout=5)
        m = re.search(r'og:image["\s]+content="([^"]+)"', r.text)
        return m.group(1) if m else None
    except: return None

def download_image(img_url, article_id):
    try:
        r = requests.get(img_url, headers=HEADERS, timeout=10)
        content_type = r.headers.get('content-type', '')
        is_image = 'image' in content_type or r.content[:3] in [b'\xff\xd8\xff', b'\x89PN', b'GIF8']
        if len(r.content) > 5000 and is_image:
            fn = 'img_{}.jpg'.format(article_id)
            path = os.path.join(IMG_DIR, fn)
            with open(path, 'wb') as f:
                f.write(r.content)
            return 'data/images/' + fn
    except: return None

def get_best_image(title, article_url, rss_desc_raw, article_id):
    # RSS image
    img = extract_img_from_html(rss_desc_raw)
    if img:
        res = download_image(img, article_id)
        if res: return res
    # OG image
    if article_url:
        img = fetch_og_image(article_url)
        if img:
            res = download_image(img, article_id)
            if res: return res
    # Bing Fallback (Search based on title)
    try:
        bing_url = 'https://www.bing.com/images/search?q={}&form=HDRSC2&first=1'.format(urllib.parse.quote(title))
        r = requests.get(bing_url, headers=HEADERS, timeout=10)
        murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?)&quot;', r.text)
        if murls:
            res = download_image(murls[0], article_id)
            if res: return res
    except: pass
    return FALLBACK_IMG

def get_weather():
    try:
        url = 'https://api.open-meteo.com/v1/forecast?latitude=59.47&longitude=17.75&current_weather=true&hourly=temperature_2m,weathercode&timezone=Europe/Stockholm&forecast_days=1'
        res = requests.get(url, timeout=10).json()
        current = res['current_weather']
        now_hour = datetime.now().hour
        h6, h12 = min(now_hour + 6, 23), min(now_hour + 12, 23)
        def code_to_icon(c):
            if c <= 1: return '\u2600\ufe0f'
            if c <= 3: return '\U0001f324\ufe0f'
            if c <= 48: return '\u2601\ufe0f'
            if c <= 67: return '\U0001f327\ufe0f'
            if c <= 77: return '\U0001f328\ufe0f'
            return '\u26c8\ufe0f'
        return {
            'now': round(current['temperature']),
            'plus6': round(res['hourly']['temperature_2m'][h6]),
            'plus12': round(res['hourly']['temperature_2m'][h12]),
            'icons': [code_to_icon(current.get('weathercode', 0)), 
                      code_to_icon(res['hourly']['weathercode'][h6]), 
                      code_to_icon(res['hourly']['weathercode'][h12])]
        }
    except: return {'now': 5, 'plus6': 6, 'plus12': 4, 'icons': ['\U0001f324\ufe0f', '\u2600\ufe0f', '\U0001f324\ufe0f']}

def get_rates():
    rates_file = os.path.join(DATA_DIR, 'rates_yesterday.json')
    try:
        res = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5).json()
        usd_sek = round(res['rates']['SEK'], 4)
        eur_sek = round(usd_sek / res['rates']['EUR'], 4)
        yesterday = {}
        if os.path.exists(rates_file):
            with open(rates_file) as f: yesterday = json.load(f)
        usd_change = round((usd_sek - yesterday.get('usd', usd_sek)) * 100)
        eur_change = round((eur_sek - yesterday.get('eur', eur_sek)) * 100)
        today = str(date.today())
        if yesterday.get('date') != today:
            with open(rates_file, 'w') as f: json.dump({'usd': usd_sek, 'eur': eur_sek, 'date': today}, f)
        return {'usd': {'val': round(usd_sek, 2), 'change_ore': usd_change}, 
                'eur': {'val': round(eur_sek, 2), 'change_ore': eur_change}}
    except: return {}

def fetch_news(feeds, prefix):
    all_items = []
    word_pool = []
    for name, url in feeds.items():
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            root = ET.fromstring(res.content)
            for item in root.findall('.//item')[:15]:
                title = item.find('title').text or ''
                if any(k in title.lower() for k in SPORT_KEYWORDS): continue
                desc_raw = item.find('description').text if item.find('description') is not None else ''
                pub = item.find('pubDate').text if item.find('pubDate') is not None else ''
                try: ts = parsedate_to_datetime(pub).timestamp()
                except: ts = 0
                kw = set(re.findall(r'\w{4,}', title.lower()))
                word_pool.extend(kw)
                all_items.append({'title': title, 'desc': clean_html(desc_raw)[:130], 'desc_raw': desc_raw, 
                                 'source': name, 'url': item.find('link').text or '#', 'keywords': kw, 'timestamp': ts})
        except: pass
    common = {w for w, c in Counter(word_pool).most_common(50) if c > 1}
    for item in all_items: item['score'] = sum(1 for k in item['keywords'] if k in common)
    all_items.sort(key=lambda x: (x['score'], x['timestamp']), reverse=True)
    selected, seen = [], []
    for item in all_items:
        if not any(len(item['keywords'] & s) >= 3 for s in seen):
            seen.append(item['keywords'])
            item['article_id'] = '{}_{}_{}'.format(prefix, datetime.now().strftime('%H%M%S'), hash(item['title']) % 1000)
            selected.append(item)
            if len(selected) >= 8: break
    def fetch_img(item): return get_best_image(item['title'], item['url'], item['desc_raw'], item['article_id'])
    with ThreadPoolExecutor(max_workers=4) as pool: images = list(pool.map(fetch_img, selected))
    final = []
    for item, img in zip(selected, images):
        final.append({
            'title': item['title'].upper(), 'desc': item['desc'] + '...', 'source': item['source'],
            'image': img or FALLBACK_IMG, 'time': datetime.fromtimestamp(item['timestamp']).strftime('%H:%M') if item['timestamp'] else '',
            'timestamp': item['timestamp'], 'url': item['url']
        })
    return final

def run():
    print('Updating Newsdesk...')
    with ThreadPoolExecutor(max_workers=2) as pool:
        se_f, int_f = pool.submit(fetch_news, FEEDS_SE, 'se'), pool.submit(fetch_news, FEEDS_INT, 'int')
        se, intl = se_f.result(), int_f.result()
    # BREAKING NEWS (Max 120 min / 2h)
    now_ts = datetime.now().timestamp()
    breaking = [n for n in (se + intl) if (now_ts - n['timestamp']) < 7200]
    breaking.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Rensa gamla bilder (behåll de senaste 50 för säkerhet/cache)
    all_imgs = [os.path.join(IMG_DIR, f) for f in os.listdir(IMG_DIR) if f.startswith('img_')]
    all_imgs.sort(key=os.path.getmtime, reverse=True)
    for old_img in all_imgs[50:]:
        try: os.remove(old_img)
        except: pass

    data = {
        'weather': get_weather(), 'rates': get_rates(), 
        'swedish': se[:6], 'international': intl[:6], 
        'breaking': breaking[:8], 'synced_at': datetime.now().strftime('%H:%M')
    }
    with open('/var/www/html/newsdesk/data/newsdesk.json', 'w') as f: json.dump(data, f, indent=2, ensure_ascii=False)
    print('Done!')

if __name__ == '__main__':
    run()
