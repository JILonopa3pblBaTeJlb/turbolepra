
import sys
from lepra_shared import GlobalState

def visualize():
    """Выводит статусную строку без затирания логов."""
    now = GlobalState.current_sim_date
    s = GlobalState.stats_today
    
    # Используем цветную рамку, чтобы статус выделялся в потоке логов
    status_line = (
        f"\n\033[44;37m >> СТАТУС СИСТЕМЫ | {now.strftime('%Y-%m-%d %H:%M')} | "
        f"Юзеров: {len(GlobalState.users)} | Золото: {GlobalState.golden_posts_count} | "
        f"Посты: {s['posts']} | Комменты: {s['comments']} | Голоса: {s['votes']} << \033[0m\n"
    )
    
    sys.stdout.write(status_line)
    sys.stdout.flush()
