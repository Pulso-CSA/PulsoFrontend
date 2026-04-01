#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import os
import threading
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader, DirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Constantes❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datasets"
PDF_DIR = DATA_DIR / "pdf"
CSV_DIR = DATA_DIR / "csv"
VECTOR_DB_PATH = BASE_DIR / "storage" / "vectorstore" / "faiss_governance"


def _get_rag_embeddings():
    """Retorna embeddings para RAG. Usa FakeEmbeddings quando USE_OLLAMA=1 e sem chave OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    use_ollama = os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes")
    if api_key and not use_ollama:
        model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        return OpenAIEmbeddings(model=model)
    from langchain_community.embeddings.fake import FakeEmbeddings
    return FakeEmbeddings(size=1536)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Treinamento/Carregamento RAG❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def train_rag_index():
    """
    Lê os arquivos PDF/CSV em datasets e cria um índice vetorial (FAISS)
    para busca semântica de boas práticas de governança.
    """
    docs = []

    # PDF Loader (COBIT, ISO, ITIL, LGPD) — rglob inclui subpastas (datasets/pdf/...)
    if PDF_DIR.exists():
        for pdf_path in sorted(PDF_DIR.rglob("*.pdf")):
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs.extend(loader.load())
            except Exception as e:
                print(f"⚠️ Falha ao carregar {pdf_path.name}: {e}")
                try:
                    docs.extend(TextLoader(str(pdf_path), encoding="utf-8").load())
                    print(f"↪️ {pdf_path.name} carregado como texto simples.")
                except Exception as e2:
                    print(f"❌ Erro ao tentar fallback para {pdf_path.name}: {e2}")

    # CSV Loader (métricas, riscos, alinhamento)
    if CSV_DIR.exists():
        for csv_path in CSV_DIR.glob("*.csv"):
            try:
                docs.extend(CSVLoader(file_path=str(csv_path)).load())
            except Exception as e:
                print(f"⚠️ Falha ao carregar {csv_path.name}: {e}")
                docs.extend(TextLoader(str(csv_path), encoding="utf-8").load())

    # Divide em chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    all_texts = splitter.split_documents(docs)

    # ✅ Verificação preventiva — evita 'list index out of range'
    if not all_texts:
        print("⚠️ Nenhum documento válido encontrado para treinar o índice RAG.")
        # cria índice vazio, para não quebrar o fluxo
        embeddings = _get_rag_embeddings()
        db = FAISS.from_texts(["Nenhum dado disponível."], embeddings)
        db.save_local(str(VECTOR_DB_PATH))
        print(f"⚠️ Índice RAG vazio criado em {VECTOR_DB_PATH}")
        return db

    # Gera embeddings e salva índice
    embeddings = _get_rag_embeddings()
    db = FAISS.from_documents(all_texts, embeddings)
    db.save_local(str(VECTOR_DB_PATH))
    print(f"✅ Índice RAG treinado e salvo em {VECTOR_DB_PATH}")
    return db


_rag_index_cache = None
_rag_lock = threading.Lock()


def load_rag_index():
    """
    Carrega o índice RAG local (FAISS) — singleton em memória (uma vez por processo).
    Se não existir no disco, cria automaticamente.
    """
    global _rag_index_cache
    if _rag_index_cache is not None:
        return _rag_index_cache
    with _rag_lock:
        if _rag_index_cache is not None:
            return _rag_index_cache
        embeddings = _get_rag_embeddings()
        if not VECTOR_DB_PATH.exists():
            print("⚠️ Índice RAG não encontrado, criando automaticamente...")
            _rag_index_cache = train_rag_index()
            return _rag_index_cache
        try:
            _rag_index_cache = FAISS.load_local(str(VECTOR_DB_PATH), embeddings, allow_dangerous_deserialization=True)
            return _rag_index_cache
        except Exception as e:
            print(f"⚠️ Falha ao carregar índice FAISS existente ({e}). Recriando...")
            _rag_index_cache = train_rag_index()
            return _rag_index_cache
