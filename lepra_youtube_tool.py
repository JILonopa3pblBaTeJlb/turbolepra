from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str) -> str:
    """Извлекает YouTube video ID из ссылки любой формы."""
    url = url.strip()
    if not url: return None

    parsed = urlparse(url)
    
    # 1. youtube.com/watch?v=...
    if "youtube.com" in parsed.netloc:
        query = parse_qs(parsed.query)
        if "v" in query: return query["v"][0]
        # 2. youtube.com/embed/...
        if "/embed/" in parsed.path: return parsed.path.split("/embed/")[-1]

    # 3. youtu.be/...
    if "youtu.be" in parsed.netloc:
        return parsed.path.lstrip("/")

    return None

def render_youtube_embed(url: str) -> str:
    """Генерирует embed-виджет с использованием nocookie и origin."""
    video_id = extract_video_id(url)
    
    if not video_id:
        return f'<a href="{url}">{url}</a>'
    
    # Используем youtube-nocookie.com и передаем origin
    # origin=http://localhost заставляет YouTube думать, что он работает в контролируемой среде
    embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?origin=http://localhost&rel=0"
    
    return f'''<iframe width="560" height="315" 
src="{embed_url}" 
title="YouTube video player" 
frameborder="0" 
allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
referrerpolicy="strict-origin-when-cross-origin" 
allowfullscreen></iframe>'''
