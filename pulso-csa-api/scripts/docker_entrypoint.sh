#!/bin/sh
# Inicia Ollama local (pull Mistral + Qwen), depois a API.
# Ativo só com USE_OLLAMA=1 e OLLAMA_HOST apontando para localhost/127.0.0.1.
# Render: disco efémero — sem volume persistente, cada deploy volta a baixar os modelos
# (vários GB). Monte um disco em /home/appuser/.ollama para reutilizar blobs.
# RAM: reserve instância com memória suficiente (ex.: 8 GB+ para os dois modelos Q4).

set -e

OLLAMA_PID=""
_cleanup() {
  if [ -n "$OLLAMA_PID" ]; then
    kill "$OLLAMA_PID" 2>/dev/null || true
    wait "$OLLAMA_PID" 2>/dev/null || true
  fi
}
trap _cleanup EXIT INT TERM

_use_ollama=""
case "${USE_OLLAMA:-}" in
  1|true|TRUE|yes|YES) _use_ollama=1 ;;
esac

_skip_serve=""
case "${OLLAMA_SKIP_SERVE:-}" in
  1|true|TRUE|yes|YES) _skip_serve=1 ;;
esac

_is_local_host() {
  _h="${OLLAMA_HOST:-http://127.0.0.1:11434}"
  case "$_h" in
    *127.0.0.1*|*localhost*) return 0 ;;
    *) return 1 ;;
  esac
}

if [ "$_use_ollama" = "1" ] && [ -z "$_skip_serve" ] && _is_local_host; then
  if ! command -v ollama >/dev/null 2>&1; then
    echo "docker_entrypoint: binário 'ollama' não encontrado (imagem incompleta?)"
    exit 1
  fi

  # Servidor: host:porta (sem esquema)
  export OLLAMA_HOST="${OLLAMA_SERVE_BIND:-127.0.0.1:11434}"
  echo "docker_entrypoint: ollama serve (${OLLAMA_HOST})..."
  ollama serve >/tmp/ollama-serve.log 2>&1 &
  OLLAMA_PID=$!

  echo "docker_entrypoint: à espera da API Ollama..."
  _i=0
  while ! curl -sf "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; do
    _i=$((_i + 1))
    if [ "$_i" -gt 300 ]; then
      echo "docker_entrypoint: timeout a aguardar Ollama (300s). Log:"
      cat /tmp/ollama-serve.log 2>/dev/null || true
      exit 1
    fi
    sleep 1
  done

  # Cliente (CLI + app Python): URL completa
  export OLLAMA_HOST="http://127.0.0.1:11434"

  _skip_pull=""
  case "${OLLAMA_SKIP_PULL:-}" in
    1|true|TRUE|yes|YES) _skip_pull=1 ;;
  esac

  if [ -z "$_skip_pull" ]; then
    M1="${OLLAMA_MODEL_INTERPRETACAO:-mistral:7b-instruct-q4_K_M}"
    M2="${OLLAMA_MODEL_EXECUCAO:-qwen2.5-coder:3b-base-q4_K_M}"
    echo "docker_entrypoint: ollama pull ${M1}"
    ollama pull "$M1"
    echo "docker_entrypoint: ollama pull ${M2}"
    ollama pull "$M2"
  else
    echo "docker_entrypoint: OLLAMA_SKIP_PULL=1 — a assumir modelos já presentes em ~/.ollama"
  fi
fi

# Railway (e outros PaaS) injetam PORT; o proxy encaminha para essa porta, não necessariamente 8000.
_APP_PORT="${PORT:-8000}"
echo "docker_entrypoint: uvicorn app.main:app --host 0.0.0.0 --port ${_APP_PORT}"
exec env PYTHONPATH=/app/api uvicorn app.main:app --host 0.0.0.0 --port "${_APP_PORT}"
