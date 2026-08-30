import json
import os
import requests
from ddgs import DDGS
from lepra_logger import log_d

KDPV_HISTORY_FILE = "used_kdpv_urls.json"

def load_used_urls():
    if os.path.exists(KDPV_HISTORY_FILE):
        with open(KDPV_HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_used_urls(used_urls):
    with open(KDPV_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(used_urls), f, indent=2)

def is_image_reachable(url: str) -> bool:
    """Проверяет, открывается ли картинка HEAD-запросом и является ли она картинкой."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.head(url, headers=headers, timeout=3, allow_redirects=True)
        
        if response.status_code != 200:
            return False
            
        # Проверяем, что контент-тайп — это изображение
        content_type = response.headers.get('Content-Type', '').lower()
        return content_type.startswith('image/')
        
    except Exception:
        return False

def get_kdpv_image(query: str):
    """Ищет картинку, проверяет её доступность и исключает использованные."""
    used = load_used_urls()
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=10))
            
            for res in results:
                image_url = res.get('image')
                if image_url and image_url not in used:
                    if is_image_reachable(image_url):
                        used.add(image_url)
                        save_used_urls(used)
                        return image_url
                    else:
                        log_d(f"[IMAGE CHECK] Ссылка недоступна или не картинка: {image_url}")
                    
    except Exception as e:
        log_d(f"[IMAGE SEARCH ERROR] '{query}': {e}")
    return None
