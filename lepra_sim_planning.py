import random
from lepra_shared import GlobalState
from lepra_logger import log_d

def do_daily_planning():
    """Сброс статистики и планирование визитов в полночь."""
    now = GlobalState.current_sim_date
    if now.hour == 0:
        # Сброс дневной статистики
        GlobalState.daily_votes = {} 
        GlobalState.stats_today = {"posts": 0, "comments": 0, "votes": 0, "mystuff_hits": 0}
        
        # Планирование визитов
        for u in GlobalState.users:
            u.will_visit_today = (now.weekday() >= 4) if u.is_miner else random.random() < 0.8
            
        # Заговоры инбоксов
        for ib in GlobalState.inboxes:
            # Сбрасываем старую цель
            ib.target_for_onnn = None
            
            # Разрешаем только кармадрочерскому инбоксу планировать набеги
            if ib.primary_interest == "кармадрочеры":
                # Шанс 40%, что сегодня они решат кого-то «пощемить»
                if random.random() < 0.4:
                    # Выбираем живых юзеров, исключая Йована
                    eligible_targets = [u for u in GlobalState.users if u.id != 1 and not u.is_banned]
                    
                    # Сортируем по карме (от самой высокой) и берем топ-20 элиты
                    top_20_elite = sorted(eligible_targets, key=lambda x: x.karma, reverse=True)[:20]
                    
                    if top_20_elite:
                        # Выбираем случайную жертву из этого списка
                        target = random.choice(top_20_elite)
                        ib.target_for_onnn = target.id
                        
                        log_d(f"\033[1;31mPLOT: Инбокс [{ib.name}] объявил охоту на элиту! Цель: {target.username} (Карма: {target.karma})\033[0m")
