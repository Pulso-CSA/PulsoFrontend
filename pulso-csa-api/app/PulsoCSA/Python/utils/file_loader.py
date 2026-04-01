#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
import os
from langchain.document_loaders import PyPDFLoader, CSVLoader

#━━━━━━━━━❮Função de Carregamento❯━━━━━━━━━
def load_all_files(dataset_path: str):
    """
    Carrega todos os PDFs e CSVs de uma pasta e retorna como lista de documentos LangChain.
    """
    documents = []
    pdf_path = os.path.join(dataset_path, "pdf")
    csv_path = os.path.join(dataset_path, "csv")

    # PDFs
    for file in os.listdir(pdf_path):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_path, file))
            documents.extend(loader.load())

    # CSVs
    for file in os.listdir(csv_path):
        if file.endswith(".csv"):
            loader = CSVLoader(file_path=os.path.join(csv_path, file))
            documents.extend(loader.load())

    return documents
