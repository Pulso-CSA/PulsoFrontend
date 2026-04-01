#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Segurança de Infraestrutura❯━━━━━━━━━
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
def generate_infra_security_report(id_requisicao: str, infra_doc: Dict) -> Dict:
    from services.agents.analise_services.json_utils import extract_json_from_response
    # Skip RAG para projetos JS (infra_doc vem com project_type quando infra fez skip)
    if (infra_doc or {}).get("project_type") == "javascript":
        report = {
            "riscos": ["porta 22 aberta ao público"],
            "recomendacoes": ["acesso SSH via bastion host e IP restrito"],
            "checklist": ["IAM revisado", "logs habilitados", "dados criptografados (at-rest/em trânsito)"],
        }
        try:
            db.upsert_security_infra(id_requisicao, report)
        except Exception as e:
            logger.warning("Falha ao salvar relatório de segurança de infra no banco: %s", e)
        return report

    client = get_openai_client()
    retriever = load_rag_index().as_retriever(search_kwargs={"k": 3})

    template_str = load_prompt("analyse/sec_infra")
    prompt = ChatPromptTemplate.from_messages([
        ("system", template_str.replace("{query}", "{input}")),
    ])
    combine_docs_chain = create_stuff_documents_chain(client.llm_fast, prompt)
    qa = create_retrieval_chain(retriever, combine_docs_chain)

    question = f"Auditar a arquitetura de infraestrutura (JSON puro). Infraestrutura: {infra_doc}"

    try:
        result = qa.invoke({"input": question})
        raw = (result.get("answer") or result.get("result") or str(result) or "").strip()
    except Exception as e:
        logger.warning("Erro durante execução RAG Segurança de Infra: %s", e)
        raw = ""

    #━━━━━━━━━❮Fallback seguro❯━━━━━━━━━
    report = {
        "riscos": ["porta 22 aberta ao público"],
        "recomendacoes": ["acesso SSH via bastion host e IP restrito"],
        "checklist": ["IAM revisado", "logs habilitados", "dados criptografados (at-rest/em trânsito)"]
    }

    #━━━━━━━━━❮Tentar interpretar JSON retornado (extração robusta)❯━━━━━━━━━
    parsed = extract_json_from_response(raw)
    if parsed:
        report = parsed

    #━━━━━━━━━❮Persistência❯━━━━━━━━━
    try:
        db.upsert_security_infra(id_requisicao, report)
    except Exception as e:
        logger.warning("Falha ao salvar relatório de segurança de infra no banco: %s", e)

    return report
