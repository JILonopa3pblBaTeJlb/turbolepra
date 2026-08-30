import os
import json
from datetime import datetime
from collections import defaultdict
from lepra_shared import GlobalState, BotUser

def load_snapshot(filename: str = "lepra_snapshot.json") -> bool:
    """Восстанавливает пользователей и корректно перепривязывает инбоксы по индексам."""
    if not os.path.exists(filename): return False
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    GlobalState.users.clear()
    GlobalState.users_map.clear()
    GlobalState.all_posts.clear()
    GlobalState.karma_matrix.clear()
    
    GlobalState.post_id_counter = data['counters']['post_id_counter']
    GlobalState.comment_id_counter = data['counters']['comment_id_counter']
    GlobalState.user_id_counter = data['counters']['user_id_counter']
    GlobalState.golden_posts_count = data['counters']['golden_posts_count']
    GlobalState.total_invites_used = data['counters']['total_invites_used']
    GlobalState.total_posts_ever = data['counters']['total_posts_ever']
    GlobalState.total_comments_ever = data['counters']['total_comments_ever']
    GlobalState.total_votes_ever = data['counters'].get('total_votes_ever', 0)
    GlobalState.current_sim_date = datetime.fromisoformat(data['current_sim_date'])
    GlobalState.karma_cache = defaultdict(int, {int(k): v for k, v in data['karma_cache'].items()})
    GlobalState.rating_cache = defaultdict(int, {int(k): v for k, v in data['rating_cache'].items()})
    GlobalState.election_history = data.get('election_history', [])

    for k_str, val in data['karma_matrix'].items():
        v_id, t_id = map(int, k_str.split(':'))
        GlobalState.karma_matrix[(v_id, t_id)] = val

    for u_data in data['users']:
        u = BotUser.__new__(BotUser)
        indices = u_data.pop('inbox_indices')
        u_data['interests'], u_data['participated_posts'] = set(u_data['interests']), set(u_data['participated_posts'])
        u_data['reg_date'] = datetime.fromisoformat(u_data['reg_date'])
        
        # Восстанавливаем datetime объекты из строк
        if u_data.get('pair_expiry'):
            u_data['pair_expiry'] = datetime.fromisoformat(u_data['pair_expiry'])
        if u_data.get('secret_affair_trigger_day'):
            u_data['secret_affair_trigger_day'] = datetime.fromisoformat(u_data['secret_affair_trigger_day'])
            
        u.__dict__.update(u_data)
        
        u.inbox_ids = []
        for idx in indices:
            if idx < len(GlobalState.inboxes):
                u.inbox_ids.append(id(GlobalState.inboxes[idx]))
                
        GlobalState.users.append(u)
        GlobalState.users_map[u.id] = u
        
    # FIX: Восстанавливаем сет занятых ников, чтобы избежать дублей после загрузки
    GlobalState.used_nicknames = {u.username for u in GlobalState.users}
    return True
