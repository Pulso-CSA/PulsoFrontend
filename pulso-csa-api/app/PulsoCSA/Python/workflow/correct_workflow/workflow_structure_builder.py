#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Builder – Estrutura Dinâmica a partir do Plano❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Dict, List
from storage.database.creation_analyse import database_c2 as db_c2


def build_structure_from_plan(
    id_requisicao: str,
    novos_arquivos: List,
    arquivos_a_alterar: List
) -> Dict[str, List[str]]:
    """
    Converte a saída do LLM para um mapa real de estrutura:

    {
        "src/services": ["test_service.py"],
        "src/ui": ["test_page.py"],
        ...
    }

    Sem estrutura fixa, sem acoplamento.
    """

    estrutura: Dict[str, List[str]] = {}

    # --- incluir arquivos novos ---
    for item in novos_arquivos:
        fullpath = item.path.replace("\\", "/")
        parts = fullpath.split("/")
        folder = "/".join(parts[:-1]).strip()
        file = parts[-1]

        if folder not in estrutura:
            estrutura[folder] = []

        estrutura[folder].append(file)

    # --- incluir arquivos a alterar ---
    for item in arquivos_a_alterar:
        fullpath = item.path.replace("\\", "/")
        parts = fullpath.split("/")
        folder = "/".join(parts[:-1]).strip()
        file = parts[-1]

        if folder not in estrutura:
            estrutura[folder] = []

        if file not in estrutura[folder]:
            estrutura[folder].append(file)

    # salvar snapshot
    try:
        db_c2.upsert_blueprint(id_requisicao, estrutura)
    except Exception as e:
        print(f"⚠️ Erro ao salvar blueprint: {e}")

    return estrutura
