import sqlite3
from typing import List
from lepra_shared import GlobalState
from lepra_logger import log_d

def archive_to_db(posts: List['Post'], db_name: str = "leprosorium.db"):
    """Оптимизированный сброс в БД с сохранением author_name, tg_id, media_url и text."""
    if not posts:
        return
        
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")
    
    posts_data = []
    comments_data =[]
    
    for p in posts:
        u = GlobalState.users_map.get(p.author_id)
        author_name = u.username if u else f"user_{p.author_id}"
        
        posts_data.append((
            p.id, p.author_id, author_name, p.post_type, p.rating, p.plus, p.minus,
            p.is_golden, p.quality, p.timestamp.isoformat(),
            p.last_activity.isoformat(), p.is_deleted,
            p.is_legendary, p.is_drama, getattr(p, 'tg_id', None),
            getattr(p, 'media_url', None), getattr(p, 'text', '')
        ))
        
        for c in p.comments:
            cu = GlobalState.users_map.get(c.author_id)
            c_author_name = cu.username if cu else f"user_{c.author_id}"
            comments_data.append((
                c.id, p.id, c.author_id, c_author_name, c.text, c.rating, c.timestamp.isoformat()
            ))
    
    try:
        cursor.execute("BEGIN TRANSACTION")
        cursor.executemany('INSERT OR REPLACE INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', posts_data)
        if comments_data:
            cursor.executemany('INSERT OR REPLACE INTO comments VALUES (?, ?, ?, ?, ?, ?, ?)', comments_data)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"DATABASE CRITICAL ERROR: {e}")
        log_d(f"DATABASE ERROR: {e}")
    finally:
        conn.close()
    
    if len(GlobalState.all_posts) > 500:
        legendaries =[p for p in GlobalState.all_posts if p.is_legendary]
        others =[p for p in GlobalState.all_posts if not p.is_legendary]
        others.sort(key=lambda x: x.last_activity, reverse=True)
        GlobalState.all_posts = legendaries + others[:500]
        
    log_d(f"DATABASE: Архивация завершена. В RAM: {len(GlobalState.all_posts)} постов.")
