import requests
import re

def test_omni_live():
    url = "https://omni.se/rss/all"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        # Search for all image URLs ending in .jpg or .png or webp inside <enclosure>
        # Omni often puts them in <enclosure url="...">
        items = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
        
        found = []
        for item in items:
            if len(found) >= 3: break
            
            # Simple title find
            t_m = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
            title = t_m.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if t_m else "Titel saknas"
            
            # Omni specifically uses <enclosure url="..."/>
            i_m = re.search(r'url="(https?://.*?)"', item)
            img = i_m.group(1) if i_m else None
            
            link_m = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
            link = link_m.group(1).strip() if link_m else "#"
            
            if img:
                found.append({"title": title, "img": img, "link": link})
        
        return found
    except Exception as e:
        return f"Error: {e}"

results = test_omni_live()
if results:
    for n in results:
        print(f"📰 {n['title']}")
        print(f"📸 {n['img']}")
        print(f"🔗 {n['link']}\n")
else:
    print("Inga nyheter med bilder hittades.")
