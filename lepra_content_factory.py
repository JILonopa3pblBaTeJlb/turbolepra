# --- START OF FILE lepra_content_factory.py ---

import json
import os
import random
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional, Set, Dict, Any
from lepra_shared import GlobalState
from lepra_logger import log_d
from lepra_movie_digger import get_random_movie

STORIES_HISTORY_FILE = Path("used_stories.json")

def load_used_stories() -> Set[str]:
    """Загружает историю сигнатур уже рассказанных историй."""
    if STORIES_HISTORY_FILE.exists():
        try:
            with open(STORIES_HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            log_d(f"STORIES HISTORY ERROR: Ошибка загрузки истории: {e}")
            return set()
    return set()

def save_used_stories(stories: Set[str]) -> None:
    """Сохраняет историю сигнатур в файл (ограничиваем последними 1000 записями)."""
    try:
        history_list = list(stories)[-1000:]
        with open(STORIES_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_d(f"STORIES HISTORY ERROR: Ошибка сохранения истории: {e}")

def get_system_prompt() -> str:
    """Читает системный промпт."""
    prompt_path = Path("generic_post_prompt.txt")
    return prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "Ты — лепроюзер. Пиши неформально."

def get_random_game() -> str:
    """Загружает список игр из games.txt построчно или возвращает дефолт при отсутствии файла."""
    games_path = Path("games.txt")
    if games_path.exists():
        try:
            games = [line.strip() for line in games_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if games:
                return random.choice(games)
        except Exception as e:
            log_d(f"GAMES TXT ERROR: Ошибка чтения games.txt: {e}")
            
    # Дефолтный пул на случай, если файла еще нет
    fallback_games = ["Ведьмак 3", "Cyberpunk 2077", "Dota 2", "Fallout", "DOOM"]
    return random.choice(fallback_games)

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

def generate_post_content(u: Any, p_type: str) -> Dict[str, Any]:
  """Фабрика контента с поддержкой парсинга реальных анекдотов/историй,

  выгрузки игр из games.txt, фильмов из TMDb / movies.txt и рерайта через LLM
  с внедрением слов из vocab.json.
  """
  sys_prompt = get_system_prompt()

  if p_type == "мем":
    return {"text": "", "is_media_required": True, "target_title": None}

  random_words = GlobalState.processor.get_random_sample(
      count=random.randint(3, 7)
  )
  keyword_str = ", ".join(random_words)

  topic = "жизнь"
  if u.interests:
    topic = random.choice(list(u.interests))

  target_title = None

  # Обработка игр и кино с выделением конкретного тайтла для поисковика картинок
  if p_type == "видеоигры":
    target_title = get_random_game()
    user_prompt = (
        f"Напиши пост про видеоигру {target_title}. Используй эти слова:"
        f" {keyword_str}."
    )
  elif p_type in ["кино", "фильмы"] or topic in ["кино", "фильмы"]:
    target_title = get_random_movie()
    user_prompt = (
        f"Напиши ироничный или развернутый пост-рецензию о кинофильме"
        f" '{target_title}'. Используй эти слова: {keyword_str}."
    )
  else:
    match p_type:
      case "охуительная история":
        raw_story = fetch_anekdot_story()
        if raw_story:
          user_prompt = (
              "Перед тобой реальная жизненная история. Твоя задача — сделать её"
              " литературный рерайт в фирменном стиле сайта Лепрозорий (добавь"
              " цинизма, едкого юмора, колорита старой доброй Лепры, сделай"
              " язык сочнее и живее). Обязательно органично вплети в текст эти"
              f" слова: {keyword_str}. Вот оригинальная история для"
              f" переработки:\n\n{raw_story}"
          )
        else:
          user_prompt = (
              "Расскажи короткую забавную или абсурдную жизненную историю на"
              f" тему '{topic}'. Используй эти слова: {keyword_str}."
          )

      case "политота диванная":
        user_prompt = (
            f"Напиши ироничный пост о политике. Используй эти слова:"
            f" {keyword_str}."
        )

      case "политота ватная":
        user_prompt = (
            f"Напиши сатиричный пост на злобу дня. Используй эти слова:"
            f" {keyword_str}."
        )

      case _:
        user_prompt = (
            f"Тип контента: {p_type}. Тема: {topic}. Напиши пост в стиле Лепры."
            f" Используй эти слова: {keyword_str}."
        )

  # Ретрив-цикл: делаем до 3 попыток получить непустой текст от Олламы
  text = ""
  for attempt in range(3):
    text = GlobalState.processor.get_gpt_response(
        [], task_type="post", system_prompt=sys_prompt, user_prompt=user_prompt
    )
    if text and text.strip():
      break
    log_d(
        f"WARNING: Пустой ответ от LLM для {u.username} (попытка"
        f" {attempt + 1}/3), повторяем..."
    )

  return {
      "text": text,
      "is_media_required": False,
      "target_title": target_title,
  }

# --- END OF FILE lepra_content_factory.py ---
