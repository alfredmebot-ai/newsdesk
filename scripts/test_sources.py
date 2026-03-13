import requests
from bs4 import BeautifulSoup
import os

sources = {
    "Aftonbladet": "https://www.aftonbladet.se/",
    "Expressen": "https://www.expressen.se/",
    "DN": "https://www.dn.se/",
    "SvD": "https://www.svd.se/"
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def test_source(name, url):
    print(f"Testing {name}...")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for the first major image
        img_url = None
        if name == "Aftonbladet":
            # Aftonbladet uses picture tags often
            img = soup.find('img', {'src': True})
            if img: img_url = img['src']
        elif name == "Expressen":
            img = soup.find('img', {'class': lambda x: x and 'image' in x.lower()})
            if img: img_url = img['src']
        else:
            # Generic first large image hunt
            for img in soup.find_all('img'):
                if img.get('src') and 'http' in img['src'] and not 'icon' in img['src']:
                    img_url = img['src']
                    break
        
        if img_url:
            if img_url.startswith('//'): img_url = 'https:' + img_url
            print(f"FOUND IMAGE for {name}: {img_url}")
            # Try to download
            img_data = requests.get(img_url, headers=headers, timeout=5).content
            path = f"/root/.openclaw/workspace/privat/projects/newsdesk/test_{name.lower()}.jpg"
            with open(path, 'wb') as f:
                f.write(img_data)
            return path
    except Exception as e:
        print(f"Error testing {name}: {e}")
    return None

for name, url in sources.items():
    res = test_source(name, url)
