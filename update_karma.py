# --- START OF FILE update_karma.py ---

from lepra_shared import GlobalState
from lepra_logger import log_d

def update_karma(voter_id, target_id, delta):
    if voter_id == target_id: return
    voter, target = GlobalState.users_map.get(voter_id), GlobalState.users_map.get(target_id)
    if not voter or not target: return

    # Получаем старое состояние
    old_state = GlobalState.karma_matrix.get((voter_id, target_id), 0)
    new_state = max(-2, min(2, old_state + delta))
    
    if new_state == old_state: return

    # Обновляем матрицу
    GlobalState.karma_matrix[(voter_id, target_id)] = new_state
    
    # Инкрементально обновляем кэш: разница между новым и старым значением
    diff = new_state - old_state
    GlobalState.karma_cache[target_id] += diff

    # Логика удаления (кармический порог)
    # Демиурги (ханя и королева) защищены от удаления
    is_demiurge = target.special_role in ["ханя", "королева"]
    
    if GlobalState.karma_cache[target_id] <= -2000 and not is_demiurge:
        target.is_deleted = True
        GlobalState.used_nicknames.discard(target.username)
        log_d(f"!!! DELETED: Юзер {target.username} удален из системы (карма {GlobalState.karma_cache[target_id]})", important=True)
        if target in GlobalState.users:
            GlobalState.users.remove(target)
            del GlobalState.users_map[target.id]
        return

    log_d(f"KARMA: {voter.username} изменил голос за {target.username}. Итого карма: {GlobalState.karma_cache[target_id]}")

    # Озлобленность
    if delta < 0: target.bitterness = min(1.0, target.bitterness + 0.01)
    elif delta > 0: target.bitterness = max(0.0, target.bitterness - 0.001)

    # Проверка на бан
    if GlobalState.karma_cache[target_id] <= -2000 and not is_demiurge:
        target.is_banned = True
        target.is_deleted = True
        log_d(f"\033[41;37mСЛИВ: Юзер {target.username} забанен за карму {GlobalState.karma_cache[target_id]}\033[0m")
