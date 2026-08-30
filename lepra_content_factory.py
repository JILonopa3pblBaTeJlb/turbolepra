# --- START OF FILE lepra_content_factory.py ---
import json
import os
import random
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional, Set
from lepra_shared import GlobalState
from lepra_logger import log_d

STORIES_HISTORY_FILE = "used_stories.json"

def load_used_stories() -> Set[str]:
    """Загружает историю сигнатур уже рассказанных историй."""
    if os.path.exists(STORIES_HISTORY_FILE):
        try:
            with open(STORIES_HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            log_d(f"STORIES HISTORY ERROR: Ошибка загрузки истории: {e}")
            return set()
    return set()

def save_used_stories(stories: Set[str]):
    """Сохраняет историю сигнатур в файл (ограничиваем последними 1000 записями)."""
    try:
        history_list = list(stories)[-1000:]
        with open(STORIES_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_d(f"STORIES HISTORY ERROR: Ошибка сохранения истории: {e}")

def get_system_prompt():
    """Читает системный промпт."""
    return Path("generic_post_prompt.txt").read_text(encoding="utf-8") if Path("generic_post_prompt.txt").exists() else "Ты — лепроюзер. Пиши неформально."

def fetch_anekdot_story() -> Optional[str]:
    """
    Парсит случайные истории с anekdot.ru, фильтрует повторы по первой строке до <br>,
    а если все доступные истории исчерпаны — сбрасывает учет.
    """
    url = "https://www.anekdot.ru/random/story/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            log_d(f"ANEKDOT ERROR: Не удалось получить страницу, статус {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        topicboxes = soup.find_all("div", class_="topicbox")
        if not topicboxes:
            topicboxes = soup.find_all("div", class_="text")
            
        stories_pool = []
        for box in topicboxes:
            text_div = box.find("div", class_="text") if box.name == "div" and "topicbox" in box.get("class", []) else box
            if text_div:
                # 1. Извлекаем сигнатуру (первая строка до первого <br>)
                br_tag = text_div.find("br")
                if br_tag:
                    sig_elements = []
                    for elem in br_tag.previous_siblings:
                        sig_elements.insert(0, elem.get_text() if hasattr(elem, 'get_text') else str(elem))
                    signature = "".join(sig_elements).strip()
                else:
                    lines = text_div.get_text().splitlines()
                    signature = lines[0].strip() if lines else ""

                # 2. Заменяем все теги <br> на переводы строк для чистого текста
                for br in text_div.find_all("br"):
                    br.replace_with("\n")
                
                raw_text = text_div.get_text()
                cleaned = "\n".join([line.strip() for line in raw_text.splitlines() if line.strip()])
                
                if cleaned and len(cleaned) > 50 and signature:
                    stories_pool.append({"signature": signature, "text": cleaned})

        if not stories_pool:
            return None

        used_stories = load_used_stories()

        # Фильтруем только те истории, которых еще не было в истории
        available_stories = [s for s in stories_pool if s["signature"] not in used_stories]

        # Если список исчерпался (все свежие истории уже были показаны), сбрасываем учет
        if not available_stories:
            log_d("STORIES HISTORY: Все истории исчерпаны, сбрасываем учет использованных историй!")
            used_stories.clear()
            available_stories = stories_pool

        # Выбираем случайную историю из доступных
        chosen = random.choice(available_stories)
        used_stories.add(chosen["signature"])
        save_used_stories(used_stories)

        log_d(f"ANEKDOT: Взята уникальная история (сигнатура: {chosen['signature'][:40]}...)")
        return chosen["text"]

    except Exception as e:
        log_d(f"ANEKDOT EXCEPTION: Ошибка при парсинге историй: {e}")
        
    return None

def generate_post_content(u, p_type) -> dict:
    """
    Фабрика контента с поддержкой парсинга реальных анекдотов/историй 
    и рерайта через LLM с внедрением слов из vocab.json.
    """
    sys_prompt = get_system_prompt()
    
    if p_type == "мем":
        return {"text": "", "is_media_required": True}
        
    random_words = GlobalState.processor.get_random_sample(count=random.randint(3, 7))
    keyword_str = ", ".join(random_words)
    
    topic = "жизнь"
    if u.interests:
        topic = random.choice(list(u.interests))
        
    if p_type == "охуительная история":
        raw_story = fetch_anekdot_story()
        if raw_story:
            user_prompt = (
                f"Перед тобой реальная жизненная история. Твоя задача — сделать её литературный рерайт "
                f"в фирменном стиле сайта Лепрозорий (добавь цинизма, едкого юмора, колорита старой доброй Лепры, "
                f"сделай язык сочнее и живее). "
                f"Обязательно органично вплети в текст эти слова: {keyword_str}. "
                f"Вот оригинальная история для переработки:\n\n{raw_story}"
            )
        else:
            user_prompt = f"Расскажи короткую забавную или абсурдную жизненную историю на тему '{topic}'. Используй эти слова: {keyword_str}."
    else:
        user_prompt = f"Тип контента: {p_type}. Тема: {topic}. Напиши пост в стиле Лепры. Используй эти слова: {keyword_str}."
        
        if p_type == "видеоигры":
            game = random.choice(["Ведьмак 3", "Cyberpunk 2077", "Dota 2", "Fallout", "DOOM"])
            user_prompt = f"Напиши пост про видеоигру {game}. Используй эти слова: {keyword_str}."
        elif p_type == "политота диванная":
            user_prompt = f"Напиши ироничный пост о политике. Используй эти слова: {keyword_str}."
        elif p_type == "политота ватная":
            user_prompt = f"Напиши сатиричный пост на злобу дня. Используй эти слова: {keyword_str}."

    text = GlobalState.processor.get_gpt_response(
        [],
        task_type="post",
        system_prompt=sys_prompt,
        user_prompt=user_prompt
    )
    
    return {"text": text, "is_media_required": False}
# --- END OF FILE lepra_content_factory.py ---
