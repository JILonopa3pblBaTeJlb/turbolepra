# --- START OF FILE lepra_sim_user_actions.py ---
import random
from lepra_shared import GlobalState, BotUser, cast_vote
from lepra_logger import log_d
from update_karma import update_karma
from lepra_nickname_gen import generate_nickname
from lepra_sim_logic_mystuff import process_mystuff
from lepra_sim_logic_feed import process_feed
from lepra_sim_logic_post_creation import process_post_creation
from lepra_sim_match import check_affair_exposure, process_match_mechanics

def check_marriage_support(u, target_id):
    partner = GlobalState.users_map.get(target_id)
    if not partner or not u.is_married or u.partner_id != target_id: return

    # Поддержка поста супруга
    if random.random() < 0.5:
        partner_posts = [p for p in GlobalState.all_posts if p.author_id == partner.id and not p.is_deleted]
        if partner_posts:
            target_post = partner_posts[-1]
            if cast_vote(target_post, u.id, 1, 1):
                log_d(f"MATCH: {u.username} поддержал пост {target_post.id} супруга {partner.username}")

def process_user_session(u, ram_posts_dict, common_glagne, inbox_posts_cache):
    now = GlobalState.current_sim_date
    ap = random.randint(15, 45)
    
    # Традиция: Поклонение Йовану (+2 один раз)
    if not u.karma_worshipped_jovan and u.id != 1:
        update_karma(u.id, 1, 2)
        u.karma_worshipped_jovan = True
        log_d(f"KARMA: {u.username} поклонился Йовану (+2)"); ap -= 1

    check_affair_exposure(u)

    if u.is_married:
        check_marriage_support(u, u.partner_id)
    
    # --- ДОБАВЛЯЕМ ВЕРОЯТНОСТЬ ЗНАКОМСТВА ---
    # Юзеры пытаются "познакомиться" с кем-то из активных
    if not u.is_married and random.random() < 0.05: # 15% шанс на социализацию в сессию
        active_list = [usr for usr in GlobalState.users if not usr.is_banned and usr.id != u.id]
        if active_list:
            target = random.choice(active_list)
            process_match_mechanics(u, target)
    # ----------------------------------------

    ap = process_mystuff(u, ap, ram_posts_dict, now)
    ap = process_feed(u, ap, common_glagne, inbox_posts_cache, now)
    ap = process_post_creation(u, ap, now)

    if now.hour == 23 and u.invites > 0 and random.random() < 0.01:
        if u.id != 1: u.invites = max(0, u.invites - 1)
        new_gender = "female" if (random.random() < 0.2) else "male"
        new_u = BotUser(username=generate_nickname(gender=new_gender), creator_id=u.id)
        new_u.gender = new_gender
        new_u.is_flagged_as_newbie = True
        GlobalState.users.append(new_u); GlobalState.users_map[new_u.id] = new_u
        update_karma(u.id, new_u.id, 2); update_karma(new_u.id, u.id, 2); GlobalState.total_invites_used += 1
        log_d(f"INVITE: {u.username} пригласил новичка {new_u.username}")
