import re
import random
import math
import sqlite3
import json
import os
import sys
import termios
import tty
import select
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Set

# --- КОНСТАНТЫ ---
MAX_COMMENTS = 5000
FEMALE_INTERESTS = ["сиське", "дизаен", "кино", "стихи", "кулинария", "книги"]

_ARH_COMMENTS = None
processor = None

INTERESTS_POOL = [
    "it", "BDSM", "сиське", "авто", "наука", "дизаен", "history", "коты", "стихи",
    "мемы", "кино", "игры", "кулинария", "геи", "кармадрочеры", "книги", "фильмы",
    "аниме", "музыка", "космос", "ремонт", "садоводство", "настолки", "вело", "ai",
    "анекдоты"
]

POST_TYPES_CONFIG = {
    "мем": {"base_quality": (0.3, 0.9), "interest": "мемы"},
    "сиське": {"base_quality": (0.8, 1), "interest": "сиське"},
    "просто красиво": {"base_quality": (0.5, 0.9), "interest": "кино"},
    "котофото": {"base_quality": (0.9, 1.0), "interest": "коты"},
    "секс": {"base_quality": (0.2, 0.8), "interest": "геи"},
    "дорогой дневничок": {"base_quality": (0.1, 0.6), "interest": "стихи"},
    "охуительная история": {"base_quality": (0.6, 1.0), "interest": "мемы"},
    "книги": {"base_quality": (0.4, 0.9), "interest": "книги"},
    "рунет": {"base_quality": (0.3, 0.7), "interest": "it"},
    "бред": {"base_quality": (0.0, 0.3), "interest": "грязь"},
    "такой бред что хорошо": {"base_quality": (0.7, 0.9), "interest": "мемы"},
    "политота диванная": {"base_quality": (0.1, 0.5), "interest": "политика"},
    "политота ватная": {"base_quality": (0.1, 0.5), "interest": "политика"},
    "пост личных челленджей": {"base_quality": (0.5, 0.8), "interest": "авто"},
    "пост полезных товаров на алиэкспресс": {"base_quality": (0.4, 0.7), "interest": "it"},
    "жалостливая просьба кинуть донатик": {"base_quality": (0.0, 0.05), "interest": "грязь"},
    "жалкие потуги": {"base_quality": (0.0, 0.3), "interest": "it"},
    "молодец": {"base_quality": (0.7, 1.0), "interest": "it"},
    "халява": {"base_quality": (0.5, 1.0), "interest": "it"},
    "поиск решения какой-то проблемы": {"base_quality": (0.3, 0.6), "interest": "it"},
    "купил мужик шляпу а она ему как раз": {"base_quality": (0.4, 0.8), "interest": "мемы"},
    "музыка": {"base_quality": (0.1, 0.9), "interest": "музыка"},
    "видеоигры": {"base_quality": (0.8, 0.9), "interest": "игры"},
    "ai": {"base_quality": (0.5, 1.0), "interest": "ai"},
    "it": {"base_quality": (0.4, 0.9), "interest": "it"},
    "вело": {"base_quality": (0.4, 0.8), "interest": "вело"},
    "авто": {"base_quality": (0.4, 0.8), "interest": "авто"},
    "космос": {"base_quality": (0.6, 1.0), "interest": "космос"},
    "наука": {"base_quality": (0.6, 1.0), "interest": "наука"},
    "кулинария": {"base_quality": (0.5, 0.9), "interest": "кулинария"},
    "ремонт": {"base_quality": (0.3, 0.7), "interest": "ремонт"},
    "видео": {"base_quality": (0.4, 0.9), "interest": "мемы"},
    "анекдоты": {"base_quality": (0.7, 0.9), "interest": "анекдоты"},
    "кино": {"base_quality": (0.2, 0.9), "interest": "кино"},
    "фильмы": {"base_quality": (0.5, 0.9), "interest": "кино"},
}

CITIES = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Владивосток", "Киев", "Минск", "Лондон"]
USER_AGENTS = ["Opera/9.20", "Mozilla/5.0 (Windows NT 5.1; rv:2.0)", "MSIE 6.0", "Firefox/2.0.0.1"]


GRAPHOMANIA_NICK_QUEUE = ["Ejik", "Nomina_Obscura", "KingOfTheDogs", "Dirlewanger", "jorik_zadunaiskiy"]

LEGENDARY_CHANCE_PER_HOUR = 1 / (16 * 365 * 24)
START_BOTS = 400
GOLDEN_THRESHOLD_PLUS = 50
GOLDEN_THRESHOLD_MINUS_LIMIT = 2
POST_CHANCE_SCALING = 0.45

