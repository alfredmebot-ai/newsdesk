import requests
import re
import xml.etree.ElementTree as ET

# CONFIG
# Denna fil är en nödbroms om GNews-trialen slutar fungera.
# Den hämtar svenska nyheter från Omni RSS utan behov av API-nyckel.
DATA_DIR = '/root/.openclaw/workspace/privat/projects/newsdesk/data'
IMG_DIR = os.path.join(DATA_DIR, 'images')
HEADERS = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'}

def fetch_omni_emergency():
    news_list = []
    url = "https://omni.se/rss/all"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        # Vi använder regex för att hitta items då Omni ibland har CDATA som bråkar med XML-parsers
        items = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
        
        for item in items:
            if len(news_list) >= 3: break
            
            title_m = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
            title = title_m.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if title_m else "Sverige Nyheter"
            
            desc_m = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
            desc = desc_m.group(1).replace('<![CDATA[', '').replace(']]>', '').strip()[:85] + "..." if desc_m else "Senaste nytt via Omni RSS."
            
            link_m = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
            url = link_m.group(1).strip() if link_m else "#"
            
            # Omni använder ofta <enclosure url="..."> för sina bilder
            img_m = re.search(r'url="(https?://.*?)"', item)
            img_url = img_m.group(1) if img_m else None
            
            if img_url:
                local_fn = f"news_emergency_{len(news_list)+1}.jpg"
                try:
                    img_data = requests.get(img_url, headers=HEADERS, timeout=5).content
                    # Notera: här skulle vi spara ner bilden om vi körde live
                    news_list.append({"title": title, "desc": desc, "source": "OMNI (RSS)", "image_url": img_url, "url": url})
                except: continue
                
        return news_list
    except Exception as e:
        print(f"OMNI Emergency Error: {e}")
        return []

# Detta är en backup-modul som fetch_data.py kan anropa om GNews returnerar 401/403 (Trial slut)
if __name__ == "__main__":
    print("Testar Omni Emergency Fetch...")
    res = fetch_omni_emergency()
    for n in res:
        print(f"[{n['source']}] {n['title']}")
