#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Backend Analysis❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.rag_trainer import load_rag_index
except ImportError:
    from app.core.openai.rag_trainer import load_rag_index
from app.prompts.loader import load_prompt
# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client
from storage.database.creation_analyse import database_c2 as db


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função Principal do Serviço❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _extract_funcionalidades_from_prompt(refined_prompt: str) -> List[str]:
    """Extrai funcionalidades específicas do pedido do usuário."""
    if not refined_prompt or not refined_prompt.strip():
        return []
    text = refined_prompt.lower()
    funcs = []
    if "login" in text or "criação de conta" in text or "create_account" in text or "cadastro" in text:
        funcs.extend(["POST /login", "POST /create_account"])
    if "bhaskara" in text:
        funcs.append("POST /bhaskara - cálculo de equação do 2º grau")
    if "pitágoras" in text or "pitagoras" in text:
        funcs.append("POST /pitagoras - cálculo da hipotenusa")
    if "4 operações" in text or "operações básicas" in text or "operacoes basicas" in text:
        funcs.append("GET/POST operações básicas (+, -, *, /)")
    if "rota /" in text or "rota raiz" in text or '"teste pulso"' in text:
        funcs.append('GET / retorna {"Teste Pulso 1.0": "OK"}')
    return funcs if funcs else []


def _is_js_structure(estrutura_arquivos: Dict[str, List[str]]) -> bool:
    """Detecta se a estrutura é de projeto JS/TS/React (não Python)."""
    if not estrutura_arquivos:
        return False
    js_ext = (".tsx", ".jsx", ".ts", ".js", ".vue")
    for folder, files in estrutura_arquivos.items():
        for f in (files or []) if isinstance(files, list) else []:
            if isinstance(f, str) and any(f.lower().endswith(ext) for ext in js_ext):
                return True
            if f == "package.json" or "src" in str(folder):
                return True
    return False


def _fallback_from_structure(
    estrutura_arquivos: Dict[str, List[str]], refined_prompt: str = ""
) -> Dict:
    """Fallback enriquecido: estrutura + funcionalidades extraídas do prompt. Suporta Python e JS/React."""
    is_js = _is_js_structure(estrutura_arquivos or {})
    arquivos = {}
    for folder, files in (estrutura_arquivos or {}).items():
        for f in files if isinstance(files, list) else []:
            if isinstance(f, str) and f and not f.startswith(".") and f != "__init__.py":
                key = f"{folder}/{f}".strip("/") if folder and folder != "." else f
                if is_js:
                    if "app" in f.lower() and (".tsx" in f or ".jsx" in f):
                        arquivos[key] = ["componente principal do app React"]
                    elif "login" in f.lower() or "auth" in f.lower():
                        if "form" in f.lower() or "page" in f.lower():
                            arquivos[key] = ["formulário ou página de login"]
                        elif "context" in f.lower():
                            arquivos[key] = ["contexto de autenticação React"]
                        elif "service" in f.lower() or "api" in f.lower():
                            arquivos[key] = ["serviço de autenticação, chamadas API"]
                        elif "hook" in f.lower():
                            arquivos[key] = ["hook useAuth para estado de login"]
                        else:
                            arquivos[key] = ["componente de autenticação"]
                    elif "api" in f.lower() or "service" in f.lower():
                        arquivos[key] = ["chamadas API, lógica de negócio"]
                    elif "package.json" in f:
                        arquivos[key] = ["dependências e scripts do projeto"]
                    elif "vite" in f.lower() or "tsconfig" in f.lower():
                        arquivos[key] = ["configuração do build/TypeScript"]
                    else:
                        arquivos[key] = ["conteúdo conforme tipo de projeto"]
                else:
                    if "model" in f.lower() or "schema" in f.lower():
                        arquivos[key] = ["modelos Pydantic/SQLAlchemy para validação"]
                    elif "auth" in f.lower() and "router" in f.lower():
                        arquivos[key] = ["rotas login e create_account"]
                    elif "auth" in f.lower() and "service" in f.lower():
                        arquivos[key] = ["lógica de autenticação, validação de credenciais"]
                    elif "calculator" in f.lower() and "router" in f.lower():
                        arquivos[key] = ["rotas bhaskara, pitagoras, operações básicas"]
                    elif "calculator" in f.lower() and "service" in f.lower():
                        arquivos[key] = ["funções bhaskara, pitagoras, soma, subtração, multiplicação, divisão"]
                    elif "setting" in f.lower() or "config" in f.lower():
                        arquivos[key] = ["configurações, os.getenv para segredos"]
                    elif "main" in f.lower():
                        arquivos[key] = ["ponto de entrada, registra routers, rota /"]
                    else:
                        arquivos[key] = ["conteúdo conforme tipo de projeto"]
    if not arquivos:
        arquivos = {"src/App.tsx": ["componente principal"]} if is_js else {"main.py": ["ponto de entrada do projeto"]}
    funcionalidades = _extract_funcionalidades_from_prompt(refined_prompt)
    if not funcionalidades:
        funcionalidades = ["implementar conforme pedido do usuário"]
    return {
        "arquivos": arquivos,
        "funcionalidades": funcionalidades,
        "conexoes": [],
        "otimizacoes": ["modularização", "tratamento de erros", "validação de entrada", "queries parametrizadas", "os.getenv para segredos"],
    }


