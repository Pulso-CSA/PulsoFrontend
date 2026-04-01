#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Segurança de Código❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import logging
from typing import Dict

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
def _is_js_backend(backend_doc: Dict) -> bool:
    """Detecta se o backend é de projeto JS (project_type ou arquivos .tsx/.jsx)."""
    if backend_doc.get("project_type") == "javascript":
        return True
    arquivos = backend_doc.get("arquivos") or {}
    js_ext = (".tsx", ".jsx", ".ts", ".js", ".vue")
    for key in arquivos if isinstance(arquivos, dict) else []:
        if isinstance(key, str) and any(key.lower().endswith(ext) for ext in js_ext):
            return True
    return False


def generate_code_security_report(id_requisicao: str, backend_doc: Dict) -> Dict:
    from services.agents.analise_services.json_utils import extract_json_from_response
    # Skip RAG para projetos JS
    if _is_js_backend(backend_doc or {}):
        report = {
            "vulnerabilidades_potenciais": [],
            "recomendacoes": ["validação de entrada", "sanitização de dados", "variáveis de ambiente para segredos"],
            "checklist": ["linters", "dependências auditadas"],
        }
        try:
            db.upsert_security_code(id_requisicao, report)
        except Exception as e:
            logger.warning("Falha ao salvar relatório de segurança no banco: %s", e)
        return report

    client = get_openai_client()
    retriever = load_rag_index().as_retriever(search_kwargs={"k": 3})

    template_str = load_prompt("analyse/sec_code")
    prompt = ChatPromptTemplate.from_messages([
        ("system", template_str.replace("{query}", "{input}")),
    ])
    combine_docs_chain = create_stuff_documents_chain(client.llm_fast, prompt)
    qa_chain = create_retrieval_chain(retriever, combine_docs_chain)

    question = f"Auditar segurança do backend planejado (JSON puro). Backend: {backend_doc}"

    try:
        result = qa_chain.invoke({"input": question})
        raw = result.get("answer") or result.get("result") or str(result)
        raw = (raw or "").strip()
    except Exception as e:
        logger.warning("Erro durante execução RAG Segurança de Código: %s", e)
        raw = ""

    report = {
        "vulnerabilidades_potenciais": [],
        "recomendacoes": ["validação de entrada", "sanitização de dados", "os.getenv para segredos"],
        "checklist": ["linters", "dependências auditadas"]
    }

    #━━━━━━━━━❮Tentar interpretar JSON retornado (extração robusta)❯━━━━━━━━━
    parsed = extract_json_from_response(raw)
    if parsed:
        report = parsed

    #━━━━━━━━━❮Persistência❯━━━━━━━━━
    try:
        db.upsert_security_code(id_requisicao, report)
    except Exception as e:
        logger.warning("Falha ao salvar relatório de segurança no banco: %s", e)

    return report
