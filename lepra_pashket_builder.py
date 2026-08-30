import random
from pathlib import Path

class PashketBuilder:
    def __init__(self):
        self.urls = []
        path = Path("pashket/pashket_url_list.txt")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.urls = [line.strip() for line in f if line.strip()]
        
    def build_pashket_post(self) -> dict:
        url = random.choice(self.urls) if self.urls else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        return {
            "text": f"Друзья, послушайте мою песню\n",
            "media_url": url,
            "post_type": "музыка",
            "quality": 0.8
        }
        
    def get_pashket_comment(self) -> str:
        return random.choice(["спасибо, друг", "хорошо, друг"])
