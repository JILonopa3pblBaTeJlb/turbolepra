# --- START OF FILE lepra_sim_moderation.py ---

import random
from update_karma import update_karma
from lepra_shared import GlobalState
from lepra_logger import log_d

def do_pg_moderation(common_glagne):
    """Модерация с механикой импичмента и политическими предпочтениями ПГ."""
    now = GlobalState.current_sim_date
    pg_user = next((u for u in GlobalState.users if u.is_pg), None)
    
    if not pg_user or now.hour not in [0, 6, 12, 18]:
        return

    # МЕХАНИКА СТРАХА
    fear_factor = 1.0
    if GlobalState.karma_cache.get(pg_user.id, 0) < 500:
        fear_factor = 0.3
        if pg_user.id != 1:
            log_d(f"PG: {pg_user.username} напуган низким рейтингом и модерирует осторожнее.")

    # МЕХАНИКА ПОЛИТИЧЕСКИХ ПРЕДПОЧТЕНИЙ (Рвение)
    zeal_factor = 1.0
    if 0.0 <= pg_user.pol_x <= 0.3:
        zeal_factor = 0.4  # Либеральный ПГ
    elif 0.6 <= pg_user.pol_x <= 1.0:
        zeal_factor = 1.5  # Ватный ПГ

    for p in common_glagne:
        if p.is_golden or p.author_id == 1:
            continue
            
        author = GlobalState.users_map.get(p.author_id)
        if not author: continue
        
        is_valuable = (getattr(p, 'is_legendary', False) or p.is_drama)
        
        # Применяем fear_factor и zeal_factor к базовой вероятности удаления
        removal_chance = pg_user.bitterness * fear_factor * zeal_factor * (0.08 if (pg_user.inbox_ids and author.inbox_ids and pg_user.inbox_ids[0] != author.inbox_ids[0]) else 0.02)
        if author.special_role == "графоманя": removal_chance *= 3
            
        if random.random() < removal_chance:
            p.is_deleted = True
            if is_valuable:
                log_d(f"\033[1;31m!!! ИМПИЧМЕНТ: ПГ {pg_user.username} удалил ценный пост {p.id} !!!\033[0m")
                
                if pg_user.id != 1:
                    participant_ids = p.commenters | {p.author_id}
                    angry_voter_ids = []
                    for uid in participant_ids:
                        user_obj = GlobalState.users_map.get(uid)
                        if user_obj and uid != pg_user.id:
                            if uid == p.author_id or user_obj.reactivity > 0.5:
                                angry_voter_ids.append(uid)
                    
                    if angry_voter_ids:
                        for v_id in angry_voter_ids:
                            update_karma(v_id, pg_user.id, -5)
                            log_d(f"PG_MOD: {GlobalState.users_map[v_id].username} негодует из-за удаления поста и минусует ПГ")
            else:
                update_karma(author.id, pg_user.id, -2)
            
            if pg_user.is_banned:
                handle_pg_impeachment(pg_user)
                break

def handle_pg_impeachment(fallen_pg):
    """Смена власти через список кандидатов или Йована."""
    candidates = getattr(GlobalState, 'last_election_candidates', [])
    successor = next((c for c in candidates[1:] if not c.is_banned), None)
    
    if not successor:
        successor = GlobalState.users_map.get(1)
        
    if successor:
        successor.is_pg = True
        log_d(f"\033[1;42mELECTION: ПГ {fallen_pg.username} слит! Власть переходит к {successor.username}\033[0m")

def check_pg_ban_for_spamming(pg_user, author):
    # Считаем посты автора подряд в ленте (нужна функция подсчета последних)
    user_posts = [p for p in GlobalState.all_posts if p.author_id == author.id and not p.is_deleted]
    if len(user_posts) >= 5:
        author.is_banned_by_pg = True
        log_d(f"PG: ПГ {pg_user.username} забанил {author.username} за спам (более 5 постов).")

def handle_pg_amnesty():
    """Сброс банов ПГ при смене власти (вызывается в do_elections)."""
    for u in GlobalState.users:
        u.is_banned_by_pg = False
