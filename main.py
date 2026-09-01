import sys
import time
import random
import select
import os
import termios
import sqlite3
from datetime import timedelta
import lepra_logger
from lepra_text_processor import TextProcessor
from lepra_shared import GlobalState, BotUser, Inbox, START_BOTS, INTERESTS_POOL, GRAPHOMANIA_NICK_QUEUE
from lepra_db_init import init_db
from lepra_snapshot_loader import load_snapshot
from lepra_snapshot_saver import save_snapshot
from lepra_archive import archive_to_db
from lepra_logger import log_d
from lepra_nickname_gen import generate_nickname
from lepra_role_limits import check_role_limits
from lepra_role_manager import enforce_role_quota, assign_role
from lepra_simulation_engine import run_simulation_step
from lepra_visualizer import visualize
from lepra_tg_tool import get_valid_image_data, get_media_url, load_used_ids, save_used_ids
from lepra_ejik_builder import EjikPostBuilder
from lepra_pashket_builder import PashketBuilder
from lepra_youtube_builder import YouTubePostBuilder
from lepra_anekdot_builder import AnekdotBuilder


def sync_tg_registry():
    """Синхронизирует json-реестр с базой данных."""
    if not os.path.exists("leprosorium.db"): return
    conn = sqlite3.connect("leprosorium.db")
    cursor = conn.cursor()
    cursor.execute("SELECT tg_id FROM posts WHERE tg_id IS NOT NULL")
    existing_ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    used = load_used_ids()
    used.update(existing_ids)
    save_used_ids(used)

def print_daily_summary():
    """Сводный отчет в конце дня."""
    s = GlobalState.stats_today
    posts = [p for p in GlobalState.all_posts if p.timestamp.date() == GlobalState.current_sim_date.date()]
    leg = len([p for p in posts if p.is_legendary])
    gold = len([p for p in posts if p.is_golden])
    drama = len([p for p in posts if p.is_drama])
    
    summary = (
        f"\n=== ИТОГИ ДНЯ {GlobalState.current_sim_date.strftime('%Y-%m-%d')} ===\n"
        f"Посты: {s['posts']} (Легенды: {leg}, Золото: {gold}, Драмы: {drama})\n"
        f"Комментарии: {s['comments']} | Голоса: {s['votes']}\n"
        f"=========================================="
    )
    print(summary)

def main():
    init_db()
    sync_tg_registry()
    """Бэкенд-процесс симуляции с поддержкой логирования в файл и паузы."""
    is_verbose = "-verbose" in sys.argv
    is_profile = "-profile" in sys.argv
    GlobalState.processor = TextProcessor()
    # Инициализация билдеров
    GlobalState.ejik_builder = EjikPostBuilder(GlobalState.processor)
    GlobalState.pashkett_builder = PashketBuilder()
    GlobalState.youtube_builder = YouTubePostBuilder()
    GlobalState.anekdot_builder = AnekdotBuilder()

    if is_verbose:
        lepra_logger.set_verbose(True)
        
    is_log_file = "-log" in sys.argv
    original_stdout = sys.stdout
    log_file = None
    old_settings = None
    
    if is_log_file:
        log_file = open("simulation.log", "w", encoding="utf-8")
        sys.stdout = log_file

    try:
        
        
        # 1. Инициализация инбоксов
        vatany = Inbox("Ватаны", "патриотизм")
        divany = Inbox("Диваны", "либерализм")
        fem_help = Inbox("Я баба помогите", "феминизм")
        shovi = Inbox("Шови", "шовинизм")
        interest_inboxes = [Inbox(interest.capitalize(), interest) for interest in INTERESTS_POOL]
        GlobalState.inboxes = [vatany, divany, fem_help, shovi] + interest_inboxes
        
        if not load_snapshot():
            # Инициализация демиургов
            hanya = BotUser(username="temp_hanya", gender="male")
            GlobalState.users.append(hanya)
            GlobalState.users_map[hanya.id] = hanya
            assign_role(hanya, "ханя")
            

            
            for _ in range(START_BOTS):
                new_gender = "female" if random.random() < 0.2 else "male"
                u = BotUser(gender=new_gender)
                u.username = generate_nickname(gender=new_gender)
                
                # Назначаем роли при старте
                if random.random() < 0.15:
                    role_to_assign = random.choice(["графоманя", "шиз", "сиськарий", "мем-лорд", "rupee", "dramqueen", "пашкет"])
                    if check_role_limits(role_to_assign, u.pol_x, gender=u.gender):
                        assign_role(u, role_to_assign)
                                    
                if u.pol_x > 0.5: u.inbox_ids.append(id(vatany))
                else: u.inbox_ids.append(id(divany))
                for ib in interest_inboxes:
                    if ib.primary_interest in u.interests: u.inbox_ids.append(id(ib))
                    
                GlobalState.users.append(u)
                GlobalState.users_map[u.id] = u
                
            GlobalState.used_nicknames = {u.username for u in GlobalState.users}

        paused = False
        iteration = 0
        while True:
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                char = sys.stdin.read(1)
                if char == ' ':
                    paused = not paused
                    status_msg = f"\n--- {'ПАУЗА' if paused else 'ПРОДОЛЖЕНИЕ'} ---\n"
                    original_stdout.write(status_msg)
                    if log_file: log_file.write(status_msg)
            
            if paused:
                time.sleep(0.1)
                continue

            if is_log_file: sys.stdout = log_file
            
            run_simulation_step()
            
            if GlobalState.current_sim_date.hour == 0:
                print_daily_summary()
                archive_to_db(GlobalState.all_posts)
                save_snapshot()
            
            GlobalState.current_sim_date += timedelta(hours=1)
            
            if iteration % 4 == 0:
                sys.stdout = original_stdout
                visualize()
                
            iteration += 1
            
    except KeyboardInterrupt:
        save_snapshot()
        print("\n[!] Симуляция остановлена.")
    finally:
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        if log_file: log_file.close()
        sys.stdout = original_stdout

if __name__ == "__main__":
    main()
