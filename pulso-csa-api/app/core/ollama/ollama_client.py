#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Cliente Ollama – Mistral (interpretação) + Qwen (execução)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Interface compatível com OpenAIClient.generate_text().
use_fast_model=True  → modelo de interpretação (RAG, blueprint, JSON longo)
use_fast_model=False → modelo de execução (código)

Em RAM limitada (Railway, etc.), Mistral 7B costuma receber SIGKILL (OOM). Por isso, se
RAILWAY_ENVIRONMENT ou OLLAMA_LOW_MEMORY=1 e OLLAMA_MODEL_INTERPRETACAO não foi definido,
o padrão de interpretação passa a ser o mesmo de execução (Qwen 3B).
"""

import os
import threading
from typing import Optional

# Modelos padrão (quantizados Q4)
MODEL_EXECUCAO = os.getenv("OLLAMA_MODEL_EXECUCAO", "qwen2.5-coder:3b-base-q4_K_M").strip() or "qwen2.5-coder:3b-base-q4_K_M"


def _default_model_interpretacao() -> str:
    explicit = os.getenv("OLLAMA_MODEL_INTERPRETACAO", "").strip()
    if explicit:
        return explicit
    low_mem = os.getenv("OLLAMA_LOW_MEMORY", "").strip().lower() in ("1", "true", "yes")
    railway = bool(os.getenv("RAILWAY_ENVIRONMENT", "").strip())
    if low_mem or railway:
        return MODEL_EXECUCAO
    return "mistral:7b-instruct-q4_K_M"


MODEL_INTERPRETACAO = _default_model_interpretacao()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_TIMEOUT_SEC = int(os.getenv("OLLAMA_TIMEOUT_SEC", "360"))
# num_predict para classificação (resposta curta JSON) — acelera
NUM_PREDICT_CLASSIFICATION = int(os.getenv("OLLAMA_NUM_PREDICT_CLASSIFICATION", "128"))

_ollama_client_instance = None
_ollama_client_lock = threading.Lock()
_llm_fast_instance = None
_llm_fast_lock = threading.Lock()


def get_ollama_client() -> "OllamaClient":
    """Retorna instância do cliente Ollama."""
    return OllamaClient()


def _get_ollama_http_client():
    """Singleton do Client HTTP Ollama (reutiliza conexão)."""
    global _ollama_client_instance
    if _ollama_client_instance is None:
        with _ollama_client_lock:
            if _ollama_client_instance is None:
                try:
                    from ollama import Client
                    _ollama_client_instance = Client(
                        host=OLLAMA_HOST.rstrip("/"),
                        timeout=OLLAMA_TIMEOUT_SEC,
                    )
                except ImportError:
                    return None
    return _ollama_client_instance


class OllamaClient:
    """
    Cliente Ollama com interface generate_text() compatível com OpenAIClient.
    Nunca armazena chaves; usa modelos locais gratuitos.
    """

    def __init__(
        self,
        model_interpretacao: str = MODEL_INTERPRETACAO,
        model_execucao: str = MODEL_EXECUCAO,
        host: str = OLLAMA_HOST,
    ):
        self._model_interpretacao = model_interpretacao
        self._model_execucao = model_execucao
        self._host = host.rstrip("/")

    @property
    def llm_fast(self):
        """
        LLM LangChain (ChatOllama) para uso em RAG, RetrievalQA e análises leves.
        Usa langchain_ollama (recomendado); fallback para langchain_community se não instalado.
        """
        global _llm_fast_instance, _llm_fast_lock
        if _llm_fast_instance is None:
            with _llm_fast_lock:
                if _llm_fast_instance is None:
                    try:
                        from langchain_ollama import ChatOllama
                    except ImportError:
                        import warnings
                        warnings.filterwarnings("ignore", message=".*ChatOllama.*deprecated.*", category=DeprecationWarning)
                        from langchain_community.chat_models.ollama import ChatOllama
                    _np = int(os.getenv("OLLAMA_CHAT_NUM_PREDICT", "2048"))
                    _llm_fast_instance = ChatOllama(
                        model=self._model_interpretacao,
                        base_url=self._host,
                        temperature=0.7,
                        num_predict=max(256, min(_np, 8192)),
                    )
        return _llm_fast_instance

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_override: Optional[int] = None,
        temperature_override: Optional[float] = None,
        use_fast_model: bool = False,
        num_predict: Optional[int] = None,
    ) -> str:
        """
        Gera texto via Ollama.
        use_fast_model=True  → Mistral (interpretação)
        use_fast_model=False → Qwen (execução)
        num_predict: limita tokens de saída (ex.: 128 para classificação) — acelera.
        """
        model = self._model_interpretacao if use_fast_model else self._model_execucao
        task_type = "interpretação" if use_fast_model else "execução"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        options = None
        if num_predict is not None and num_predict > 0:
            options = {"num_predict": num_predict}
        elif use_fast_model and len((prompt or "") + (system_prompt or "")) < 800:
            options = {"num_predict": NUM_PREDICT_CLASSIFICATION}

        import time
        t0 = time.perf_counter()
        try:
            from app.utils.log_manager import add_log
            _n = len(prompt or "") + len(system_prompt or "")
            add_log("info", f"Ollama: {model} ({task_type}) iniciado | total_chars≈{_n} | num_predict={options}", "ollama")
        except Exception:
            pass

        timeout_sec = timeout_override if timeout_override is not None and timeout_override > 0 else OLLAMA_TIMEOUT_SEC
        client = _get_ollama_http_client()
        if client is None:
            return (
                "Erro: pacote 'ollama' não instalado. Execute: pip install ollama. "
                "Em seguida: ollama pull qwen2.5-coder:3b-base-q4_K_M "
                "(e, se usar Mistral para interpretação: ollama pull mistral:7b-instruct-q4_K_M)."
            )
        # Timeout maior por requisição: usar cliente com timeout_override para evitar ReadTimeout em prompts longos
        if timeout_override is not None and timeout_override > 0:
            try:
                from ollama import Client
                client = Client(host=self._host.rstrip("/"), timeout=timeout_sec)
            except ImportError:
                pass
        last_err = None
        for attempt in range(3):
            try:
                response = client.chat(model=model, messages=messages, options=options)
                content = response.message.content if response and response.message else ""
                elapsed = time.perf_counter() - t0
                try:
                    from app.utils.log_manager import add_log
                    add_log("info", f"Ollama: {model} ({task_type}) concluído em {elapsed:.1f}s", "ollama")
                except Exception:
                    pass
                return (content or "").strip()
            except Exception as e:
                last_err = e
                if attempt < 2 and ("timeout" in str(e).lower() or "timed out" in str(e).lower()):
                    import time
                    time.sleep(2 * (attempt + 1))
                    continue
                break
        elapsed = time.perf_counter() - t0
        try:
            from app.utils.log_manager import add_log
            add_log("error", f"Ollama ({model}) falhou após {elapsed:.1f}s: {type(last_err).__name__}: {str(last_err)[:200]}", "ollama")
        except Exception:
            pass
        hint = ""
        err_s = str(last_err or "").lower()
        if "killed" in err_s or "signal" in err_s:
            hint = (
                " Se o processo foi morto (signal: killed), é provável falta de RAM no host do Ollama: "
                "defina OLLAMA_LOW_MEMORY=1 ou use apenas qwen (já é o padrão no Railway sem OLLAMA_MODEL_INTERPRETACAO), "
                "ou suba memória / use OPENAI_API_KEY."
            )
        return (
            "Erro ao gerar texto com Ollama. Verifique se o Ollama está rodando e os modelos estão instalados. "
            "Se ocorrer timeout, aumente OLLAMA_TIMEOUT_SEC no ambiente (ex.: 180)." + hint
        )
