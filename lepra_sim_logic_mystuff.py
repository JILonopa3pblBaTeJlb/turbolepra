import random
from datetime import timedelta
from lepra_shared import GlobalState, Comment, cast_vote, MAX_COMMENTS, get_arkhipizdrit_comment, generate_reply
from lepra_logger import log_d
from update_karma import update_karma
from lepra_affinity import get_affinity
from lepra_loader import load_post_by_id
from lepra_role_manager import get_role_behavior
from lepra_tg_tool import get_valid_image_data, render_media_html

def process_mystuff(u, ap, ram_posts_dict, now):
    if ap <= 0: return ap
    participated_limited = list(u.participated_posts)[-20:]
    empath_chance = max(0.0, (u.empathy - 0.7) * 3.33)
    cynic_chance = max(0.0, (0.3 - u.empathy) * 3.33)
    
    for p_id in participated_limited:
        if ap <= 0: break
        p = ram_posts_dict.get(p_id)
        if not p:
            if random.random() < 0.05:
                p = load_post_by_id(p_id)
                if p: GlobalState.all_posts.append(p); ram_posts_dict[p.id] = p
                else: continue
            else: continue
        
        if p.is_deleted: continue
        threshold_time = now - timedelta(hours=2)
        new_c =[c for c in p.comments if c.timestamp > threshold_time]
        if not new_c: continue
        
        GlobalState.stats_today["mystuff_hits"] += 1
        c = random.choice(new_c)
        if c.author_id == u.id or u.id in c.voters: continue
        
        c_author = GlobalState.users_map.get(c.author_id)
        if not c_author or c_author.is_banned: continue
        
        aff = 1.0 if c_author.id == 1 else get_affinity(u, c_author)[0]
        if set(u.inbox_ids) & set(c_author.inbox_ids): aff = min(1.0, aff + 0.15)
        
        role_cfg = get_role_behavior(c_author.special_role)
        hate_factor = role_cfg.get("hate_factor", 0.0)
        
        sign = 1 if (aff > 0.6 or (p.quality > 0.8 and aff > 0.5)) else -1
        if hate_factor > 0 and random.random() < (hate_factor * 2): sign = -1
        if p.is_legendary: sign, aff = 1, 1.0
        
        if random.random() < empath_chance: sign = 1
        elif random.random() < cynic_chance: sign = -1

        weight = u.get_vote_weight()
        if cast_vote(c, u.id, sign, weight):
            GlobalState.rating_cache[c_author.id] += (sign * weight)
            GlobalState.stats_today["votes"] += 1
            GlobalState.total_votes_ever += 1
            log_d(f"MYSTUFF: {u.username} {'одобрил' if sign > 0 else 'минусанул'} коммент {c_author.username}")
        
        if random.random() < 0.4:
            is_same_inbox = (u.inbox_ids and c_author.inbox_ids and u.inbox_ids[0] == c_author.inbox_ids[0])
            k_score = -2 if hate_factor > 0.5 else (2 if (aff > 0.8 or c_author.id == 1) else (1 if is_same_inbox else (-1 if sign < 0 else 1)))
            update_karma(u.id, c_author.id, k_score)
        
        ap -= 1
        reactivity_mult = 10.0 if p.is_legendary else 1.0
        rupee_mod = 0.1 if u.special_role == "rupee" else 1.0
        
        if u.can_comment() and len(p.comments) < MAX_COMMENTS and random.random() < (u.reactivity * 0.0025 * reactivity_mult * rupee_mod):
            
            # --- СТРОГОЕ ПРАВИЛО ДЛЯ АНЕКДОТОВ В MYSTUFF ---
            if getattr(p, 'post_type', '') == "анекдоты" and hasattr(GlobalState, 'anekdot_builder'):
                c_text = GlobalState.anekdot_builder.build_anekdot_comment()
            # ---------------------------------------------
            elif u.empathy < 0.4:
                c_text = get_arkhipizdrit_comment(p.comments, u.id)
            else:
                # Если предыдущий коммент — это картинка, отвечаем картинкой
                if "<img" in c.text:
                    _, media_url = get_valid_image_data()
                    c_text = render_media_html(media_url) if media_url else "поддерживаю"
                else:
                    random_words = GlobalState.processor.get_random_sample(count=random.randint(10, 50))
                    user_prompt = f"Ты пишешь ответ на этот комментарий: '{getattr(c, 'text', '')[:500]}'. Используй эти слова: {', '.join(random_words)}."
                    c_text = GlobalState.processor.get_gpt_response([], task_type="comment", user_prompt=user_prompt)
                
            p.comments.append(Comment(u.id, p.id, text=c_text))
            p.last_activity = now
            GlobalState.stats_today["comments"] += 1
            log_d(f"\033[94mMYSTUFF: {u.username} влез в спор в посте {p.id}\033[0m")
            
            ap -= 5
    return ap
