#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
from app.core.openai.rag_trainer import train_rag_index, load_rag_index

#━━━━━━━━━❮Vector Store❯━━━━━━━━━
def initialize_vectorstore():
    try:
        db = load_rag_index()
        print("✅ Vector store carregado com sucesso.")
    except Exception:
        print("⚠️ Nenhum índice encontrado, criando novo...")
        db = train_rag_index()
        print("✅ Novo índice criado.")
    return db
