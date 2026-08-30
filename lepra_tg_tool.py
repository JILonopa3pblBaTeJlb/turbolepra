# --- START OF FILE lepra_tg_tool.py ---

import json
import os
import random
import requests
from typing import Optional, Tuple, Set

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

from lepra_logger import log_d

TG_FILE = "shown_images.json"

def load_used_ids() -> Set[str]:
    """Загружает историю показанных URL картинок из файла."""
    if os.path.exists(TG_FILE):
        try:
            with open(TG_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            log_d(f"TG_TOOL ERROR: Ошибка загрузки истории: {e}")
            return set()
    return set()

def save_used_ids(used_ids: Set[str]):
    """Сохраняет историю в файл, ограничивая последние 2000 записей."""
    try:
        history_list = list(used_ids)[-2000:]
        with open(TG_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_d(f"TG_TOOL ERROR: Ошибка сохранения истории: {e}")

def get_media_url(tg_id, channel="zaboristoyeah") -> Optional[str]:
    """Заглушка обратной совместимости для старых импортов."""
    return None

def is_image_reachable(url: str) -> bool:
    """Проверяет, доступна ли ссылка и является ли она валидным изображением."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 1. Пробуем быстрый HEAD-запрос
    try:
        r = requests.head(url, headers=headers, timeout=3, allow_redirects=True)
        if r.status_code == 200:
            ct = r.headers.get("Content-Type", "").lower()
            if "image" in ct or not ct:
                return True
    except Exception:
        pass

    # 2. Если HEAD заблокирован, делаем легкий GET-запрос
    try:
        r = requests.get(url, headers=headers, timeout=4, allow_redirects=True)
        if r.status_code == 200:
            ct = r.headers.get("Content-Type", "").lower()
            if "image" in ct or not ct:
                return True
    except Exception:
        pass

    return False

def render_media_html(media_url: str) -> str:
    """Генерирует чистый HTML для отображения картинки."""
    if not media_url: 
        return ""
    return f'<img src="{media_url}" style="width: 450px; height: auto; border: 0;">'

def get_valid_image_data(channel: str = "мем", max_attempts: int = 5) -> Tuple[Optional[int], Optional[str]]:
    """
    Ищет рабочую картинку через DuckDuckGo (ddgs) с динамическим уникальным запросом 
    (комбинация шаблона и случайного слова из vocab.json симуляции), исключая дубликаты.
    """
    if DDGS is None:
        log_d("TG_TOOL ERROR: Библиотека ddgs не установлена!")
        return None, None

    used = load_used_ids()
    
    # Пытаемся взять случайное существительное из живого словаря симуляции
    random_word = ""
    try:
        from lepra_shared import GlobalState
        if hasattr(GlobalState, 'processor') and GlobalState.processor:
            sample = GlobalState.processor.get_random_sample(count=1)
            if sample:
                random_word = sample[0]
    except Exception:
        pass
        
    # Фоллбэк-набор, если процессор еще не инициализирован
    if not random_word:
        random_word = random.choice(["кот", "жизнь", "работа", "пиво", "компьютер", "студент", "аниме", "лето", "зима", "утро"])
        
    base_templates = ["мем", "смешная картинка", "жизненный мем", "ржака", "прикол", "мемасик"]
    query = f"{random.choice(base_templates)} {random_word}"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(
                query, 
                max_results=max(10, max_attempts * 3),
                safesearch="off",
                region="wt-wt",
                size="Large"
            ))
            
            for item in results:
                url = item.get("image")
                if not url or url in used:
                    continue
                
                if is_image_reachable(url):
                    used.add(url)
                    save_used_ids(used)
                    dummy_id = random.randint(100000, 999999)
                    log_d(f"TG_TOOL: Успешно найден мем по запросу '{query}': {url}")
                    return dummy_id, url
                else:
                    # Битые ссылки сразу кидаем в историю
                    used.add(url)
                    
    except Exception as e:
        log_d(f"TG_TOOL ERROR: Ошибка поиска в DDG по запросу '{query}': {e}")

    save_used_ids(used)
    return None, None
# --- END OF FILE lepra_tg_tool.py ---
