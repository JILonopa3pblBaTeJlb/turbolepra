

import json
from lepra_shared import GlobalState
from lepra_logger import log_d

def save_snapshot(filename: str = "lepra_snapshot.json"):
    """Сериализует ТОЛЬКО состояние пользователей и счетчики."""
    users_data = []
    for u in GlobalState.users:
        u_dict = u.__dict__.copy()
        u_dict['interests'], u_dict['participated_posts'] = list(u.interests), list(u.participated_posts)
        u_dict['reg_date'] = u.reg_date.isoformat()
        
        # Конвертируем новые datetime поля в строку для JSON
        if u_dict.get('pair_expiry'):
            u_dict['pair_expiry'] = u_dict['pair_expiry'].isoformat()
        if u_dict.get('secret_affair_trigger_day'):
            u_dict['secret_affair_trigger_day'] = u_dict['secret_affair_trigger_day'].isoformat()
        
        # Сохраняем индексы инбоксов вместо ссылок на объекты
        inbox_indices = [idx for idx, ib in enumerate(GlobalState.inboxes) if id(ib) in u.inbox_ids]
        u_dict['inbox_indices'] = inbox_indices
        
        if 'inbox_ids' in u_dict:
            del u_dict['inbox_ids']
        users_data.append(u_dict)

    state = {
        "counters": {
            "post_id_counter": GlobalState.post_id_counter,
            "comment_id_counter": GlobalState.comment_id_counter,
            "user_id_counter": GlobalState.user_id_counter,
            "golden_posts_count": GlobalState.golden_posts_count,
            "total_invites_used": GlobalState.total_invites_used,
            "total_posts_ever": GlobalState.total_posts_ever,
            "total_comments_ever": GlobalState.total_comments_ever,
            "total_votes_ever": GlobalState.total_votes_ever
        },
        "inbox_names": [ib.name for ib in GlobalState.inboxes],
        "current_sim_date": GlobalState.current_sim_date.isoformat(),
        "users": users_data,
        "karma_matrix": {f"{k[0]}:{k[1]}": v for k, v in GlobalState.karma_matrix.items()},
        "karma_cache": dict(GlobalState.karma_cache),
        "rating_cache": dict(GlobalState.rating_cache),
        "election_history": GlobalState.election_history
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    log_d(f"SNAPSHOT: Состояние {len(GlobalState.users)} юзеров сохранено.")
