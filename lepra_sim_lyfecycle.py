import random
from lepra_shared import GlobalState, Post, BotUser
from lepra_logger import log_d
from update_karma import update_karma
from lepra_role_manager import assign_role

def perform_repakuku(u):
    """Ритуальное сеппуку: пост и уход в бан."""
    p = Post(u.id, p_type="бред")
    p.is_deleted = True
    GlobalState.all_posts.append(p)
    u.is_deleted = True
    u.is_banned = True
    if u in GlobalState.users:
        GlobalState.users.remove(u)
        GlobalState.used_nicknames.discard(u.username)
    log_d(f"!!! REPAKUKU: {u.username} выложил пароль РЕПАКУКУ на глагне и самоликвидировался !!!", important=True)

def process_lifecycle(u):
    """Обработка жизненного цикла с учетом защиты демиургов и респауна Пашкета."""
    # 0. Демиурги защищены от выгорания и смерти
    if u.special_role in ["ханя", "королева"]:
        return

    # 1. Логика выхода из выгорания
    if u.is_burned_out:
        if random.random() < 0.5:
            u.is_burned_out = False
            u.will_visit_today = True
            log_d(f"LIFE: {u.username} вернулся из неактива после ностальгии.")
        return

    # 2. Проверка союзов (если истек срок)
    if u.is_married and u.pair_expiry and GlobalState.current_sim_date > u.pair_expiry:
        # ЗАЩИТА ЭЛИТНОЙ ПАРЫ
        partner = GlobalState.users_map.get(u.partner_id)
        if partner and (u.special_role in ["ханя", "королева"] or partner.special_role in ["ханя", "королева"]):
            u.pair_expiry = None
            partner.pair_expiry = None
            return

        if random.random() > 0.2:
            u.is_married = u.partner_id = u.pair_expiry = False
            if partner:
                partner.is_married = partner.partner_id = partner.pair_expiry = False
                log_d(f"MATCH: Союз {u.username} и {partner.username} распался по сроку.", important=True)

    # 3. Репакуку для Dramqueen
    if u.special_role == "dramqueen":
        dramas = [p for p in GlobalState.all_posts if p.author_id == u.id and p.is_drama]
        bad_dramas = [p for p in dramas if p.rating < -2000]
        if len(bad_dramas) >= 2:
            log_d(f"LIFE: {u.username} не выдержала позора двух заминусованных драм.", important=True)
            perform_repakuku(u)
            return

    # 4. Респаун для Пашкета и Графомани
    if u.is_deleted and u.special_role in ["графоманя", "пашкет"]:
        role = u.special_role
        log_d(f"LIFE: {role.capitalize()} {u.username} был удален, но возродился в новом воплощении.")
        new_u = BotUser(gender="male")
        GlobalState.users.append(new_u)
        GlobalState.users_map[new_u.id] = new_u
        assign_role(new_u, role)
        return

    # 5. Таймер выгорания
    if not u.special_role:
        if u.participated_posts and u.days_since_first_post is None:
            u.days_since_first_post = 0.0
        if u.days_since_first_post is not None:
            burn_speed = 1.0 + u.bitterness
            u.days_since_first_post += (1/24) * burn_speed
            if u.days_since_first_post >= u.burnout_threshold:
                u.is_burned_out = True
                return

    # 6. Мерячение
    if u.karma > 2000 and u.days_since_first_post and u.days_since_first_post > 180:
        if u.special_role != "dramqueen":
            if u in sorted(GlobalState.users, key=lambda x: x.karma, reverse=True)[:11]:
                log_d(f"\033[1;31m!!! MERJACHENIE: {u.username} впадает в состояние психоза !!!\033[0m", important=True)
                update_karma(u.id, 1, -2)
                if random.random() < 0.5:
                    perform_repakuku(u)
                else:
                    shizes = [x for x in GlobalState.users if x.special_role == "шиз"]
                    if len(shizes) < GlobalState.shiz_limit:
                        u.special_role = "шиз"
