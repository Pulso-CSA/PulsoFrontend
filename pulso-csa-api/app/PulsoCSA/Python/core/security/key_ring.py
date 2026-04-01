#━━━━━━━━━❮Key Ring – Chave Rotativa + Double-Buffer❯━━━━━━━━━
"""
Sistema de chave rotativa a cada 6h com:
- HKDF-SHA384 para derivação (pós-quântico)
- Lista de 20 palavras como seed
- Double-buffer: current + previous (grace period)
- Sem conflito durante rotação (operações longas preservadas)
"""
from __future__ import annotations

import hashlib
import os
import random
import threading
import time
from dataclasses import dataclass
from typing import Optional

# HKDF via cryptography (fallback: hashlib para HKDF manual se cryptography não disponível)
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.backends import default_backend

    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False


# ═══════════════════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════════════════
WINDOW_SECONDS = 6 * 60 * 60  # 6 horas
INFO_CONTEXT = b"pulso-api-key-v1"  # context para HKDF
KEY_LENGTH = 48  # 384 bits para HS384
CLOCK_SKEW_TOLERANCE = 300  # ±5 min tolerância


@dataclass
class KeySlot:
    """Slot de chave com metadados."""
    key_id: str
    key_bytes: bytes
    epoch: int
    issued_at: float
    expires_at: float


def _hkdf_sha384(salt: bytes, ikm: bytes, length: int = KEY_LENGTH) -> bytes:
    """Deriva chave via HKDF-SHA384."""
    if _HAS_CRYPTOGRAPHY:
        hkdf = HKDF(
            algorithm=hashes.SHA384(),
            length=length,
            salt=salt,
            info=INFO_CONTEXT,
            backend=default_backend(),
        )
        return hkdf.derive(ikm)
    # Fallback: HKDF-Extract + Expand (RFC 5869) usando SHA384
    prk = _hkdf_extract_sha384(salt, ikm)
    return _hkdf_expand_sha384(prk, length)


def _hkdf_extract_sha384(salt: bytes, ikm: bytes) -> bytes:
    """HKDF-Extract: PRK = HMAC-Hash(salt, IKM)."""
    import hmac
    s = salt if salt else b"\x00" * 48
    return hmac.new(s, ikm, hashlib.sha384).digest()


def _hkdf_expand_sha384(prk: bytes, length: int) -> bytes:
    """HKDF-Expand (RFC 5869): OKM = T(1)|T(2)|... com T(i)=HMAC(PRK, T(i-1)|info|i)."""
    import hmac
    okm = b""
    n = (length + 47) // 48
    t = b""
    for i in range(1, n + 1):
        block = hmac.new(prk, t + INFO_CONTEXT + bytes([i]), hashlib.sha384).digest()
        t = block
        okm += block
    return okm[:length]


