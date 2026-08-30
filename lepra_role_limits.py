from lepra_shared import GlobalState

def check_role_limits(role: str, pol_x: float, gender: str = "male") -> bool:
    """Проверяет, можно ли назначить роль согласно динамическим лимитам."""
    active_users = [u for u in GlobalState.users if u.special_role == role and not
    u.is_banned and u.karma > -1000]

    match role:
        case "графоманя":
            return len(active_users) < 1
        case "пашкет":
            # Музыкальный графоманя аналогичен обычному
            return len(active_users) < 1
        case "rupee":
            return len(active_users) < 1
        case "шиз":
            # Используем динамический лимит, вычисленный в RoleManager
            return len(active_users) < GlobalState.shiz_limit
        case "сиськарий":
            is_vatan = pol_x > 0.7
            for u in active_users:
                u_is_vatan = u.pol_x > 0.7
                if u_is_vatan == is_vatan:
                    return False
            return len(active_users) < 2
        case "мем-лорд":
            return len(active_users) < 2
        case "dramqueen":
            if gender != "female":
                return False
            return len(active_users) < 4
        case "ханя" | "королева":
            return len(active_users) < 1
        
    return True
