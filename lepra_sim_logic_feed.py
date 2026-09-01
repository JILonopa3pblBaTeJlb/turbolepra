import random
from lepra_shared import (
    GlobalState, Comment, cast_vote, GOLDEN_THRESHOLD_PLUS,
    GOLDEN_THRESHOLD_MINUS_LIMIT, MAX_COMMENTS, START_BOTS, get_arkhipizdrit_comment
)
from lepra_logger import log_d
from update_karma import update_karma
from lepra_affinity import get_affinity
from lepra_sim_match import process_match_mechanics
from lepra_role_manager import get_role_behavior
from lepra_tg_tool import get_valid_image_data, render_media_html

def process_feed(u, ap, common_glagne, inbox_posts_cache, now):
    if ap <= 0: return ap

    empath_chance = max(0.0, (u.empathy - 0.7) * 3.33)
    cynic_chance = max(0.0, (0.3 - u.empathy) * 3.33)

    my_inbox_posts =[p for ib_id in u.inbox_ids for p in inbox_posts_cache.get(ib_id, [])]
    legends_in_ram =[p for p in GlobalState.all_posts if p.is_legendary and not p.is_deleted]

    pool = list(set(common_glagne) | set(my_inbox_posts) | set(legends_in_ram))
    targets = random.sample(pool, k=min(len(pool), 8))

    for p in targets:
        if ap <= 0: break
        
        author = GlobalState.users_map.get(p.author_id)
        if not author or author.is_banned: continue
        
        is_leg = p.is_legendary
        author_cfg = get_role_behavior(author.special_role)
        hate_factor = author_cfg.get("hate_factor", 0.0)
        
        aff, _ = get_affinity(u, author)
        is_newbie = (author.id > START_BOTS and (now - author.reg_date).days < 180 and author.is_flagged_as_newbie)
        
        if p.quality > 0.7 or aff > 0.75:
            sign = 1
        else:
            sign = -1

        if getattr(p, 'is_tupak', False): sign = -1
        if p.post_type == "жалостливая просьба кинуть донатик": sign = -1
        if is_newbie: sign = -1
        elif hate_factor > 0 and random.random() < hate_factor: sign = -1
        
        if sign < 0 and (set(u.inbox_ids) & set(author.inbox_ids)) and author.special_role != "пашкет":
            if p.quality > 0.6: sign = 1

        if getattr(p, 'is_drama', False): p.is_golden = False
        
        if sign < 0 and (not p.is_golden and p.plus >= 20 and p.minus <= 1) and author.id != 1 and not is_leg:
            if not (aff < 0.2 or GlobalState.karma_matrix.get((u.id, author.id), 0) < 0) and random.random() < 0.2:
                continue

        if random.random() < empath_chance and sign < 0: sign = 1
        elif random.random() < cynic_chance and sign > 0: sign = -1

        weight = u.get_vote_weight()
        if cast_vote(p, u.id, sign, weight):
            GlobalState.rating_cache[author.id] += (sign * weight)
            GlobalState.stats_today["votes"] += 1
            GlobalState.total_votes_ever += 1
            log_d(f"{'FEED: ' + u.username + ' плюсанул' if sign > 0 else 'FEED: ' + u.username + ' заминусовал'} пост {p.id} ({author.username})")
        
        if random.random() < 0.2:
            k_score = (2 if (aff > 0.85 or (u.inbox_ids and author.inbox_ids and u.inbox_ids[0] == author.inbox_ids[0])) else 1) if sign > 0 else (-2 if (getattr(p, 'is_tupak', False) or p.post_type in["бред", "жалостливая просьба кинуть донатик", "жалкие потуги"]) else -1)
            if author.id == 1 or is_leg: k_score = 2
            update_karma(u.id, author.id, k_score)
        
        if sign < 0: author.bitterness = min(1.0, author.bitterness + 0.005)
        
        if not p.is_golden and not getattr(p, 'is_drama', False) and p.plus >= GOLDEN_THRESHOLD_PLUS and p.minus <= GOLDEN_THRESHOLD_MINUS_LIMIT and p.quality > 0.8:
            p.is_golden = True
            author.invites += 1
            GlobalState.golden_posts_count += 1
            log_d(f"\033[93mЗОЛОТО: Пост {p.id} юзера {author.username} стал золотым!\033[0m")
        
        rupee_mod = 0.01 if u.special_role == "rupee" else 1.0
        if ap >= 5 and u.can_comment() and len(p.comments) < MAX_COMMENTS and random.random() < (u.reactivity * 0.004 * (5.0 if is_leg else 1.0) * rupee_mod):
            
            # --- СТРОГОЕ ПРАВИЛО ДЛЯ АНЕКДОТОВ ---
            if getattr(p, 'post_type', '') == "анекдоты" and hasattr(GlobalState, 'anekdot_builder'):
                c_text = GlobalState.anekdot_builder.build_anekdot_comment()
            # ------------------------------------
            elif u.special_role == "пашкет" and random.random() < 0.3:
                c_text = GlobalState.pashkett_builder.get_pashket_comment()
            elif u.empathy < 0.4:
                c_text = get_arkhipizdrit_comment(p.comments, u.id)
            else:
                post_text = getattr(p, 'text', '')
                # Если мем или поста нет — бот отвечает "картинкой"
                if not post_text or p.post_type == "мем":
                    _, media_url = get_valid_image_data()
                    c_text = render_media_html(media_url) if media_url else "держи мем"
                else:
                    random_words = GlobalState.processor.get_random_sample(count=random.randint(5, 10))
                    
                    # Улучшенный промпт
                    user_prompt = (
                        f"Ты — пользователь сайта Лепрозорий. Тебе нужно написать комментарий к посту типа '{p.post_type}' "
                        f"от автора '{author.username}'. "
                        f"Контент поста: '{post_text[:400]}'. "
                        f"Твоя задача: не пересказывай и не повторяй содержание поста. "
                        f"Ответь на пост саркастично, агрессивно, одобрительно или с юмором (в стиле лепрозорца). "
                        f"Твой комментарий должен быть коротким. "
                        f"Обязательно вплети в ответ эти слова: {', '.join(random_words)}."
                    )
                    c_text = GlobalState.processor.get_gpt_response([], task_type="comment", user_prompt=user_prompt)
            
            p.comments.append(Comment(u.id, p.id, text=c_text))
            u.participated_posts.add(p.id)
            p.last_activity = now
            GlobalState.stats_today["comments"] += 1
            log_d(f"COMMENT: {u.username} оставил коммент в {'ЛЕГЕНДЕ' if is_leg else 'посте'} {p.id}")
            ap -= 5
    return ap
