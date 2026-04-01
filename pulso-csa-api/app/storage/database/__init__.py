#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━
#━━━━━━━━━❮Pacote Database – Inicialização❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━

# database_core é compartilhado e permanece aqui
from . import database_core

# creation_analyse foi movido para PulsoCSA/Python/storage/database/creation_analyse
# Importar apenas database_core que é compartilhado
__all__ = ["database_core"]
