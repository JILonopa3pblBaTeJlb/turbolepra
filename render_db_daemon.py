# --- START OF FILE render_daemon.py ---

import os
import time
import sys
from datetime import datetime
from render_db import render_full_db_to_html, DB_NAME

def log_message(msg: str) -> None:
    """Выводит логи демона с текущей временной меткой."""
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{time_str}] [RENDER DAEMON] {msg}", flush=True)

def watch_database(db_path: str = DB_NAME, interval: float = 1.0) -> None:
    """Следит за изменением времени модификации (mtime) базы данных и запускает рендеринг."""
    if not os.path.exists(db_path):
        log_message(f"База данных {db_path} не найдена. Ожидание появления файла...")
        while not os.path.exists(db_path):
            time.sleep(2.0)

    last_mtime = os.path.getmtime(db_path)
    log_message(f"Запущено наблюдение за файлом '{db_path}'. Интервал проверки: {interval} сек.")

    # Первичный прогон при старте демона
    try:
        log_message("Выполнение начального рендеринга статики...")
        render_full_db_to_html()
    except Exception as e:
        log_message(f"Ошибка при первичном рендеринге: {e}")

    while True:
        try:
            time.sleep(interval)
            if not os.path.exists(db_path):
                continue
            
            current_mtime = os.path.getmtime(db_path)
            if current_mtime != last_mtime:
                log_message(f"Зафиксировано обновление базы данных. Пересборка сайта...")
                start_time = time.time()
                
                render_full_db_to_html()
                
                elapsed = time.time() - start_time
                last_mtime = os.path.getmtime(db_path)
                log_message(f"Рендеринг успешно завершен за {elapsed:.2f} сек.")
                
        except Exception as e:
            log_message(f"Ошибка в цикле мониторинга: {e}")

def main() -> None:
    """Точка входа демона авторендеринга."""
    log_message("Инициализация серверной утилиты авторендеринга...")
    try:
        watch_database()
    except KeyboardInterrupt:
        log_message("Демон остановлен пользователем (Ctrl+C).")
        sys.exit(0)

if __name__ == "__main__":
    main()

# --- END OF FILE render_daemon.py ---
