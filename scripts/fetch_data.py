import json
import os
import requests
import re
import urllib.parse
from datetime import datetime

DATA_DIR = '/var/www/html/newsdesk/data'
IMG_DIR = os.path.join(DATA_DIR, 'images')
os.makedirs(IMG_DIR, exist_ok=True)

def get_weather():
    try:
        res = requests.get('https://api.open-meteo.com/v1/forecast?latitude=59.47&longitude=17.75&current_weather=true', timeout=5)
        return {'temp': round(res.json()['current_weather']['temperature']), 'desc': 'KUNGSÄNGEN'}
    except: return {'temp': 5, 'desc': 'KUNGSÄNGEN'}

def find_image(query):
    # Vi använder DuckDuckGo:s enkla bildsök för att hitta en passande bild
    try:
        url = f'https://duckduckgo.com/assets/logo_social.64.png' # Fallback
        search_url = f'https://duckduckgo.com/i.js?q={urllib.parse.quote(query)}&o=json'
        # Vi låtsas vara en webbläsare
        res = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        data = res.json()
        if 'results' in data and len(data['results']) > 0:
            return data['results'][0]['image']
    except: pass
    return 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=600&auto=format&fit=crop' # Nyhets-fallback

def fetch_aftonbladet_sitemap():
    items = []
    try:
        res = requests.get('https://www.aftonbladet.se/sitemaps/2026-03-articles.xml', timeout=10)
        urls = re.findall(r'<loc>(https://www.aftonbladet.se/nyheter/a/.*?)</loc>', res.text)
        for link in reversed(urls[-10:]):
            slug = link.split('/')[-1]
            title = slug.replace('-', ' ').title()
            
            # NU ANVÄNDER VI DIN IDÉ: Sök efter en bild baserat på titeln!
            img_url = find_image(title + ' nyheter')
            
            # Försök ladda ner bilden lokalt via vår proxy-metod (vi använder wsrv.nl som tvättar bilden)
            local_fn = f'news_{slug[:20]}.jpg'
            local_path = os.path.join(IMG_DIR, local_fn)
            proxy_url = f'https://wsrv.nl/?url={img_url}&w=600&h=400&fit=cover'
            
            final_img = ''
            try:
                img_res = requests.get(proxy_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                if img_res.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(img_res.content)
                    final_img = f'data/images/{local_fn}'
            except: pass

            items.append({
                'title': title,
                'desc': 'SENASTE NYTT FRÅN SVERIGE OCH VÄRLDEN.',
                'source': 'NYHETSDESK',
                'image': final_img or img_url,
                'url': link
            })
    except Exception as e: print(f'Error: {e}')
    return items

def run():
    print('Updating with SMART IMAGE SEARCH...')
    news = fetch_aftonbladet_sitemap()
    data = {'weather': {'now': get_weather()}, 'news': news}
    with open(os.path.join(DATA_DIR, 'newsdesk.json'), 'w') as f:
        json.dump(data, f, indent=4)
    print('Done!')

if __name__ == '__main__':
    run()
