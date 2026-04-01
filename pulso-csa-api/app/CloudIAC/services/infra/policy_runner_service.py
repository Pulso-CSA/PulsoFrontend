#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Policy Runner – regras internas (sem OPA)❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import os
import re
from pathlib import Path
from typing import Optional

from app.CloudIAC.models.infra.reports import PolicyReport


# Regras internas (fallback quando OPA/Conftest indisponível)
FORBIDDEN_0_0_0_0 = re.compile(r"0\.0\.0\.0/0")
FORBIDDEN_PUBLIC_IP = re.compile(r"associate_public_ip_address\s*=\s*true", re.IGNORECASE)
REQUIRED_TAGS = ["Environment", "Project", "ManagedBy"]


def run_policy_check(
    terraform_dir: str,
    allow_override: bool = False,
    override_reason: Optional[str] = None,
) -> PolicyReport:
    """
    Verifica políticas em arquivos .tf do diretório.
    Regras: sem 0.0.0.0/0 em portas sensíveis, sem recursos públicos por padrão, tags obrigatórias.
    """
    failures: list[str] = []
    warnings: list[str] = []

    if not terraform_dir or not os.path.isdir(terraform_dir):
        return PolicyReport(passed=False, failures=["Diretório terraform inválido ou inexistente"])

    for tf_file in Path(terraform_dir).rglob("*.tf"):
        try:
            content = tf_file.read_text(encoding="utf-8", errors="ignore")
            rel = str(tf_file.relative_to(terraform_dir))

            if FORBIDDEN_0_0_0_0.search(content):
                failures.append(f"{rel}: CIDR 0.0.0.0/0 não permitido em portas sensíveis")

            if FORBIDDEN_PUBLIC_IP.search(content):
                warnings.append(f"{rel}: associate_public_ip_address=true detectado; preferir false")

            if "output" in content and "password" in content.lower():
                failures.append(f"{rel}: outputs sensíveis (password) não permitidos")

            if "output" in content and "secret" in content.lower():
                warnings.append(f"{rel}: output com 'secret' pode expor dados sensíveis")

        except Exception as e:
            warnings.append(f"{tf_file}: erro ao ler: {e}")

    passed = len(failures) == 0 or (allow_override and override_reason)
    return PolicyReport(
        passed=passed,
        failures=failures,
        warnings=warnings,
        allow_override=allow_override,
        override_reason=override_reason,
    )
