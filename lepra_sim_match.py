import random
from datetime import timedelta
from lepra_shared import GlobalState, Post
from lepra_logger import log_d
from update_karma import update_karma

def create_match(u1, u2):
    """Образование союза и традиционный взаимный плюс."""
    expiry = None if (u1.id in [1, 6579] and u2.id in [1, 6579]) else timedelta(days=random.randint(60, 1825))


    u1.is_married = u2.is_married = True
    u1.partner_id, u2.partner_id = u2.id, u1.id
    u1.pair_expiry = u2.pair_expiry = (GlobalState.current_sim_date + expiry) if expiry else None

    update_karma(u1.id, u2.id, 2)
    update_karma(u2.id, u1.id, 2)

    log_d(f"\033[35mMATCH: Союз образован между {u1.username} и {u2.username} (+2/+2)\033[0m")

def trigger_drama(u1, u2, reason):
    """Генерация полноценного драматического поста через LLM."""
    p = Post(u1.id, p_type="бред")
    p.is_drama = True
    
    # Формируем промпт для генерации настоящего лепро-скандала
    system_prompt = (
        "Ты — пользователь культового сайта Лепрозорий. У тебя разворачивается тяжелая личная драма "
        "или публичный скандал с другим юзером. Напиши яростный, едкий, токсичный или эмоциональный пост-разоблачение "
        "в фирменном стиле Лепры (с сарказмом, обидой и драмой)."
    )
    user_prompt = (
        f"Автор поста: {u1.username}. "
        f"Второй участник конфликта: {u2.username}. "
        f"Причина драмы: {reason}. "
        f"Напиши полноценный развернутый пост, описывающий эту ситуацию и выражающий твое отношение к оппоненту."
    )
    
    try:
        # Генерируем реальный текст через LLM
        p.text = GlobalState.processor.get_gpt_response(
            [], 
            task_type="post", 
            system_prompt=system_prompt, 
            user_prompt=user_prompt
        )
    except Exception as e:
        # Аварийный фоллбэк, если LLM недоступна
        p.text = f"ДРАМА: {reason} между {u1.username} и {u2.username}. Все в шоке, в комментах полыхает."
        
    GlobalState.all_posts.append(p)
    log_d(f"\033[31mDRAMA: {u1.username} инициировал драму против {u2.username} ({reason})\033[0m")
    
    # 20% шанс на репакуку или уход в оффлайн на 1-1.5 года (12-18 месяцев)
    if random.random() < 0.2:
        if random.random() < 0.5:
            u1.is_banned = True
            log_d(f"!!! REPAKUKU: {u1.username} не выдержал драмы !!!")
        else:
            u1.is_burned_out = True
            u1.burnout_threshold = random.uniform(365, 545) 
            log_d(f"LIFE: {u1.username} ушел в реал после драмы.")

def process_match_mechanics(u, target_user):
    """Логика образования пар согласно ТЗ: координаты в пределах 0.2 и 2+ общих интереса."""
    # 1. Базовые ограничения: разный пол и оба свободны
    if u.gender == target_user.gender or u.is_married or target_user.is_married:
        return

    # 2. Проверка условий ТЗ
    # Политические координаты в пределах 0.2
    diff_x = abs(u.pol_x - target_user.pol_x)
    diff_y = abs(u.pol_y - target_user.pol_y)
    
    # Не менее 2 одинаковых интересов
    common_interests_count = len(u.interests.intersection(target_user.interests))
    
    if diff_x <= 0.2 and diff_y <= 0.2 and common_interests_count >= 2:
        # Условия соблюдены, с небольшим шансом (например 25%) создаем пару,
        # чтобы они не "женились" мгновенно при первом же контакте
        if random.random() < 0.25:
            create_match(u, target_user)
        
    # Промискуитет (10% случаев у занятых)
    if u.is_married and random.random() < 0.1:
        u.is_promiscuous = True
        u.secret_affair_trigger_day = GlobalState.current_sim_date
        log_d(f"MATCH: {u.username} вступил в тайную связь!")



def check_affair_exposure(u):
    """Проверка раскрытия измены."""
    if u.is_promiscuous and u.secret_affair_trigger_day:
        days_passed = (GlobalState.current_sim_date - u.secret_affair_trigger_day).days
        # Раскрытие в период от 1 до 60 дней (если не 0.3 вероятность, что не раскроется вообще)
        if 1 <= days_passed <= 60 and random.random() < 0.02: # Примерная динамика вероятности
            partner = GlobalState.users_map.get(u.partner_id)
            if partner:
                trigger_drama(u, partner, "измена")
                trigger_drama(partner, u, "предательство")
                trigger_drama(u, partner, "последствия измены")
                u.is_promiscuous = False

def force_hanya_queen_pair():
    """Принудительное сведение Йована и Королевы."""
    hanya = GlobalState.users_map.get(1)
    queen = next((u for u in GlobalState.users if u.special_role == "королева"), None)
    
    if hanya and queen:
        # Принудительно устанавливаем связь, если её нет
        if not hanya.is_married or hanya.partner_id != queen.id:
            create_match(hanya, queen)
            log_d("\033[1;35mMATCH: ЭЛИТНЫЙ СОЮЗ: Йован и Королева воссоединились!\033[0m", important=True)
        
        # Блокируем возможность распада: обнуляем таймер истечения
        hanya.pair_expiry = None
        queen.pair_expiry = None
