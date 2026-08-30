import os
import random
import json
from pathlib import Path
from lepra_tg_tool import get_media_url
from lepra_logger import log_d

class EjikPostBuilder:
    """Специализированный билдер для графомани (Ejik) с защитой от повторов."""
    
    def __init__(self, gpt_client):
        self.gpt = gpt_client
        self.folder = Path("ejik")
        self.history_file = self.folder / "used_history.json"
        self.prompt = (self.folder / "ejik_prompt.txt").read_text(encoding="utf-8") if (self.folder / "ejik_prompt.txt").exists() else "Перепиши текст."
        
        self.articles = []
        self.personal =[]
        self._load_files_correctly()
        
        # Загружаем историю использованных индексов
        self.used_history = {"articles": [], "personal":[]}
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                self.used_history = json.load(f)
        
        self.interests = ["видеоигры", "кино", "музыка", "история", "книги"]

    def _save_history(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.used_history, f)

    def _load_files_correctly(self):
        for f in self.folder.glob("*.txt"):
            if f.name.startswith("personal"):
                self.personal.append(f.read_text(encoding="utf-8"))
            elif f.stem.isdigit():
                self.articles.append(f.read_text(encoding="utf-8"))
        log_d(f"EJIK: Загружено {len(self.articles)} статей и {len(self.personal)} личных постов.")

    def _get_unique_content(self, pool, key):
        """Выбирает контент, который еще не был использован, либо сбрасывает историю."""
        available_indices = [i for i in range(len(pool)) if i not in self.used_history[key]]
        
        if not available_indices:
            self.used_history[key] =[] # Сброс
            available_indices = range(len(pool))
            
        idx = random.choice(available_indices)
        self.used_history[key].append(idx)
        self._save_history()
        return pool[idx]

    def build_ejik_post(self) -> dict:
        if not self.articles or not self.personal:
             log_d("EJIK: Внимание! Пустые списки файлов, использую дефолтный текст.")
             return {"text": "Опять перерыв в вещании.", "post_type": "обычный", "quality": 0.1}

        r = random.random()
        
        if r < 0.3:
            content = self._get_unique_content(self.articles, "articles")
            return self._process_text_post(content)
        elif r < 0.6:
            content = self._get_unique_content(self.personal, "personal")
            return self._process_text_post(content)
        elif r < 0.9:
            tg_id = random.randint(1, 185)
            url = get_media_url(tg_id, channel="dirlewangr")
            if url:
                return {"text": "", "media_url": url, "post_type": "мем", "quality": 0.1}
            else:
                return self._process_text_post("Заметка о жизни")
        else:
            topic = random.choice(self.interests)
            return self._process_interest_post(topic)

    def _process_text_post(self, text):
        combined = f"{self.prompt}\n\nТекст: {text}"
        if len(combined) > 4000:
            max_text_len = max(100, 4000 - len(self.prompt))
            text = text[:max_text_len]
        
        try:
            rewritten = self.gpt.ask(self.prompt, {"text": text})
            if rewritten and len(rewritten) > 10:
                return {"text": rewritten, "post_type": "обычный", "quality": 0.1}
        except Exception as e:
            print(f"[EJIK ERROR] Ошибка генерации: {e}")
        
        return {"text": text, "post_type": "обычный", "quality": 0.1}

    def _process_interest_post(self, topic):
        final_topic = f"Напиши пост на тему: {topic}."
        try:
            response = self.gpt.ask(self.prompt, {"topic": final_topic})
            if response and len(response) > 10:
                return {"text": response, "post_type": "обычный", "quality": 0.1}
        except Exception as e:
            print(f"[EJIK ERROR] Ошибка генерации интересов: {e}")
            
        return {"text": f"Размышления о {topic}.", "post_type": "обычный", "quality": 0.1}
