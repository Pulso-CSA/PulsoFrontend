from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

ALLOWED_SCOPES = [
    "PulsoCSA/Python",
    "PulsoCSA/JavaScript",
    "InteligenciaDados",
    "FinOps",
    "CloudIAC",
]

SCOPE_DIRECTORY_MAP: Dict[str, str] = {
    "PulsoCSA/Python": "api/app/PulsoCSA/Python",
    "PulsoCSA/JavaScript": "api/app/PulsoCSA/JavaScript",
    "InteligenciaDados": "api/app/InteligenciaDados",
    "FinOps": "api/app/FinOps",
    "CloudIAC": "api/app/CloudIAC",
}


class RegenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(..., description="Objetivo do ciclo regenerativo.")
    usuario: str = Field(default="regenai", description="Usuario da execucao.")
    scopes: List[str] = Field(
        ...,
        min_length=1,
        description="Escopos alvo da execucao regenerativa.",
        examples=[["PulsoCSA/Python"], ["PulsoCSA/Python", "CloudIAC"]],
    )
    root_path: Optional[str] = Field(
        default=None,
        description="Compatibilidade: caminho raiz legado. Ignorado quando scopes sao informados.",
    )
    max_rounds: int = Field(
        default=5,
        ge=1,
        le=5,
        description="Numero maximo de rodadas regenerativas.",
    )
    max_concurrency: int = Field(
        default=6,
        ge=1,
        le=6,
        description="Numero maximo de operacoes simultaneas.",
    )
    route_limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Limite de rotas analisadas por execucao.",
    )
    include_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST"],
        description="Metodos HTTP que entram no ciclo de teste.",
    )
    include_keywords: List[str] = Field(
        default_factory=list,
        description="Palavras-chave extras para priorizar rotas.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_scope_aliases(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        payload = dict(data)
        if "scopes" not in payload:
            alias_value = payload.get("scope")
            if alias_value is not None:
                payload["scopes"] = alias_value if isinstance(alias_value, list) else [alias_value]
            elif "target_modules" in payload:
                target = payload.get("target_modules")
                payload["scopes"] = target if isinstance(target, list) else [target]
        payload.pop("scope", None)
        payload.pop("target_modules", None)
        return payload

    @model_validator(mode="after")
    def validate_scopes(self) -> "RegenRequest":
        normalized = []
        for scope in self.scopes:
            if scope not in ALLOWED_SCOPES:
                allowed = ", ".join(ALLOWED_SCOPES)
                raise ValueError(f"Escopo invalido '{scope}'. Escopos permitidos: {allowed}")
            if scope not in normalized:
                normalized.append(scope)
        self.scopes = normalized
        return self

