# --- START OF FILE lepra_sim_airdrop.py ---
import random
from lepra_shared import GlobalState
from lepra_logger import log_d

def do_jovan_airdrop():
    """Событие раздачи инвайтов Йованом."""
    now = GlobalState.current_sim_date
    if now.hour == 0 and random.random() < (2 / 365.0):
        drop_amount = 0
        for u in GlobalState.users:
            gift = random.randint(1, 3)
            u.invites += gift
            drop_amount += gift
        
        log_d(f"\033[1;33m!!! JOVAN AIRDROP: Йован проснулся и раздал {drop_amount} инвайтов всему Гнезду !!!\033[0m")
# --- END OF FILE lepra_sim_airdrop.py ---
