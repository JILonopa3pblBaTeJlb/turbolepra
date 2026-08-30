# --- START OF FILE lepra_sim_logic_post_creation.py ---

import random
from lepra_shared import GlobalState, Post, POST_TYPES_CONFIG, POST_CHANCE_SCALING
from lepra_logger import log_d
from lepra_role_manager import get_role_behavior, get_post_quality
from lepra_tg_tool import get_valid_image_data
from lepra_image_search import get_kdpv_image
from lepra_content_factory import generate_post_content

def process_post_creation(u, ap, now):
    if ap < 10: return ap
    if not u.can_post(): return ap
    
    is_dq = (u.special_role == "dramqueen")
    role_cfg = get_role_behavior(u.special_role)
    q_range = get_post_quality(u.special_role)
    
    creativity_mod = 1.5 if is_dq else 1.0
    drama_chance_mod = 3.0 if is_dq else 1.0
    
    # Проверяем, выпала ли легенда на этом шаге
    is_legendary_trigger = random.random() < (1 / (16 * 365 * 24) * (2 if is_dq else 1))
    
    can_post = True
    forced_p_type = "охуительная история" if is_legendary_trigger else None
    
    if getattr(u, 'is_flagged_as_newbie', False) and (now - u.reg_date).days < 180:
        can_post = (random.random() < 0.05)
    
    if can_post:
        chance = u.creativity * creativity_mod * 0.04 * POST_CHANCE_SCALING * (6 if u.special_role == "шиз" else (10 if u.special_role in["графоманя", "пашкет"] else 1))
        
        # Если это легенда, принудительно разрешаем пост
        if is_legendary_trigger or random.random() < chance:
            
            # Спец-ветка: Графоманя
            if u.special_role == "графоманя" and not is_legendary_trigger:
                post_data = GlobalState.ejik_builder.build_ejik_post()
                p = Post(u.id, p_type=post_data["post_type"])
                p.text = post_data["text"]
                p.quality = post_data["quality"]
                if "media_url" in post_data: p.media_url = post_data["media_url"]
                GlobalState.all_posts.append(p); u.participated_posts.add(p.id); GlobalState.stats_today["posts"] += 1
                log_d(f"\033[91mEJIK POST: {u.username} опубликовал пост (id:{p.id})\033[0m"); ap -= 10; return ap
            
            # Спец-ветка: Пашкет
            elif u.special_role == "пашкет" and not is_legendary_trigger:
                post_data = GlobalState.pashkett_builder.build_pashket_post()
                p = Post(u.id, p_type=post_data["post_type"])
                p.text = post_data["text"]; p.media_url = post_data["media_url"]; p.quality = post_data["quality"]
                GlobalState.all_posts.append(p); u.participated_posts.add(p.id); GlobalState.stats_today["posts"] += 1
                log_d(f"\033[96mPASHKET POST: {u.username} выложил видео (id:{p.id})\033[0m"); return ap
                
            # Спец-ветка: Обычные юзеры постят YouTube-ролик (если не легенда)
            elif hasattr(GlobalState, 'youtube_builder') and not is_legendary_trigger and random.random() < 0.15:
                post_data = GlobalState.youtube_builder.build_youtube_post()
                p = Post(u.id, p_type=post_data["post_type"])
                p.text = post_data["text"]
                p.media_url = post_data["media_url"]
                p.quality = post_data["quality"]
                GlobalState.all_posts.append(p)
                u.participated_posts.add(p.id)
                GlobalState.stats_today["posts"] += 1
                log_d(f"\033[96mYOUTUBE POST: {u.username} поделился роликом с ютуба (id:{p.id})\033[0m")
                ap -= 10
                return ap

            # Стандартная генерация (или генерация для Легенды через content_factory)
            forced_type = role_cfg.get("forced_post_type")
            
            if is_legendary_trigger:
                p_type = "охуительная история"
            elif forced_type:
                p_type = forced_type
            else:
                available_types = [t for t, cfg in POST_TYPES_CONFIG.items() if cfg["interest"] in u.interests]
                p_type = random.choice(available_types) if available_types else "обычный"
            
            # Защита от сбоев генерации контента
            try:
                content = generate_post_content(u, p_type)
                if not content or (not content.get("text") and not content.get("is_media_required")):
                    log_d(f"WARNING: Пустой контент для {u.username}, пропускаем пост.")
                    return ap
            except Exception as e:
                log_d(f"CRITICAL: Ошибка при генерации контента: {e}")
                return ap
            
            p = Post(u.id, p_type=p_type)
            
            # Навешиваем статус Легенды, если это она
            if is_legendary_trigger:
                p.is_legendary = True
                p.quality = 1.0
                if is_dq or random.random() < 0.5:
                    p.is_golden = True
                    GlobalState.golden_posts_count += 1
                    log_d(f"\033[91;1m!!! ЛЕГЕНДА (ЗОЛОТО): {u.username} написал шедевр (id:{p.id}) !!!\033[0m")
                else:
                    p.is_drama = True
                    log_d(f"\033[91;1m!!! ЛЕГЕНДА (ДРАМА): {u.username} взорвал гнездо (id:{p.id}) !!!\033[0m")
            
            # Мем-логика (обрабатываем отдельно, если нужно)
            if p_type == "мем" or content.get("is_media_required"):
                tg_id, media_url = get_valid_image_data()
                if tg_id:
                    p.tg_id = tg_id; p.media_url = media_url
                else:
                    p.post_type = "обычный"
            else:
                p.text = content.get("text", "")
                # КДПВ для обычных постов (легендам тоже можно подтянуть картинку для сочности)
                if random.random() < (0.9 if is_legendary_trigger else 0.7):
                    query = f"{p.post_type} {list(u.interests)[0] if u.interests else ''}"
                    kdpv_url = get_kdpv_image(query)
                    if kdpv_url: p.media_url = kdpv_url
            
            if not is_legendary_trigger:
                if random.random() < (0.01 * drama_chance_mod): p.is_drama = True
                elif random.random() < u.get_shitpost_prob(): p.is_tupak = True
            
            if is_legendary_trigger:
                p.quality = 1.0
            elif q_range:
                p.quality = random.uniform(q_range[0], q_range[1])
            elif p.is_tupak:
                p.quality = random.uniform(0.0, 0.15)
            
            GlobalState.all_posts.append(p)
            u.participated_posts.add(p.id)
            GlobalState.stats_today["posts"] += 1
            
            prefix = "ЛЕГЕНДАРНЫЙ ПОСТ" if is_legendary_trigger else f"POST [{p.post_type}]"
            log_d(f"\033[91m{prefix}: {u.username} опубликовал пост (id:{p.id})\033[0m")
            ap -= 10
            return ap
    return ap
# --- END OF FILE lepra_sim_logic_post_creation.py ---
