#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviços de Criação JavaScript (equivalente ao pipeline Python)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from .structure_creator_service_js import create_structure_from_report_js
from .code_creator_from_reports_js import create_code_from_reports_js

__all__ = ["create_structure_from_report_js", "create_code_from_reports_js"]
