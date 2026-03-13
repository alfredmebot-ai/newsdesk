import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def get_best_img(url, name):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        img_url = None
        
        if name == "Aftonbladet":
            # Look for picture source or main teaser image
            img = soup.find('img', {'class': lambda x: x and 'Teaser-image' in x})
            if not img: img = soup.find('img', src=re.compile(r'images\.aftonbladet\.se'))
            if img: img_url = img['src']
            
        elif name == "Expressen":
            img = soup.find('img', src=re.compile(r'expressen\.se.*\.jpg'))
            if img: img_url = img['src']
            
        elif name == "DN":
            img = soup.find('img', src=re.compile(r'static\.bonniernews\.se'))
            if img: img_url = img['src']
            
        elif name == "SvD":
            img = soup.find('img', src=re.compile(r'static\.svd\.se'))
            if img: img_url = img['src']

        if img_url:
            if img_url.startswith('//'): img_url = 'https:' + img_url
            r_img = requests.get(img_url, headers=headers, timeout=5)
            path = f"/root/.openclaw/workspace/privat/projects/newsdesk/final_test_{name.lower()}.jpg"
            with open(path, 'wb') as f: f.write(r_img.content)
            return path
    except: pass
    return None

results = {}
for name, url in {"Aftonbladet": "https://www.aftonbladet.se/", "Expressen": "https://www.expressen.se/", "DN": "https://www.dn.se/", "SvD": "https://www.svd.se/"}.items():
    results[name] = get_best_img(url, name)
    print(f"{name}: {results[name]}")