def cast_vote(target_obj, voter_id: int, sign: int, weight: int):
    """
    Универсальная функция голосования.
    target_obj должен иметь атрибуты: plus, minus, rating, user_votes
    """
    if voter_id in target_obj.user_votes:
        old_sign = target_obj.user_votes[voter_id]
        if old_sign == sign: return False # Уже голосовал так же
        
        # Откат старого
        if old_sign > 0: target_obj.plus -= 1
        else: target_obj.minus -= 1
        target_obj.rating -= (old_sign * weight)
    
    # Новый голос
    if sign > 0: target_obj.plus += 1
    else: target_obj.minus -= 1
    target_obj.user_votes[voter_id] = sign
    target_obj.rating += (sign * weight)
    return True
    
def get_arkhipizdrit_comment(post_comments: List['Comment'], author_id: int) -> str:
    """Выбирает строчку из arkhipizdrit.txt или генерирует через GPT (синхронно)."""
    global _ARH_COMMENTS
    if _ARH_COMMENTS is None:
        if os.path.exists("arkhipizdrit.txt"):
            with open("arkhipizdrit.txt", "r", encoding="utf-8") as f:
                _ARH_COMMENTS =[line.strip() for line in f if line.strip()]
        else:
            _ARH_COMMENTS =[]
            
    used_texts = {c.text for c in post_comments}
    available =[c for c in _ARH_COMMENTS if c not in used_texts]
    
    if available:
        return random.choice(available)
    
    # Теперь явно указываем task_type="comment", чтобы не попадать в логику постов
    words = GlobalState.processor.get_random_sample(count=4)
    return GlobalState.processor.get_gpt_response(words, task_type="comment")
    
    
def generate_reply(text: str) -> str:
    """Генерация ответа на коммент."""
    # Очистка текста от лишнего (упрощенно)
    clean = re.sub(r'[^а-яА-ЯёЁ\s]', '', text).strip()
    if not clean: clean = "коммент"
    
    if random.random() < 0.5:
        return f"сам ты {clean}"
    else:
        return f"{clean} у тебя в жопе"
        
        



class Inbox:
    def __init__(self, name: str, primary_interest: str):
        self.name = name
        self.primary_interest = primary_interest
        self.member_ids: List[int] = []
        self.target_for_onnn: Optional[int] = None
        self.candidate_id: Optional[int] = None

class GlobalState:
    post_id_counter = 450000
    comment_id_counter = 1200000
    user_id_counter = 1
    pashkett_counter = 1
    used_nicknames: Set[str] = set()
    
    users: List['BotUser'] = []
    users_map: Dict[int, 'BotUser'] = {}
    all_posts: List['Post'] = []
    inboxes: List[Inbox] = []
    
    karma_matrix: Dict[tuple, int] = {}
    karma_cache = defaultdict(int)
    rating_cache = defaultdict(int)
    
    active_shizes = 0
    shiz_limit = 3
    
    golden_posts_count = 0
    total_invites_used = 0
    
    total_posts_ever = 0
    total_comments_ever = 0
    total_votes_ever = 0
    
    current_sim_date = datetime(2007, 1, 1, 0, 0)
    daily_journal = []
    daily_votes = {}
    
    election_history: List[dict] = []
    last_election_candidates = []
    stats_today = {"posts": 0, "comments": 0, "votes": 0, "mystuff_hits": 0}
    
    sort_mode = 0
    old_settings = None

class Comment:
    def __init__(self, author_id: int, post_id: int, text: str = "Коммент"):
        self.id = GlobalState.comment_id_counter
        GlobalState.comment_id_counter += 1
        self.author_id = author_id
        self.post_id = post_id
        self.text = text
        self.rating = 0
        self.plus = 0
        self.minus = 0
        self.user_votes = {} # Сюда будем писать {user_id: sign}
        self.voters: Set[int] = set()
        self.timestamp = GlobalState.current_sim_date
        GlobalState.total_comments_ever += 1

class Post:
    def __init__(self, author_id: int, p_type: str = "обычный"):
        self.id = GlobalState.post_id_counter
        GlobalState.post_id_counter += 1
        self.author_id = author_id
        self.post_type = p_type
        self.text = ""  # ДОБАВЛЕНО: чтобы не падал AttributeError
        self.rating = 0
        self.plus = 0
        self.minus = 0
        self.user_votes = {}
        self.is_deleted = False
        self.comments: List[Comment] = []
        self.commenters: Set[int] = set()
        self.voters: Set[int] = set()
        self.is_golden = False
        self.timestamp = GlobalState.current_sim_date
        self.last_activity = GlobalState.current_sim_date
        self.tg_id = None
        self.media_url = None
        
        self.is_legendary = False
        self.is_drama = False
        self.is_tupak = False
        
        if p_type in POST_TYPES_CONFIG:
            q_min, q_max = POST_TYPES_CONFIG[p_type]["base_quality"]
            self.quality = random.uniform(q_min, q_max)
        else:
            self.quality = random.uniform(0, 1)
            
        GlobalState.total_posts_ever += 1

