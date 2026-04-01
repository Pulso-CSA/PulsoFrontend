#━━━━━━━━━❮Lock para Retreino❯━━━━━━━━━
# Evita execução duplicada/concorrente de retreinos.
import time
from typing import Dict, Optional
from threading import Lock

# Lock por agendamento_id (em produção usar Redis/DistributedLock)
_RETREINO_LOCKS: Dict[str, tuple[Lock, float]] = {}
_LOCK_CLEANUP_INTERVAL = 300  # 5 minutos


def obter_lock_retreino(agendamento_id: str, timeout_seconds: float = 60.0) -> bool:
    """
    Tenta obter lock para executar retreino.
    Retorna True se conseguiu, False se já está em execução.
    """
    now = time.time()
    # Limpar locks antigos
    if len(_RETREINO_LOCKS) > 100:
        _RETREINO_LOCKS.clear()
    if agendamento_id in _RETREINO_LOCKS:
        lock, timestamp = _RETREINO_LOCKS[agendamento_id]
        if now - timestamp < timeout_seconds:
            return False  # Já está em execução
        else:
            del _RETREINO_LOCKS[agendamento_id]
    lock = Lock()
    acquired = lock.acquire(blocking=False)
    if acquired:
        _RETREINO_LOCKS[agendamento_id] = (lock, now)
    return acquired


def liberar_lock_retreino(agendamento_id: str):
    """Libera o lock após conclusão do retreino."""
    if agendamento_id in _RETREINO_LOCKS:
        lock, _ = _RETREINO_LOCKS[agendamento_id]
        lock.release()
        del _RETREINO_LOCKS[agendamento_id]
