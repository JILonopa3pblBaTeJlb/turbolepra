

# --- START OF FILE lepra_sim_registrations.py ---
import random
from lepra_shared import GlobalState, BotUser
from lepra_logger import log_d
from lepra_nickname_gen import generate_nickname
from update_karma import update_karma

def _perform_registration(inviter: BotUser) -> BotUser:
    """Техническая процедура регистрации с логом и соблюдением гендерного баланса 4:1."""
    if inviter.id != 1:
        if inviter.invites <= 0:
            return None
        inviter.invites -= 1
    
    # Гендерный баланс: 1 женщина на 4 мужчин
    female_count = len([u for u in GlobalState.users if u.gender == "female"])
    male_count = len([u for u in GlobalState.users if u.gender == "male"])
    
    gender = "female" if (female_count * 4 < male_count) else "male"
    
    # ПЕРЕДАЕМ gender В generate_nickname
    new_u = BotUser(username=generate_nickname(gender=gender), creator_id=inviter.id)
    new_u.gender = gender
    new_u.is_flagged_as_newbie = True
    GlobalState.users.append(new_u)
    GlobalState.users_map[new_u.id] = new_u
    
    log_d(f"\033[95mINVITE: {inviter.username} привел новичка {new_u.username} (ID: {new_u.id}, пол: {new_u.gender})\033[0m")
    
    update_karma(inviter.id, new_u.id, 2)
    update_karma(new_u.id, inviter.id, 2)
    
    GlobalState.total_invites_used += 1
    return new_u

def do_registration_wave():
    """Волна регистраций."""
    now = GlobalState.current_sim_date
    if now.day == 1 and now.hour == 0:
        potential_inviters = [u for u in GlobalState.users if u.invites > 0]
        if potential_inviters:
            new_count = random.randint(1, 40)
            for _ in range(new_count):
                inviter = random.choice(potential_inviters)
                _perform_registration(inviter)
            log_d(f"\033[1;95mREG_WAVE: Первое число месяца, зарегистрировано {new_count} душ.\033[0m")

def enforce_invite_cap():
    """Принудительная раздача излишков."""
    forced_count = 0
    current_users = list(GlobalState.users)
    for u in current_users:
        if u.id == 1: continue
        if u.invites > 6:
            excess = int(u.invites - 6)
            for _ in range(excess):
                _perform_registration(u)
                forced_count += 1
    if forced_count > 0:
        log_d(f"\033[95mSYSTEM: Принудительно расселено {forced_count} новичков от жадных юзеров.\033[0m")
# --- END OF FILE lepra_sim_registrations.py ---