class BotUser:
    def __init__(self, username=None, special_role=None, creator_id=None, gender=None):
        self.id = GlobalState.user_id_counter
        GlobalState.user_id_counter += 1
        
        # ЛОГИКА ЭНЗЕ с корректным приоритетом переданных аргументов конструктора
        if self.id == 6579:
            self.username = username if username else "enze"
            self.special_role = special_role if special_role else "королева"
            self.gender = gender if gender else "female"
        else:
            self.username = username if username else "temp"
            self.special_role = special_role
            self.gender = gender if gender else ("female" if random.random() < 0.2 else "male")
        
        # Базовая инициализация с учетом пола и креативности
        if self.gender == "female":
            self.interests = set(random.sample(INTERESTS_POOL, k=random.randint(3, 6)))
            self.interests.update(random.sample(FEMALE_INTERESTS, 2))
            self.creativity = random.uniform(0.0, 0.015)
        else:
            self.interests = set(random.sample(INTERESTS_POOL, k=random.randint(3, 6)))
            self.creativity = random.uniform(0.0, 0.75)
        
        self.inbox_ids: List[int] = []
        self.is_miner = random.random() < 0.3
        self.will_visit_today = True
        self.participated_posts: Set[int] = set()
        self.karma_worshipped_jovan = False
        self.burnout_counter = 0.0
        self.is_burned_out = False
        self.burnout_threshold = random.uniform(7, 730)
        self.is_banned_by_pg = False
        self.is_deleted = False
        self.days_since_first_post = None
        self.merjachenie_triggered = False
        
        self.is_married = False
        self.partner_id = None
        self.is_promiscuous = False
        self.pair_expiry = None
        self.secret_affair_trigger_day = None

        r = random.random()
        if r < 0.05: self.skill_type = "talented"
        elif r < 0.55: self.skill_type = "improver"
        elif r < 0.88: self.skill_type = "static"
        else: self.skill_type = "random"
        
        if creator_id and creator_id in GlobalState.users_map:
            creator = GlobalState.users_map[creator_id]
            if random.random() < 0.8:
                self.pol_x = max(0, min(1, creator.pol_x + random.uniform(-0.05, 0.05)))
                self.pol_y = max(0, min(1, creator.pol_y + random.uniform(-0.05, 0.05)))
            else:
                self.pol_x = random.uniform(0, 1)
                self.pol_y = random.uniform(0, 1)
        else:
            self.pol_x = random.uniform(0, 1)
            self.pol_y = random.uniform(0, 1)
            
        self.empathy = max(0.0, min(1.0, random.gauss(0.5, 0.15)))
        self.reactivity = random.uniform(0, 0.8)
        self.bitterness = random.uniform(0, 0.2)
        
        if random.random() < 0.7:
            self.tz_offset = random.randint(0, 9)
        else:
            rest_of_world = list(range(-12, 0)) + list(range(10, 15))
            self.tz_offset = random.choice(rest_of_world)
            
        self.invites = 3
        self.is_pg = False
        self.is_banned = False
        self.is_deleted = False
        self.is_flagged_as_newbie = False
        self.reg_date = GlobalState.current_sim_date
        self.votes_received_today = 0
        
    def apply_role_state(self, params: dict):
            """Универсальный метод для установки параметров через RoleManager."""
            for key, value in params.items():
                setattr(self, key, value)

    @property
    def karma(self): return GlobalState.karma_cache[self.id]

    @property
    def rating(self): return GlobalState.rating_cache[self.id]

    def get_vote_weight(self):
        k = self.karma
        if k >= 5000: return 7
        if k >= 2000: return 4
        if k >= 100: return 2
        return 1

    def is_awake(self, hour):
        h = (hour - self.tz_offset) % 24
        return not (0 <= h < 8)

    def get_shitpost_prob(self):
        age_days = (GlobalState.current_sim_date - self.reg_date).days
        multiplier = 2.0 if self.gender == "female" else 1.0
        
        match self.skill_type:
            case "talented": return 0.05 * multiplier
            case "improver":
                progress = min(1.0, age_days / 730)
                return max(0.05, 1.0 - (0.95 * progress)) * multiplier
            case "static": return 0.5 * multiplier
            case "random": return random.uniform(0.05, 1.0) * multiplier
        return 0.5 * multiplier

    def can_post(self) -> bool:
        if self.is_deleted or self.is_banned_by_pg: return False
        if self.karma <= -1700: return False
        return True

    def can_comment(self) -> bool:
        if self.is_deleted or self.is_banned_by_pg: return False
        if self.karma <= -1999: return False
        return True
