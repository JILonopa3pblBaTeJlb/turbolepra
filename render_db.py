# --- START OF FILE render_db.py ---

import sqlite3
import os
import math
import json
from lepra_tg_tool import render_media_html
from lepra_youtube_tool import render_youtube_embed
from datetime import datetime

OUTPUT_DIR = ""  # Корневая директория проекта
DB_NAME = "leprosorium.db"
TEMPLATE_FILE = "template_base.html"
POSTS_PER_PAGE = 42

def format_lepra_date(date_str: str) -> str:
    dt = datetime.fromisoformat(date_str)
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
        7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    return f"{dt.day} {months[dt.month]} {dt.year} в {dt.strftime('%H.%M')}"

def get_page_filename(page_num):
    return "index.html" if page_num == 0 else f"page_{page_num}.html"

def get_user_count() -> str:
    user_count = 0
    if os.path.exists("lepra_snapshot.json"):
        try:
            with open("lepra_snapshot.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                user_count = len(data.get("users", []))
        except Exception:
            pass
    
    if user_count == 0 and os.path.exists(DB_NAME):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT author_id) FROM (
                    SELECT author_id FROM posts 
                    UNION 
                    SELECT author_id FROM comments
                )
            """)
            res = cursor.fetchone()
            if res:
                user_count = res[0]
            conn.close()
        except Exception:
            pass
            
    return f"{user_count:,}".replace(",", ".")

def get_simulation_datetime() -> str:
    sim_date_str = None
    if os.path.exists("lepra_snapshot.json"):
        try:
            with open("lepra_snapshot.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                sim_date_str = data.get("current_sim_date")
        except Exception:
            pass
            
    if not sim_date_str and os.path.exists(DB_NAME):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(timestamp) FROM posts")
            res = cursor.fetchone()
            if res and res[0]:
                sim_date_str = res[0]
            conn.close()
        except Exception:
            pass
            
    if sim_date_str:
        return format_lepra_date(sim_date_str)
        
    return "2007 год"

def generate_paginator_html(current_page, total_pages):
    prev_link = get_page_filename(current_page - 1) if current_page > 0 else "#"
    next_link = get_page_filename(current_page + 1) if current_page < total_pages - 1 else "#"
    
    pages_html = ""
    for p in range(total_pages):
        if p >= 10: break
        
        link = get_page_filename(p)
        if p == current_page:
            pages_html += f'<td width="10%"><span><strong><em>{p+1}</em></strong></span></td>'
        else:
            pages_html += f'<td width="10%"><span><a href="{link}"><em>{p+1}</em></a></span></td>'

    return f'''
    <div class="b-paginator">
        <div class="paginator_go_to_pages" style="width: 100%;">
            <a title="Предыдущая страница" href="{prev_link}" class="paginator_go_to_page paginator_go_to_previous" id="js-paginator_control_prev"><span></span></a>
            <a title="Следующая страница" href="{next_link}" class="paginator_go_to_page paginator_go_to_next" id="js-paginator_control_next"><span></span></a>
        </div>
        <div>
            <div class="paginator paginator_first_page" id="js-paginator" style="width: 100%;">
                <table style="width:100%;"><tbody><tr>{pages_html}</tr></tbody></table>
            </div>
            <div class="paginator_pages">{total_pages} страниц</div>
        </div>
    </div>
    '''

def get_full_post_html(p_id, author_id, username, post_type, rating, content, comments_html, timestamp):
    return f'''
    <div class="post u{username}" id="p{p_id}">
        <div class="dt">
            <div class="dti p_body">{content}</div>
        </div>
        <div class="c_footer" style="font-size: smaller; color: rgb(120, 120, 120); margin: 10px 0;">
            <div class="ddi" style="display: inline-block;">
                Написал <a href="users/user_{author_id}.html" style="color: rgb(120, 120, 120);">{username}</a>
                <span class="js-date" style="text-decoration: none; cursor: pointer;" 
                      onmouseover="this.style.textDecoration='underline'" 
                      onmouseout="this.style.textDecoration='none'">{timestamp}</span>
            </div>
            <div class="vote" id="js-post_id_{p_id}" style="float: right;">
                <strong class="vote_result">{rating}</strong>
            </div>
        </div>
    </div>
    <div class="comments_section">
        {comments_html}
    </div>
    '''

def get_content_html(post_type, media_url, text, timestamp):
    content_html = ""
    if text and text.strip():
        formatted_text = text.replace('\n', '<br>')
        content_html += f'<div class="post_text" style="margin-bottom: 10px;">{formatted_text}</div>'
    
    media_html = ""
    if media_url:
        if "youtube.com" in media_url or "youtu.be" in media_url:
            media_html = render_youtube_embed(media_url)
        elif post_type == "мем":
            media_html = f'<div style="text-align:left; width:500px; display:block; margin:0;">{render_media_html(media_url)}</div>'
        else:
            media_html = f'<div style="text-align:left; width:500px; display:block; margin:10px 0;"><img src="{media_url}" width="500"></div>'
    
    if media_html:
        content_html = media_html + content_html
    return content_html if content_html else f"Контент поста: {post_type}"

def get_post_summary_html(p_id, author_id, username, post_type, rating, comments_count, timestamp, media_url=None, text=None):
    content = get_content_html(post_type, media_url, text, timestamp)
    return f'''
    <div class="post u{username}" id="p{p_id}">
        <div class="dt">
            <div class="dti p_body">{content}</div>
        </div>
        <div class="c_footer" style="font-size: smaller; color: rgb(120, 120, 120); margin: 10px 0;">
            <div class="ddi" style="display: inline-block;">
                Написал <a href="users/user_{author_id}.html" style="color: rgb(120, 120, 120);">{username}</a>
                <span class="js-date" style="text-decoration: none; cursor: pointer;" 
                      onmouseover="this.style.textDecoration='underline'" 
                      onmouseout="this.style.textDecoration='none'">{timestamp}</span>
                <span class="b-post_comments_links">
                    <a href="post_{p_id}.html" style="color: rgb(120, 120, 120);"><strong>{comments_count} комментариев</strong></a>
                </span>
            </div>
            <div class="vote" style="float: right;">{rating}</div>
        </div>
    </div><br><br>
    '''

def get_comment_html(c_id, author_id, author_name, text, rating, timestamp):
    formatted_text = text.replace('\n', '<br>') if text else ""
    return f'''
    <div class="c_i" id="c{c_id}">
    <br>
        <div class="b-c_o" style="border-color: rgb(160, 89, 0);"></div>
        <div class="c_body">{formatted_text}</div>
        <div class="c_footer" style="font-size: smaller; color: rgb(120, 120, 120);">
            <div class="ddi" style="display: inline-block;">
                <span class="c_wrote">Написал</span> 
                <a href="users/user_{author_id}.html" class="c_user" style="color: rgb(120, 120, 120);">{author_name}</a> 
                <a class="c_date" href="#" style="color: rgb(120, 120, 120); text-decoration: none; cursor: pointer;" 
                   onmouseover="this.style.textDecoration='underline'" 
                   onmouseout="this.style.textDecoration='none'">{timestamp}</a> 
                <a class="c_answer" href="#" style="color: rgb(120, 120, 120);">ответить</a>
            </div>
            <div class="vote c_vote" style="float: right;">
                <table style="border-collapse: collapse; display: inline-table; vertical-align: middle;">
                    <tr>
                        <td style="padding: 0 2px;"><a class="vote_button vote_button_minus" href="#" style="color: rgb(120, 120, 120); text-decoration: none;">-<em></em></a></td>
                        <td style="text-align: right; font-size: smaller; padding: 0 5px; min-width: 10px;"><strong class="vote_result">{rating}</strong></td>
                        <td style="padding: 0 2px;"><a class="vote_button vote_button_plus" href="#" style="color: rgb(120, 120, 120); text-decoration: none;">+<em></em></a></td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
    <br>
    '''

def get_user_profile_html(user_data, posts, comments, inviter_name, invitees_list, karma, users_map):
    username = user_data.get('username', 'user')
    user_id = user_data.get('id', 1)
    reg_date_formatted = format_lepra_date(user_data.get('reg_date', '2007-01-01T00:00:00'))
    special_role = user_data.get('special_role') or 'гражданин'
    posts_count = len(posts)
    comments_count = len(comments)
    
    invitees_html = ", ".join([f'<a href="user_{inv["id"]}.html">{inv["username"]}</a>' for inv in invitees_list]) if invitees_list else "никого"
    
    if inviter_name and inviter_name in users_map:
        inv_user = users_map[inviter_name]
        inviter_html = f'<a href="user_{inv_user["id"]}.html">{inv_user["username"]}</a>'
    else:
        inviter_html = "Система (первородный)"

    posts_list_html = "".join([f'<li style="margin-bottom: 6px;"><a href="../post_{p[0]}.html">Пост #{p[0]}</a> ({p[4]:+d})</li>' for p in posts[:15]])

    return f'''
    <div class="dt" style="background: #fff; padding: 20px; margin-bottom: 20px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td width="220" valign="top" style="padding-right: 20px;">
                    <div style="background: #fff; padding: 5px; margin-bottom: 15px; text-align: center;">
                        <img src="https://picsum.photos/180/180?random={user_id}" style="width: 100%; height: auto; display: block;" alt="avatar">
                        <div style="margin-top: 8px; font-style: italic; font-size: 11px; color: #666;">«Лепра никогда не меняется»</div>
                    </div>
                    <div style="font-size: 11px; color: #444; line-height: 1.5; padding: 10px; background: #fafafa;">
                        <p style="margin: 0 0 8px 0;"><strong>Приглашение:</strong><br>от {inviter_html}</p>
                        <p style="margin: 0;"><strong>Привел за руку:</strong><br>{invitees_html}</p>
                    </div>
                </td>
                
                <td valign="top">
                    <h2 style="margin: 0 0 5px 0; font-size: 24px; font-weight: bold; color: #000;">{username}</h2>
                    <div style="color: #666; font-size: 12px; margin-bottom: 15px;">#{user_id}, с нами с {reg_date_formatted} | Статус: <strong>{special_role}</strong></div>
                    
                    <div style="margin-bottom: 15px;">
                        <button style="background: #f0f0f0; border: 1px solid #999; padding: 3px 10px; cursor: pointer; font-size: 12px;">Написать инбокс</button>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 12px; margin-bottom: 20px; font-size: 13px; line-height: 1.5;">
                        <p style="margin: 0 0 5px 0;">Написал <strong>{posts_count} постов</strong> и <strong>{comments_count} комментариев</strong>.</p>
                        <p style="margin: 0;">Общий рейтинг (Карма): <strong style="color: #000;">{karma}</strong></p>
                    </div>
                    
                    <h3 style="font-size: 14px; font-weight: bold; margin: 0 0 10px 0; padding-bottom: 3px;">Последние посты пользователя:</h3>
                    <ul style="padding-left: 20px; font-size: 13px; line-height: 1.6; margin: 0;">
                        {posts_list_html if posts_list_html else '<li>Постов пока нет</li>'}
                    </ul>
                </td>
            </tr>
        </table>
    </div>
    '''

def render_user_profiles():
    snapshot_file = "lepra_snapshot.json"
    if not os.path.exists(snapshot_file): return
    
    with open(snapshot_file, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
        
    users = snapshot.get("users", [])
    users_map_by_id = {u['id']: u for u in users}
    users_map_by_name = {u['username']: u for u in users}
    karma_cache = snapshot.get("karma_cache", {})
    
    users_dir = "users"
    os.makedirs(users_dir, exist_ok=True)
    
    if not os.path.exists(DB_NAME): return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        base_template = f.read()

    actual_users_str = get_user_count()
    sim_datetime_str = get_simulation_datetime()
    
    for u in users:
        u_id = u['id']
        
        cursor.execute("SELECT id, post_type, timestamp, text, rating FROM posts WHERE author_id = ? ORDER BY timestamp DESC", (u_id,))
        posts = cursor.fetchall()
        
        cursor.execute("SELECT id, post_id, text, timestamp FROM comments WHERE author_id = ? ORDER BY timestamp DESC", (u_id,))
        comments = cursor.fetchall()
        
        creator_id = u.get('creator_id')
        inviter_name = users_map_by_id.get(creator_id, {}).get('username') if creator_id else None
        
        invitees = [other for other in users if other.get('creator_id') == u_id]
        karma = karma_cache.get(str(u_id), 0)
        
        profile_content = get_user_profile_html(u, posts, comments, inviter_name, invitees, karma, users_map_by_name)
        
        page_html = base_template \
            .replace("{{ROOT}}", "../") \
            .replace("{{TOTAL_USERS}}", actual_users_str) \
            .replace("{{DATETIME}}", sim_datetime_str) \
            .replace("{{CONTENT}}", profile_content) \
            .replace("{{NAV}}", '<a href="../index.html">← На главную глагне</a>')
            
        with open(os.path.join(users_dir, f"user_{u_id}.html"), "w", encoding="utf-8") as f:
            f.write(page_html)
            
    conn.close()

def render_full_db_to_html():
    if not os.path.exists(DB_NAME) or not os.path.exists(TEMPLATE_FILE): return

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        base_html = f.read()

    actual_users_str = get_user_count()
    sim_datetime_str = get_simulation_datetime()

    # Для корневых страниц заменяем {{ROOT}} на пустую строку
    root_base_html = base_html \
        .replace("{{ROOT}}", "") \
        .replace("{{TOTAL_USERS}}", actual_users_str) \
        .replace("{{DATETIME}}", sim_datetime_str)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM posts")
    total_posts = cursor.fetchone()[0]
    total_pages = math.ceil(total_posts / POSTS_PER_PAGE) if total_posts > 0 else 1
    
    for page in range(total_pages):
        cursor.execute("""
            SELECT p.id, p.author_id, p.author_name, p.post_type, p.rating, p.media_url, p.text, p.timestamp
            FROM posts p
            LEFT JOIN (SELECT post_id, MAX(timestamp) as last_comment_time FROM comments GROUP BY post_id) c 
            ON p.id = c.post_id
            ORDER BY COALESCE(c.last_comment_time, p.timestamp) DESC
            LIMIT ? OFFSET ?
        """, (POSTS_PER_PAGE, page * POSTS_PER_PAGE))
        posts = cursor.fetchall()
        post_blocks = []
        for p in posts:
            p_id, author_id, author_name, p_type, rating, media_url, text, timestamp = p
            cursor.execute("SELECT count(*) FROM comments WHERE post_id=?", (p_id,))
            c_count = cursor.fetchone()[0]
            post_blocks.append(get_post_summary_html(p_id, author_id, author_name, p_type, rating, c_count, format_lepra_date(timestamp), media_url, text))

        paginator_html = generate_paginator_html(page, total_pages)
        filename = get_page_filename(page)
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(root_base_html.replace("{{CONTENT}}", "".join(post_blocks) + paginator_html).replace("{{NAV}}", ""))

    cursor.execute("SELECT id, author_id, author_name, post_type, rating, media_url, text, timestamp FROM posts")
    all_posts = cursor.fetchall()
    
    for p in all_posts:
        p_id, author_id, author_name, p_type, rating, media_url, text, timestamp = p
        cursor.execute("SELECT id, author_id, author_name, text, rating, timestamp FROM comments WHERE post_id = ?", (p_id,))
        comments = cursor.fetchall()
        
        f_timestamp = format_lepra_date(timestamp)
        content = get_content_html(p_type, media_url, text, f_timestamp)
        
        comments_html = "".join([get_comment_html(c[0], c[1], c[2], c[3], c[4], format_lepra_date(c[5])) for c in comments])
        full_post = get_full_post_html(p_id, author_id, author_name, p_type, rating, content, comments_html, f_timestamp)
        
        with open(f"post_{p_id}.html", "w", encoding="utf-8") as f:
            f.write(root_base_html.replace("{{CONTENT}}", full_post).replace("{{NAV}}", ""))

    conn.close()
    print(f"[*] Рендеринг постов в корне завершен", flush=True)

    render_user_profiles()
    print(f"[*] Генерация полностью завершена!", flush=True)

if __name__ == "__main__":
    render_full_db_to_html()
# --- END OF FILE render_db.py ---
