#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Infraestrutura❯━━━━━━━━━
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
from services.agents.analise_services.json_utils import extract_json_from_response


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Helpers❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _is_js_structure(estrutura_arquivos: Dict) -> bool:
    """Detecta se a estrutura é de projeto JS/TS/React."""
    if not estrutura_arquivos:
        return False
    js_ext = (".tsx", ".jsx", ".ts", ".js", ".vue")
    for folder, files in (estrutura_arquivos or {}).items():
        for f in (files or []) if isinstance(files, list) else []:
            if isinstance(f, str) and any(f.lower().endswith(ext) for ext in js_ext):
                return True
            if f == "package.json" or "src" in str(folder):
                return True
    return False


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função Principal do Serviço❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def generate_infra_doc(id_requisicao: str, estrutura_arquivos: Dict, backend_doc: Dict) -> Dict:
    # Skip RAG para projetos JS – fallback adequado, evita lentidão/erros
    if _is_js_structure(estrutura_arquivos or {}) or backend_doc.get("project_type") == "javascript":
        infra_doc = {
            "recursos_infraestrutura": ["EC2 t3.medium", "RDS PostgreSQL", "S3 Bucket Logs"],
            "provedores": ["AWS"],
            "pipeline_deploy": ["GitHub Actions", "Terraform", "Docker Compose"],
            "configuracoes_de_rede": ["VPC privada", "segurança via Security Groups"],
            "project_type": "javascript",
        }
        try:
            db.upsert_infra_doc(id_requisicao, infra_doc)
        except Exception as e:
            logger.warning("Falha ao salvar documento de infraestrutura no banco: %s", e)
        return infra_doc

    client = get_openai_client()
    retriever = load_rag_index().as_retriever(search_kwargs={"k": 3})

    template_str = load_prompt("analyse/infra")
    prompt = ChatPromptTemplate.from_messages([
        ("system", template_str.replace("{query}", "{input}")),
    ])
    combine_docs_chain = create_stuff_documents_chain(client.llm_fast, prompt)
    qa_chain = create_retrieval_chain(retriever, combine_docs_chain)

    question = f"Gerar infraestrutura ideal (JSON puro) para a estrutura {estrutura_arquivos} e backend {backend_doc}"

    try:
        result = qa_chain.invoke({"input": question})
        raw = result.get("answer") or result.get("result") or str(result)
        raw = (raw or "").strip()
    except Exception as e:
        logger.warning("Erro durante execução RAG Infraestrutura: %s", e)
        raw = ""

    #━━━━━━━━━❮Fallback seguro❯━━━━━━━━━
    infra_doc = {
        "recursos_infraestrutura": ["EC2 t3.medium", "RDS PostgreSQL", "S3 Bucket Logs"],
        "provedores": ["AWS"],
        "pipeline_deploy": ["GitHub Actions", "Terraform", "Docker Compose"],
        "configuracoes_de_rede": ["VPC privada", "segurança via Security Groups"]
    }

    #━━━━━━━━━❮Tentar interpretar JSON retornado (extração robusta)❯━━━━━━━━━
    parsed = extract_json_from_response(raw)
    if parsed:
        infra_doc = parsed

    #━━━━━━━━━❮Persistência❯━━━━━━━━━
    try:
        db.upsert_infra_doc(id_requisicao, infra_doc)
    except Exception as e:
        logger.warning("Falha ao salvar documento de infraestrutura no banco: %s", e)

    return infra_doc
