import random
from lepra_shared import GlobalState
from lepra_logger import log_d
from lepra_affinity import get_affinity

def do_elections():
    """Выборы Президента с сохранением списка кандидатов для импичмента."""
    now = GlobalState.current_sim_date
    if now.weekday() == 2 and now.hour == 23:
        all_eligible = [u for u in GlobalState.users if not u.is_banned]
        top_tier = sorted([u for u in all_eligible if u.karma > 0], key=lambda x: x.karma, reverse=True)[:8]
        potential = top_tier + random.sample([u for u in all_eligible if u not in top_tier], k=min(2, len(all_eligible)-len(top_tier)))
        
        if potential:
            candidate_names = ", ".join([u.username for u in potential])
            log_d(f"\033[1;34mELECTION: Начало голосования! Кандидаты: {candidate_names}\033[0m")
            
            for v in [u for u in GlobalState.users if not u.is_banned]:
                best = max(potential, key=lambda c: get_affinity(v, c)[0] * (1.2 if (v.inbox_ids and c.inbox_ids and v.inbox_ids[0] == c.inbox_ids[0]) else 1.0))
                best.votes_received_today += 1
            
            # Сортируем кандидатов по голосам для определения победителя и заместителя
            sorted_candidates = sorted(potential, key=lambda x: x.votes_received_today, reverse=True)
            winner = sorted_candidates[0]
            
            # Сохраняем топ кандидатов в GlobalState
            GlobalState.last_election_candidates = sorted_candidates
            
            GlobalState.election_history.append({
                "date": now.strftime("%Y-%m-%d"),
                "winner_id": winner.id,
                "winner_name": winner.username,
                "votes": winner.votes_received_today
            })
            
            for u in GlobalState.users: u.is_pg = False
            winner.is_pg = True
            for u in GlobalState.users: u.votes_received_today = 0
            
            log_d(f"\033[1;44;37mELECTION: ВЫБРАН ПРЕЗИДЕНТ — {winner.username.upper()}! (Зам: {sorted_candidates[1].username if len(sorted_candidates)>1 else 'Нет'})\033[0m")
