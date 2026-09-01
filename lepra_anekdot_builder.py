# --- START OF FILE lepra_anekdot_builder.py ---

import json
import random
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional, Set, Dict, Any
from lepra_logger import log_d

ANEKDOTS_HISTORY_FILE = Path("used_anekdots.json")

def load_used_anekdots() -> Set[str]:
    """Загружает единую историю сигнатур уже использованных анекдотов (для постов и комментов)."""
    if ANEKDOTS_HISTORY_FILE.exists():
        try:
            with open(ANEKDOTS_HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            log_d(f"ANEKDOTS HISTORY ERROR: Ошибка загрузки истории: {e}")
            return set()
    return set()

def save_used_anekdots(items: Set[str]) -> None:
    """Сохраняет единую историю сигнатур в файл (ограничиваем последними 2000 записями)."""
    try:
        history_list = list(items)[-2000:]
        with open(ANEKDOTS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_d(f"ANEKDOTS HISTORY ERROR: Ошибка сохранения истории: {e}")

def fetch_anekdot_from_web(url: str, log_prefix: str) -> Optional[str]:
    """
    Универсальный парсер анекдотов с anekdot.ru с единым реестром уникальности (used_anekdots.json).
    Используется и для постов, и для комментариев-анекдотов.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            log_d(f"{log_prefix} ERROR: Не удалось получить страницу, статус {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        topicboxes = soup.find_all("div", class_="topicbox")
        if not topicboxes:
            topicboxes = soup.find_all("div", class_="text")
            
        pool = []
        for box in topicboxes:
            text_div = box.find("div", class_="text") if box.name == "div" and "topicbox" in box.get("class", []) else box
            if text_div:
                # Извлекаем сигнатуру (первая строка до первого <br>)
                br_tag = text_div.find("br")
                if br_tag:
                    sig_elements = []
                    for elem in br_tag.previous_siblings:
                        sig_elements.insert(0, elem.get_text() if hasattr(elem, 'get_text') else str(elem))
                    signature = "".join(sig_elements).strip()
                else:
                    lines = text_div.get_text().splitlines()
                    signature = lines[0].strip() if lines else ""

                # Заменяем теги <br> на переводы строк для чистого текста
                for br in text_div.find_all("br"):
                    br.replace_with("\n")
                
                raw_text = text_div.get_text()
                cleaned = "\n".join([line.strip() for line in raw_text.splitlines() if line.strip()])
                
                if cleaned and len(cleaned) > 15 and signature:
                    pool.append({"signature": signature, "text": cleaned})

        if not pool:
            return None

        used_items = load_used_anekdots()
        available = [item for item in pool if item["signature"] not in used_items]

        # Если всё исчерпано — сбрасываем единый реестр
        if not available:
            log_d(f"{log_prefix} HISTORY: Единый реестр анекдотов исчерпан, сбрасываем историю!")
            used_items.clear()
            available = pool

        chosen = random.choice(available)
        used_items.add(chosen["signature"])
        save_used_anekdots(used_items)

        log_d(f"{log_prefix}: Взят уникальный анекдот из единого реестра (сигнатура: {chosen['signature'][:40]}...)")
        return chosen["text"]

    except Exception as e:
        log_d(f"{log_prefix} EXCEPTION: Ошибка при парсинге анекдотов: {e}")
        
    return None

class AnekdotBuilder:
    """Билдер для постов-анекдотов и комментариев-анекдотов, использующий единый реестр."""
    
    def __init__(self):
        self.post_url = "https://www.anekdot.ru/random/anekdot/"
        self.comment_url = "https://www.anekdot.ru/random/anekdot/"

    def build_anekdot_post(self) -> Dict[str, Any]:
        """Собирает пост с типом 'анекдоты' через общий парсер и единый реестр."""
        text = fetch_anekdot_from_web(self.post_url, "ANEKDOT_POST")
        if not text:
            text = "Шел медведь по лесу, видит — машина горит. Сел в нее и сгорел."
        
        return {
            "post_type": "анекдоты",
            "text": text,
            "quality": random.uniform(0.4, 0.9),
            "is_media_required": False
        }

    def build_anekdot_comment(self) -> str:
        """Собирает комментарий-анекдот из того же единого реестра анекдотов."""
        text = fetch_anekdot_from_web(self.comment_url, "ANEKDOT_COMMENT")
        if not text:
            text = "Колобок повесился."
        return text

# --- END OF FILE lepra_anekdot_builder.py ---