def _get_epoch() -> int:
    """Epoch da janela atual (6h)."""
    return int(time.time() // WINDOW_SECONDS)


def _epoch_to_key_id(epoch: int) -> str:
    """Gera key_id determinístico a partir do epoch."""
    h = hashlib.sha384(f"pulso-kid-{epoch}".encode()).hexdigest()
    return h[:16]


def _derive_key(epoch: int, seed_word: str) -> tuple[str, bytes]:
    """Deriva chave a partir de epoch e palavra seed. Suporta Unicode (ç, ã, etc.)."""
    salt = f"pulso-salt-{epoch}".encode("utf-8")
    ikm = seed_word.encode("utf-8")
    key_bytes = _hkdf_sha384(salt, ikm)
    key_id = _epoch_to_key_id(epoch)
    return key_id, key_bytes


# ═══════════════════════════════════════════════════════════════════════════
# KeyRing
# ═══════════════════════════════════════════════════════════════════════════

class KeyRing:
    """
    Gerenciador de chaves rotativas com double-buffer.
    Aceita current e previous para evitar quebra durante rotação.
    """

    def __init__(self, seed_words: list[str]):
        if len(seed_words) < 1:
            raise ValueError("Pelo menos 1 palavra seed é necessária")
        self._seed_words = [w.strip() for w in seed_words if w.strip()]
        self._lock = threading.RLock()
        self._current: Optional[KeySlot] = None
        self._previous: Optional[KeySlot] = None
        self._last_rotation_epoch: int = -1

    def _pick_random_word(self) -> str:
        """Escolhe palavra aleatória da lista."""
        return random.SystemRandom().choice(self._seed_words)

    def _ensure_rotated(self) -> None:
        """Garante que current e previous estão atualizados para a janela vigente."""
        with self._lock:
            now = time.time()
            epoch = _get_epoch()
            if self._last_rotation_epoch == epoch and self._current:
                return
            # Rotação: previous = current, current = nova
            if self._current and self._current.epoch == epoch - 1:
                self._previous = self._current
            elif self._current and self._current.epoch < epoch - 1:
                # Janela anterior já expirou; mantém previous por grace period
                self._previous = self._current
            word = self._pick_random_word()
            # Debug: só exibe com KEY_RING_DEBUG=1 (nunca em produção)
            if os.getenv("KEY_RING_DEBUG", "").lower() in ("1", "true", "yes"):
                print(f"[KeyRing] Palavra escolhida para janela atual: {word!r}")
            key_id, key_bytes = _derive_key(epoch, word)
            issued = epoch * WINDOW_SECONDS
            expires = (epoch + 2) * WINDOW_SECONDS + CLOCK_SKEW_TOLERANCE
            self._current = KeySlot(
                key_id=key_id,
                key_bytes=key_bytes,
                epoch=epoch,
                issued_at=issued,
                expires_at=expires,
            )
            if not self._previous or self._previous.epoch < epoch - 1:
                # Preenche previous com chave da janela anterior
                prev_word = self._pick_random_word()
                if os.getenv("KEY_RING_DEBUG", "").lower() in ("1", "true", "yes"):
                    print(f"[KeyRing] Palavra escolhida para janela anterior: {prev_word!r}")
                prev_id, prev_bytes = _derive_key(epoch - 1, prev_word)
                prev_issued = (epoch - 1) * WINDOW_SECONDS
                prev_expires = epoch * WINDOW_SECONDS + CLOCK_SKEW_TOLERANCE
                self._previous = KeySlot(
                    key_id=prev_id,
                    key_bytes=prev_bytes,
                    epoch=epoch - 1,
                    issued_at=prev_issued,
                    expires_at=prev_expires,
                )
            self._last_rotation_epoch = epoch

    def get_current_key(self) -> tuple[str, bytes]:
        """Retorna (key_id, key_bytes) da chave atual."""
        self._ensure_rotated()
        with self._lock:
            if not self._current:
                raise RuntimeError("KeyRing não inicializado")
            return self._current.key_id, self._current.key_bytes

    def get_keys_for_validation(self) -> list[tuple[str, bytes]]:
        """
        Retorna lista de (key_id, key_bytes) para validação.
        Ordem: [current, previous] — aceita ambos durante grace period.
        """
        self._ensure_rotated()
        with self._lock:
            result = []
            if self._current:
                result.append((self._current.key_id, self._current.key_bytes))
            if self._previous and self._previous.key_id != (self._current.key_id if self._current else ""):
                result.append((self._previous.key_id, self._previous.key_bytes))
            return result

    def get_key_by_id(self, key_id: str) -> Optional[bytes]:
        """Retorna key_bytes para um key_id conhecido, ou None."""
        keys = self.get_keys_for_validation()
        for kid, kbytes in keys:
            if kid == key_id:
                return kbytes
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Singleton / Factory
# ═══════════════════════════════════════════════════════════════════════════

_key_ring_instance: Optional[KeyRing] = None
_key_ring_lock = threading.Lock()


def get_key_ring() -> KeyRing:
    """
    Retorna instância singleton do KeyRing.
    Suporta palavras com caracteres Unicode (ç, ã, á, etc.).
    """
    global _key_ring_instance
    if _key_ring_instance is None:
        with _key_ring_lock:
            if _key_ring_instance is None:
                words_str = os.getenv("KEY_SEED_WORDS", "")
                if isinstance(words_str, bytes):
                    words_str = words_str.decode("utf-8")
                if not words_str:
                    fallback = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
                    if fallback:
                        words_str = fallback  # fallback para compatibilidade
                    else:
                        raise RuntimeError(
                            "KEY_SEED_WORDS ou JWT_SECRET deve estar definido no ambiente"
                        )
                words = [w.strip() for w in words_str.replace(",", " ").split() if w.strip()]
                if len(words) < 1:
                    words = [words_str]
                _key_ring_instance = KeyRing(words)
    return _key_ring_instance
