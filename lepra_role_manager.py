# --- START OF FILE lepra_role_manager.py ---
import random
from lepra_shared import GlobalState, GRAPHOMANIA_NICK_QUEUE
from lepra_role_limits import check_role_limits
from lepra_logger import log_d

ROLE_CONFIGS = {
    "ханя": {"invites": float('inf'), "creativity": 0.025, "pol_x": (0.71, 1.0), "is_promiscuous": False},
    "королева": {
        "creativity": 0.0555,
        "reactivity": 0.02,
        "pol_x": (0.45, 0.55),
        "pol_y": (0.0, 0.59),
        "is_promiscuous": False
    },
    "пашкет": {
        "creativity": 0.9,
        "reactivity": 0.1,
        "forced_post_type": "музыка",
        "hate_factor": 0.7,
        "pol_x": 0.5,
        "pol_y": 0.5
    },
    "графоманя": {
        "pol_y": 0.9,
        "reactivity": 0.9,
        "empathy": 0.05,
        "creativity": 0.9,
        "hate_factor": 0.4
    },
    "rupee": {"creativity": 0.9, "reactivity": 0.0},
    "мем-лорд": {"creativity": 0.9, "forced_post_type": "мем"},
    "шиз": {"hate_factor": 0.75}
}

def get_role_behavior(role):
    return ROLE_CONFIGS.get(role, {})

def get_post_quality(role):
    """Возвращает диапазон качества в зависимости от роли."""
    if role in ["графоманя", "пашкет"]:
        return (0.0, 0.1)
    if role in ["ханя", "королева"]:
        return (0.95, 1.0)
    if role in ["шиз"]:
        return (0, 0.4)
    if role in ["rupee"]:
        return (0.8, 1.0)
    
    return None

def enforce_role_quota():
    GlobalState.shiz_limit = max(3, int(len(GlobalState.users) * 0.1))
    roles = ["графоманя", "шиз", "сиськарий", "мем-лорд", "rupee", "dramqueen", "пашкет"]
    for role in roles:
        holders = [u for u in GlobalState.users if u.special_role == role and not u.is_banned]
        if role in ["ханя", "королева", "пашкет"] and holders: continue
        if not holders:
            candidates = [u for u in GlobalState.users if not u.special_role and u.karma > -500]
            if role == "dramqueen": candidates = [u for u in candidates if u.gender == "female"]
            elif role in ["rupee", "графоманя", "пашкет"]: candidates = [u for u in candidates if u.gender == "male"]
            if candidates:
                candidate = random.choice(candidates)
                if check_role_limits(role, candidate.pol_x, gender=candidate.gender):
                    assign_role(candidate, role)

def assign_role(user, role):
    user.special_role = role
    cfg = ROLE_CONFIGS.get(role, {})
    # Добавляем is_promiscuous в список полей для применения
    user.apply_role_state({k: v for k, v in cfg.items() if k in ["invites", "creativity", "reactivity", "pol_y", "empathy", "is_promiscuous"]})
    
    if role == "графоманя":
        for nick in GRAPHOMANIA_NICK_QUEUE:
            if nick not in GlobalState.used_nicknames:
                GlobalState.used_nicknames.discard(user.username)
                user.username = nick
                GlobalState.used_nicknames.add(nick)
                break
    elif role == "пашкет":
        user.username = f"Pashkett{GlobalState.pashkett_counter}"
        GlobalState.pashkett_counter += 1
        GlobalState.used_nicknames.add(user.username)
    elif role == "ханя":
        user.username = "jovan"
    elif role == "королева":
        user.username = "enze"
        user.gender = "female"
    log_d(f"ROLE: Назначена роль [{role}]. Юзер: {user.username}")