def _extract_json_from_response(raw: str) -> dict | None:
    """Extrai JSON de resposta LLM (markdown, texto misto, vazio)."""
    import re
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    brace = text.find("{")
    if brace >= 0:
        depth, end = 0, -1
        for i in range(brace, len(text)):
            if text[i] == "{": depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0: end = i; break
        if end >= 0:
            text = text[brace : end + 1]
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        try:
            fixed = re.sub(r",\s*}", "}", text)
            fixed = re.sub(r",\s*]", "]", fixed)
            parsed = json.loads(fixed)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None


def generate_backend_doc(
    id_requisicao: str,
    estrutura_arquivos: Dict[str, List[str]],
    refined_prompt: str = "",
) -> Dict:
    # Skip RAG para projetos JS – fallback é adequado e evita lentidão/erros JSON
    if _is_js_structure(estrutura_arquivos or {}):
        backend_doc = _fallback_from_structure(estrutura_arquivos, refined_prompt)
        backend_doc["project_type"] = "javascript"
        try:
            db.upsert_backend_doc(id_requisicao, backend_doc)
        except Exception as e:
            logger.warning("Falha ao salvar backend_doc no banco: %s", e)
        return backend_doc

    client = get_openai_client()
    retriever = load_rag_index().as_retriever(search_kwargs={"k": 3})

    template_str = load_prompt("analyse/backend")
    prompt = ChatPromptTemplate.from_messages([
        ("system", template_str.replace("{query}", "{input}")),
    ])

    combine_docs_chain = create_stuff_documents_chain(client.llm_fast, prompt)
    qa_chain = create_retrieval_chain(retriever, combine_docs_chain)

    pedido = (refined_prompt or "").strip()[:500]
    question = (
        f"Gerar documento JSON de backend. Pedido do usuário: {pedido or '(não informado)'}. "
        f"Estrutura: {estrutura_arquivos}. "
        "Adapte ao tipo (API, CLI, Streamlit, Django, biblioteca, script). Não invente dados ausentes."
    )

    try:
        result = qa_chain.invoke({"input": question})
        raw = result.get("answer") or result.get("result") or str(result)
        raw = (raw or "").strip()
    except Exception as e:
        logger.warning("Erro durante execução RAG Backend: %s", e)
        raw = ""

    backend_doc = _fallback_from_structure(estrutura_arquivos, refined_prompt)

    #━━━━━━━━━❮Interpretação da Resposta (extração robusta)❯━━━━━━━━━
    parsed = _extract_json_from_response(raw)
    if parsed:
        backend_doc = parsed
        # Enriquecer funcionalidades se o LLM retornou genérico
        extracted = _extract_funcionalidades_from_prompt(refined_prompt)
        if extracted and (
            not backend_doc.get("funcionalidades")
            or backend_doc.get("funcionalidades") == ["implementar conforme pedido do usuário"]
        ):
            backend_doc["funcionalidades"] = extracted

    #━━━━━━━━━❮Salvar no MongoDB❯━━━━━━━━━
    try:
        db.upsert_backend_doc(id_requisicao, backend_doc)
    except Exception as e:
        logger.warning("Falha ao salvar backend_doc no banco: %s", e)

    #━━━━━━━━━❮Retorno Padronizado❯━━━━━━━━━
    return backend_doc
