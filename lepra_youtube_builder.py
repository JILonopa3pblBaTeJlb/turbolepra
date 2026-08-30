# --- START OF FILE lepra_youtube_builder.py ---
import json
import os
import random
from pathlib import Path
from lepra_logger import log_d

class YouTubePostBuilder:
    """Билдер для постов с YouTube-ссылками из общей базы без повторов для обычных лепроюзеров."""
    
    def __init__(self, txt_path: str = "youtube_links_clean.txt", history_path: str = "used_youtube_history.json"):
        self.txt_path = Path(txt_path)
        self.history_path = Path(history_path)
        self.links = []
        self.used_history = set()
        
        self._load_links()
        self._load_history()

    def _load_links(self):
        if self.txt_path.exists():
            self.links = [line.strip() for line in self.txt_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            log_d(f"YOUTUBE BUILDER: Загружено {len(self.links)} чистых ссылок на видео.")
        else:
            log_d(f"YOUTUBE BUILDER ERROR: Файл {self.txt_path} не найден!")

    def _load_history(self):
        if self.history_path.exists():
            try:
                data = json.loads(self.history_path.read_text(encoding="utf-8"))
                self.used_history = set(data)
                log_d(f"YOUTUBE BUILDER: Загружена история использованных видео ({len(self.used_history)} шт.).")
            except Exception as e:
                log_d(f"YOUTUBE BUILDER ERROR: Ошибка загрузки истории: {e}")

    def _save_history(self):
        try:
            self.history_path.write_text(json.dumps(list(self.used_history), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            log_d(f"YOUTUBE BUILDER ERROR: Ошибка сохранения истории: {e}")

    def get_fresh_link(self) -> str | None:
        if not self.links:
            return None
            
        available = [l for l in self.links if l not in self.used_history]
        if not available:
            log_d("YOUTUBE BUILDER: Все ссылки из базы исчерпаны! Сбрасываем историю использованных видео.")
            self.used_history.clear()
            available = self.links
            
        link = random.choice(available)
        self.used_history.add(link)
        self._save_history()
        return link

    def build_youtube_post(self) -> dict:
        url = self.get_fresh_link()
        if not url:
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Фоллбэк
            
        # Сопровождающие фразы отключены (текст пустой)
        return {
            "text": "",
            "media_url": url,
            "post_type": "видео",
            "quality": random.uniform(0.4, 0.9)
        }
# --- END OF FILE lepra_youtube_builder.py ---
