import sqlite3

def init_db(db_name: str = "leprosorium.db"):
    """Создает таблицы и обновляет схему, если нужно."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY, author_id INTEGER, author_name TEXT, post_type TEXT, 
            rating INTEGER, plus INTEGER, minus INTEGER, is_golden BOOLEAN, 
            quality REAL, timestamp TEXT, last_activity TEXT, is_deleted BOOLEAN,
            is_legendary BOOLEAN DEFAULT 0, is_drama BOOLEAN DEFAULT 0
        )
    ''')
    
    # Добавляем колонку tg_id, media_url и text, если их нет
    for col in["tg_id INTEGER", "media_url TEXT", "text TEXT"]:
        try:
            cursor.execute(f"ALTER TABLE posts ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY, post_id INTEGER, author_id INTEGER, author_name TEXT,
            text TEXT, rating INTEGER, timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()
