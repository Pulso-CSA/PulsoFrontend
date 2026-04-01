#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Terraform Stack Generator – glue code❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from app.CloudIAC.models.infra.core import InfraSpec

# Path para módulos golden (dentro do repo PulsoAPI)
def _get_repo_terraform_modules() -> Path:
    """Retorna path terraform/modules do repo (quando disponível)."""
    p = Path(__file__).resolve()
    for _ in range(6):
        p = p.parent
        mod = p / "terraform" / "modules"
        if mod.exists():
            return mod
    return Path()


def get_terraform_base_path(root_path: str) -> str:
    """Retorna path base para terraform (terraform/ dentro do root_path)."""
    return str(Path(root_path).resolve() / "terraform")


def compute_terraform_tree_hash(terraform_dir: str) -> str:
    """Hash da árvore de arquivos .tf para invalidar token."""
    if not os.path.isdir(terraform_dir):
        return ""
    parts: list[str] = []
    for dirpath, _, filenames in os.walk(terraform_dir):
        for f in sorted(filenames):
            if f.endswith(".tf"):
                fp = os.path.join(dirpath, f)
                try:
                    stat = os.stat(fp)
                    rel = os.path.relpath(fp, terraform_dir)
                    parts.append(f"{rel}:{stat.st_mtime}:{stat.st_size}")
                except OSError:
                    pass
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def ensure_terraform_structure(root_path: str, spec: InfraSpec) -> dict[str, Any]:
    """
    Garante estrutura terraform/ com stacks por env/provider.
    Cria main.tf de wiring (chama golden modules) se não existir.
    Copia módulos golden do repo para root_path/terraform/modules quando necessário.
    """
    base = Path(root_path).resolve() / "terraform"
    base.mkdir(parents=True, exist_ok=True)
    modules_dst = base / "modules"
    repo_modules = _get_repo_terraform_modules()
    if repo_modules.exists() and not modules_dst.exists():
        try:
            shutil.copytree(repo_modules, modules_dst)
        except Exception:
            modules_dst.mkdir(parents=True, exist_ok=True)

    providers = [p.provider if hasattr(p, "provider") else p for p in spec.providers]
    if not providers:
        providers = ["aws"]
    envs = spec.envs or ["dev"]

    created: list[str] = []
    for env in envs:
        for prov in providers:
            stack_dir = base / "stacks" / env / prov
            stack_dir.mkdir(parents=True, exist_ok=True)
            main_tf = stack_dir / "main.tf"
            if not main_tf.exists():
                _write_main_tf(main_tf, prov, env, spec)
                created.append(str(main_tf.relative_to(base)))

    return {
        "terraform_base": str(base),
        "created": created,
        "providers": providers,
        "envs": envs,
    }


def _write_main_tf(path: Path, provider: str, env: str, spec: InfraSpec) -> None:
    """Escreve main.tf de wiring (chama golden modules)."""
    modules = spec.golden_modules or []
    blocks: list[str] = []
    for m in modules:
        if m.provider != provider:
            continue
        name = m.module_name.replace("-", "_")
        rel = m.module_path.replace("terraform/", "").replace("terraform\\", "").lstrip("/")
        source = f"../../../{rel}" if rel else f"../../../modules/{provider}/{m.module_name}"
        blocks.append(f'''
module "{name}" {{
  source = "{source}"
  env    = "{env}"
  tags = {{
    Environment = "{env}"
    Project     = "pulso"
    ManagedBy   = "PulsoAPI"
  }}
}}
''')
    if not blocks:
        blocks = [f'''
# Placeholder para {provider} - adicione módulos golden
resource "null_resource" "placeholder" {{
  triggers = {{
    env = "{env}"
  }}
}}
''']
    if provider == "aws":
        content = f'''# Terraform stack: {provider} / {env}
terraform {{
  required_providers {{
    aws = {{ source = "hashicorp/aws", version = "~> 5.0" }}
  }}
  backend "local" {{
    path = "terraform.tfstate"
  }}
}}

provider "aws" {{
  region = "us-east-1"
}}

{"".join(blocks)}
'''
    elif provider == "azure":
        content = f'''# Terraform stack: {provider} / {env}
terraform {{
  required_providers {{
    azurerm = {{ source = "hashicorp/azurerm", version = "~> 3.0" }}
  }}
  backend "local" {{
    path = "terraform.tfstate"
  }}
}}

provider "azurerm" {{
  features {{}}
}}

{"".join(blocks)}
'''
    elif provider == "gcp":
        content = f'''# Terraform stack: {provider} / {env}
terraform {{
  required_providers {{
    google = {{ source = "hashicorp/google", version = "~> 5.0" }}
  }}
  backend "local" {{
    path = "terraform.tfstate"
  }}
}}

provider "google" {{
  project = "my-project"
  region  = "us-central1"
}}

{"".join(blocks)}
'''
    path.write_text(content, encoding="utf-8")
