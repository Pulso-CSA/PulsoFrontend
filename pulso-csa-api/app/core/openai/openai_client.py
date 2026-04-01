#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import os
import threading
from typing import Optional, Union

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# .env é carregado em main.py antes de qualquer import que use OpenAI (padrão Stripe).

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Configuração (sem expor chave em log/print)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _get_openai_config(api_key_override: Optional[str] = None):
    """Lê config da OpenAI. api_key_override: chave do request (BYOK); senão usa env."""
    api_key = api_key_override or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada (env ou request).")
    return {
        "api_key": api_key,
        "model": os.getenv("OPENAI_MODEL", "o3"),
        "model_fast": os.getenv("OPENAI_MODEL_FAST", "gpt-4o-mini"),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "1.0")),
        "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        "timeout": int(os.getenv("OPENAI_REQUEST_TIMEOUT", "360")),
    }


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Singleton (uma instância por processo)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

_instance: Optional["OpenAIClient"] = None
_lock = threading.Lock()
_ollama_instance: Optional["OllamaClient"] = None
_ollama_lock = threading.Lock()
_llm_provider_logged = False


def get_openai_client(api_key_override: Optional[str] = None) -> Union["OpenAIClient", "OllamaClient"]:
    """
    Retorna cliente LLM para geração de texto.
    - USE_OLLAMA=1 no .env → força Ollama (ignora chave)
    - Se api_key no request (BYOK) ou OPENAI_API_KEY no env → OpenAIClient
    - Se nenhuma chave → OllamaClient (Mistral + Qwen, gratuito)
    Nunca armazena chaves em banco.
    """
    global _instance, _ollama_instance, _ollama_lock, _llm_provider_logged
    from app.core.llm import get_request_api_key
    from app.core.ollama.ollama_client import OllamaClient

    request_key = get_request_api_key()
    byok_key = api_key_override or request_key
    use_ollama = os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes")
    env_key = None if use_ollama else os.getenv("OPENAI_API_KEY")
    api_key = byok_key or env_key

    if use_ollama and not byok_key:
        with _ollama_lock:
            if _ollama_instance is None:
                _ollama_instance = OllamaClient()
            if not _llm_provider_logged:
                try:
                    from app.utils.log_manager import add_log
                    add_log("info", "LLM: Ollama forçado (USE_OLLAMA=1)", "llm_provider")
                    _llm_provider_logged = True
                except Exception:
                    pass
        return _ollama_instance

    if api_key:
        if not api_key_override and not request_key:
            if _instance is None:
                with _lock:
                    if _instance is None:
                        _instance = OpenAIClient()
                        try:
                            from app.utils.log_manager import add_log
                            add_log("info", "LLM: OpenAI (env)", "llm_provider")
                        except Exception:
                            pass
            return _instance
        return OpenAIClient(api_key_override=api_key)

    with _ollama_lock:
        if _ollama_instance is None:
            _ollama_instance = OllamaClient()
        if not _llm_provider_logged:
            try:
                from app.utils.log_manager import add_log
                add_log("info", "LLM: Ollama (Mistral + Qwen – modelos gratuitos)", "llm_provider")
                _llm_provider_logged = True
            except Exception:
                pass
    return _ollama_instance


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Classe Principal❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
class OpenAIClient:
    """
    Cliente OpenAI integrado ao LangChain para geração de texto e embeddings.
    Usa variáveis de ambiente (carregadas em main.py); chave nunca é exposta.
    Singleton via get_openai_client(); retry com backoff para 429/5xx/timeout.
    """

    def __init__(self, api_key_override: Optional[str] = None):
        cfg = _get_openai_config(api_key_override=api_key_override)
        temperature = 1 if cfg["model"].startswith("o") else cfg["temperature"]
        timeout = cfg.get("timeout", 360)
        self.llm = ChatOpenAI(
            model=cfg["model"],
            temperature=temperature,
            max_tokens=4096,
            api_key=cfg["api_key"],
            request_timeout=timeout,
        )
        # Modelo barato para tarefas leves (classificação, refino, análise) — economia de custo.
        self._model_fast = cfg.get("model_fast", "gpt-4o-mini")
        self._cfg = cfg
        self.embeddings = OpenAIEmbeddings(model=cfg["embedding_model"])
        # Cache: instância única de llm_fast (evita criar ChatOpenAI a cada request)
        self._llm_fast_instance = ChatOpenAI(
            model=self._model_fast,
            temperature=0.7,
            max_tokens=4096,
            api_key=self._cfg["api_key"],
            request_timeout=self._cfg.get("timeout", 360),
        )

    @property
    def llm_fast(self):
        """LLM com OPENAI_MODEL_FAST para uso em refino, classificação e análises leves."""
        return self._llm_fast_instance

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
    #━━━━━━━━━❮Geração de Texto (com retry)❯━━━━━━━━━
    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        timeout_override: int | None = None,
        temperature_override: float | None = None,
        use_fast_model: bool = False,
        num_predict: int | None = None,
    ) -> str:
        """
        Gera texto com o LLM usando invoke().
        Retry com backoff para 429, 5xx e timeout; nunca expõe stack/chave em log.
        temperature_override: se definido (ex.: 0 para classificação), usa esse valor na chamada.
        use_fast_model: se True, usa OPENAI_MODEL_FAST (ex.: gpt-4o-mini) para economia de custo.
        num_predict: ignorado (Ollama usa); mantido para compatibilidade.
        """
        return self._generate_text_with_retry(
            prompt=prompt,
            system_prompt=system_prompt,
            timeout_override=timeout_override,
            temperature_override=temperature_override,
            use_fast_model=use_fast_model,
        )

    def _generate_text_with_retry(
        self,
        prompt: str,
        system_prompt: str | None = None,
        timeout_override: int | None = None,
        temperature_override: float | None = None,
        use_fast_model: bool = False,
    ) -> str:
        from openai import APIError, APITimeoutError, RateLimitError

        cfg = self._cfg
        model = cfg["model_fast"] if use_fast_model else cfg["model"]
        timeout = timeout_override or cfg.get("timeout", 360)
        if use_fast_model and temperature_override is None:
            llm = self._llm_fast_instance
        elif temperature_override is not None:
            model_name = model.lower()
            temp = 1 if model_name.startswith("o") else temperature_override
            llm = ChatOpenAI(model=model, temperature=temp, max_tokens=4096, api_key=cfg["api_key"], request_timeout=timeout)
        else:
            llm = self.llm

        def _invoke():
            if system_prompt:
                response = llm.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ])
            else:
                response = llm.invoke(prompt)
            return response.content.strip() if hasattr(response, "content") else str(response)

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((RateLimitError, APIError, APITimeoutError, TimeoutError)),
            reraise=True,
        )
        def _do_invoke():
            return _invoke()

        import time as _time_mod

        _t_gen = _time_mod.perf_counter()
        _plen = len(prompt or "")
        _slen = len(system_prompt or "")
        try:
            from app.utils.log_manager import add_log
            add_log(
                "info",
                f"[openai] generate_text início | model={model} | use_fast_model={use_fast_model} | "
                f"prompt_chars={_plen} | system_chars={_slen} | timeout={timeout}",
                "openai",
            )
        except Exception:
            pass
        try:
            out = _do_invoke()
            try:
                from app.utils.log_manager import add_log
                add_log(
                    "info",
                    f"[openai] generate_text OK em {_time_mod.perf_counter()-_t_gen:.2f}s | model={model} | "
                    f"out_chars={len(out or '')}",
                    "openai",
                )
            except Exception:
                pass
            return out
        except Exception as e:
            try:
                from app.utils.log_manager import add_log
                add_log(
                    "error",
                    f"[openai] generate_text falhou após {_time_mod.perf_counter()-_t_gen:.2f}s | model={model} | "
                    f"{type(e).__name__}: {str(e)[:200]}",
                    "openai",
                )
            except Exception:
                pass
            return "Erro ao gerar texto com OpenAI."
