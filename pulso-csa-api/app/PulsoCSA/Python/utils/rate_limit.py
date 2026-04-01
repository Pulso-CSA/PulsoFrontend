#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Rate limit (IP) e métricas por usuário❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import threading
import time
from collections import defaultdict
from typing import Dict, List, Tuple

# Limite por IP: requisições por minuto (janela deslizante).
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "120"))
RATE_LIMIT_WINDOW_SEC = 60

# Limite por usuário (opcional): ex.: 60 req/min por usuario.
# Padrão ativado: 100 req/min por usuário (configurável via env)
RATE_LIMIT_PER_USER_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_USER_PER_MINUTE", "100"))  # Padrão: 100 req/min

# Estado: IP -> lista de timestamps (janela deslizante)
_ip_timestamps: Dict[str, List[float]] = {}
_lock = threading.Lock()

# Métricas por usuário: usuario -> (total_requests, last_minute_count, last_reset)
_user_requests: Dict[str, List[float]] = defaultdict(list)
_user_lock = threading.Lock()


def _prune_old(timestamps: List[float], window_sec: float) -> None:
    """Remove timestamps fora da janela."""
    cutoff = time.monotonic() - window_sec
    while timestamps and timestamps[0] < cutoff:
        timestamps.pop(0)


def check_rate_limit_ip(ip: str) -> Tuple[bool, int]:
    """
    Verifica rate limit por IP. Retorna (allowed, current_count_após_esta).
    Se allowed=False, o request deve retornar 429 (a requisição não é contada).
    """
    with _lock:
        now = time.monotonic()
        if ip not in _ip_timestamps:
            _ip_timestamps[ip] = []
        _prune_old(_ip_timestamps[ip], RATE_LIMIT_WINDOW_SEC)
        count = len(_ip_timestamps[ip])
        if count >= RATE_LIMIT_REQUESTS_PER_MINUTE:
            return (False, count)
        _ip_timestamps[ip].append(now)
        return (True, count + 1)


def check_rate_limit_user(usuario: str) -> Tuple[bool, int]:
    """
    Verifica rate limit por usuário (se RATE_LIMIT_PER_USER_PER_MINUTE > 0).
    Retorna (allowed, current_count_no_minuto). Só leitura; não registra a requisição.
    """
    if RATE_LIMIT_PER_USER_PER_MINUTE <= 0:
        return (True, 0)
    with _user_lock:
        _prune_old(_user_requests[usuario], RATE_LIMIT_WINDOW_SEC)
        count = len(_user_requests[usuario])
        if count >= RATE_LIMIT_PER_USER_PER_MINUTE:
            return (False, count)
        return (True, count)


def record_user_request(usuario: str) -> None:
    """Registra uma requisição do usuário (métricas e contagem para rate limit por user)."""
    with _user_lock:
        _user_requests[usuario].append(time.monotonic())
        _prune_old(_user_requests[usuario], RATE_LIMIT_WINDOW_SEC)


def get_user_usage(usuario: str) -> Dict[str, int]:
    """
    Retorna métricas de uso do usuário: requests na última minuto e total (desde último reset do processo).
    """
    with _user_lock:
        _prune_old(_user_requests[usuario], RATE_LIMIT_WINDOW_SEC)
        last_minute = len(_user_requests[usuario])
        total = len(_user_requests[usuario])  # após prune, só tem última janela; para total real seria preciso persistir
    return {"requests_last_minute": last_minute, "requests_in_window": last_minute}


def get_all_users_usage() -> Dict[str, Dict[str, int]]:
    """Retorna uso de todos os usuários vistos (para admin/dashboard)."""
    with _user_lock:
        result = {}
        for user, ts_list in list(_user_requests.items()):
            _prune_old(ts_list, RATE_LIMIT_WINDOW_SEC)
            result[user] = {"requests_last_minute": len(ts_list)}
        return result
