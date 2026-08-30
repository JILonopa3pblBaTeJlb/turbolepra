

import random
from collections import defaultdict
from lepra_shared import GlobalState
from lepra_sim_airdrop import do_jovan_airdrop
from lepra_sim_registrations import do_registration_wave, enforce_invite_cap
from lepra_sim_planning import do_daily_planning
from lepra_sim_moderation import do_pg_moderation
from lepra_sim_user_actions import process_user_session
from lepra_sim_elections import do_elections
from lepra_role_manager import enforce_role_quota
from lepra_sim_lyfecycle import process_lifecycle

def run_simulation_step():
    """Главный цикл симуляции: минимизация переборов и подготовка данных."""
    now = GlobalState.current_sim_date
    
    # 1. Системные события
    do_jovan_airdrop()
    do_registration_wave()
    do_daily_planning()
    if now.hour == 1:
        enforce_invite_cap()
        
    # 2. Подготовка данных
    glagne_pool = [p for p in GlobalState.all_posts if not p.is_deleted]
    common_glagne = sorted(glagne_pool, key=lambda x: x.last_activity, reverse=True)[:20]
    
    # КЭШ ТОПОВ: вычисляем один раз на шаг, а не в каждом lifecycle
    eligible = [u for u in GlobalState.users if not u.is_banned]
    top_11 = sorted(eligible, key=lambda x: x.karma, reverse=True)[:11]
    GlobalState.top_11_ids = {u.id for u in top_11}
    
    inbox_posts_cache = defaultdict(list)
    for p in glagne_pool:
        author = GlobalState.users_map.get(p.author_id)
        if author and author.inbox_ids:
            inbox_posts_cache[author.inbox_ids[0]].append(p)
    
    ram_posts_dict = {p.id: p for p in GlobalState.all_posts}

    # 3. Модерация
    do_pg_moderation(common_glagne)
    
    # 3.5 Женим jovan и enze
    from lepra_sim_match import force_hanya_queen_pair
    force_hanya_queen_pair()

    # 4. Активность юзеров
    active_users = [u for u in GlobalState.users if u.is_awake(now.hour) and u.will_visit_today and not u.is_banned]
    
    for u in active_users:
        process_lifecycle(u)
        if u.is_burned_out: continue
        if u.id == 1 and random.random() > 0.02: continue
        process_user_session(u, ram_posts_dict, common_glagne, inbox_posts_cache)

    # 5. Политика
    do_elections()
    if now.hour == 0:
        enforce_role_quota()
