# --- START OF FILE lepra_text_processor.py ---
import json
import re
import random
import signal
import time
import requests
from pathlib import Path
import pymorphy3
import g4f

from lepra_image_search import get_kdpv_image

# Устанавливаем уровень логирования для g4f
import logging
logging.getLogger("g4f").setLevel(logging.INFO)

FILES = {
    "vocab": Path("vocab.json"),
    "prompt": Path("prompt.txt"),
    "denials": Path("denials.txt"),
    "providers": Path("providerslist.txt"),
    "inactive": Path("inactive_providers.json"),
}

# Регулярка для выкусывания мета-процесса
RE_END_OF_THOUGHT = re.compile(r"End of Thought\s*\(\*?\d+(?:\.\d+)?s?\)", flags=re.IGNORECASE)

PROVIDER_COOLDOWN = 600  # 10 минут в секундах

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

class TextProcessor:
    def __init__(self):
        self.morph = pymorphy3.MorphAnalyzer()
        self.vocab_cache = self._load_initial_vocab()
        self.denials = self._load_denials() # Загружаем отказы при инициализации
        self.bypass_comments = False  # ОТКЛЮЧЕН: теперь все идет в ЛЛМ
        self.bypass_posts = False    # Для постов отключен (реальный GPT)

    def _load_initial_vocab(self):
        if FILES["vocab"].exists():
            with open(FILES["vocab"], 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_denials(self):
        """Загрузка фраз-отказов из файла."""
        if FILES["denials"].exists():
            return [line.strip().lower() for line in FILES["denials"].read_text(encoding='utf-8').splitlines() if line.strip()]
        return[]

    def _is_denial(self, text: str) -> bool:
        """Проверка, является ли текст отказом."""
        text_lower = text.lower()
        for denial in self.denials:
            if denial in text_lower:
                return True
        return False

    def _load_inactive_map(self):
        if FILES["inactive"].exists():
            with open(FILES["inactive"], 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_inactive_map(self, data):
        with open(FILES["inactive"], 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r'\s-\s', ' — ', text)
        return text.strip()

    def _clean_thought_process(self, text: str) -> str:
        """Механизм выкусывания End of Thought."""
        match = RE_END_OF_THOUGHT.search(text)
        if match:
            return text[match.end():].strip()
        return text

    def _apply_fallback_formatting(self, words_list):
        text = " ".join(words_list)
        text = self._normalize_text(text)
        choice = random.choice([0, 1, 2, 3])
        if choice == 0:
            text = text.capitalize()
            if not text.endswith('.'): text += '.'
        elif choice == 1: text = text.capitalize()
        elif choice == 2:
            if not text.endswith('.'): text += '.'
        return text

    def extract_nouns(self, text: str):
        words = re.findall(r'\b[а-яА-ЯёЁ]{2,21}\b', text)
        nouns = set()
        for word in words:
            parsed = self.morph.parse(word)
            if parsed and any('NOUN' in p.tag for p in parsed):
                nouns.add(parsed[0].normal_form.lower())
        return nouns

    def update_vocab(self, text: str):
        new_nouns = self.extract_nouns(text)
        changed = False
        for word in new_nouns:
            first = word[0]
            if first not in self.vocab_cache: self.vocab_cache[first] =[]
            if word not in self.vocab_cache[first]:
                self.vocab_cache[first].append(word)
                changed = True
        if changed:
            with open(FILES["vocab"], 'w', encoding='utf-8') as f:
                json.dump(self.vocab_cache, f, ensure_ascii=False, indent=2)
        return changed
    
    def _process_image_placeholders(self, text: str) -> str:
        """
        Ищет [текст в скобках], заменяет на <img> через поиск картинок.
        Если картинка не найдена, оставляет текст в скобках как есть.
        """
        def replace_with_image(match):
            query = match.group(1).strip()
            # Пытаемся найти картинку
            image_url = get_kdpv_image(query)
            if image_url:
                # Возвращаем HTML-тег для картинки
                return f'<img src="{image_url}" style="max-width: 500px; height: auto;">'
            # Если поиск ничего не дал, возвращаем исходный текст, чтобы не сломать логику
            return f"[{query}]"

        # Регулярка для поиска текста внутри []
        return re.sub(r'\[([^\]]+)\]', replace_with_image, text)

    def get_gpt_response(self, words_list: list, task_type="post", system_prompt=None, user_prompt=None):
        if self.bypass_comments and task_type == "comment":
            return self._apply_fallback_formatting(words_list)

        system_content = system_prompt if system_prompt else FILES['prompt'].read_text(encoding='utf-8')
        user_content = user_prompt if user_prompt else f"Текст: {' '.join(words_list)}"

        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "mannix/llama3.1-8b-abliterated",
            "system": system_content,
            "prompt": user_content,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json().get('response', '')
                if result:
                    clean_text = self._normalize_text(result.replace('"', '').replace('*', ''))
                    return self._process_image_placeholders(clean_text)
        except Exception as e:
            print(f"[OLLAMA ERROR] {e}")

        # УМНЫЙ ФОЛЛБЭК: Если LLM недоступна или молчит, берем реплику из arkhipizdrit.txt
        arh_file = Path("arkhipizdrit.txt")
        if arh_file.exists():
            try:
                lines = [line.strip() for line in arh_file.read_text(encoding="utf-8").splitlines() if line.strip()]
                if lines:
                    return random.choice(lines)
            except Exception:
                pass

        # ЗАПАСНОЙ ВАРИАНТ: Если файла нет, генерируем из vocab.json через get_random_sample
        fallback_words = words_list if words_list else self.get_random_sample(count=4)
        return self._apply_fallback_formatting(fallback_words)
    
    def ask(self, system_prompt: str, context: dict) -> str:
        text = context.get("text", context.get("topic", ""))
        return self.get_gpt_response([text], task_type="post", system_prompt=system_prompt)
        
    def get_random_sample(self, count=5):
        all_words =[w for sublist in self.vocab_cache.values() for w in sublist if len(w) > 1]
        if len(all_words) < count: return all_words
        return random.sample(all_words, count)
