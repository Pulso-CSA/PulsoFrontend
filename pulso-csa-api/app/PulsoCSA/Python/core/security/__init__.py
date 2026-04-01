#━━━━━━━━━❮Core Security – Chave Rotativa + PQC❯━━━━━━━━━
"""
Módulo de segurança: chave rotativa com HKDF-SHA384, double-buffer (grace period),
compatível com operações longas e múltiplas instâncias.
"""
from core.security.key_ring import KeyRing, get_key_ring

__all__ = ["KeyRing", "get_key_ring"]
