from lepra_shared import GlobalState
import sys

VERBOSE_MODE = False

def set_verbose(value: bool):
    global VERBOSE_MODE
    VERBOSE_MODE = value

def log_d(msg, style=None, important=False):
    """Журналирование с поддержкой сайлент-режима."""
    # Если не verbose и не важное событие — молчим
    if not VERBOSE_MODE and not important:
        return

    styles = {
        "system": "\033[1;36m",
        "user": "\033[0;37m",
        "post": "\033[0;33m",
        "action": "\033[0;32m",
        "neg": "\033[0;31m",
        "admin": "\033[1;35m",
        "alert": "\033[1;41;37m"
    }

    if not style:
        if "SYSTEM" in msg or "REG_WAVE" in msg: style = "system"
        elif "POST" in msg or "ЗОЛОТО" in msg: style = "post"
        elif "KARMA" in msg and "+" in msg: style = "action"
        elif "KARMA" in msg and "-" in msg: style = "neg"
        elif "MOD" in msg or "ELECTION" in msg: style = "admin"
        elif "СЛИВ" in msg or "!!! " in msg: style = "alert"
        else: style = "user"

    color = styles.get(style, "\033[0m")
    reset = "\033[0m"
    
    time_str = GlobalState.current_sim_date.strftime('%H:%M:%S')
    formatted_msg = f"[{time_str}] {color}{msg}{reset}"
    
    GlobalState.daily_journal.append(formatted_msg)
    if len(GlobalState.daily_journal) > 1000:
        GlobalState.daily_journal.pop(0)
        
    print(formatted_msg, flush=True)
