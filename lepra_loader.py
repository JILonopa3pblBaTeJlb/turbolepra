import sqlite3
import os
from datetime import datetime
from typing import Optional
from lepra_shared import Post, Comment

def load_post_by_id(post_id: int, db_name: str = "leprosorium.db") -> Optional['Post']:
    """Ленивая загрузка: достает пост из БД и восстанавливает всё, включая текст."""
    if not os.path.exists(db_name): return None
    
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
        
    p = Post.__new__(Post)
    data = dict(row)
    
    p.id = data['id']
    p.author_id = data['author_id']
    p.post_type = data['post_type']
    p.rating = data['rating']
    p.plus = data['plus']
    p.minus = data['minus']
    p.is_golden = bool(data['is_golden'])
    p.quality = data['quality']
    p.timestamp = datetime.fromisoformat(data['timestamp'])
    p.last_activity = datetime.fromisoformat(data['last_activity'])
    p.is_deleted = bool(data['is_deleted'])
    p.user_votes = {}
    p.voters = set()
    
    p.is_legendary = bool(data.get('is_legendary', 0))
    p.is_drama = bool(data.get('is_drama', 0))
    p.tg_id = data.get('tg_id')
    p.media_url = data.get('media_url')
    p.text = data.get('text', '') # Восстанавливаем текст
    
    p.comments =[]
    p.commenters = set()
    
    cursor.execute("SELECT * FROM comments WHERE post_id = ?", (post_id,))
    for cr in cursor.fetchall():
        c_data = dict(cr)
        c = Comment.__new__(Comment)
        c.id = c_data['id']
        c.post_id = c_data['post_id']
        c.author_id = c_data['author_id']
        c.text = c_data['text']
        c.rating = c_data['rating']
        c.timestamp = datetime.fromisoformat(c_data['timestamp'])
        
        c.plus = 0
        c.minus = 0
        c.user_votes = {}
        c.voters = set()
        
        p.comments.append(c)
        p.commenters.add(c.author_id)
        
    conn.close()
    return p
