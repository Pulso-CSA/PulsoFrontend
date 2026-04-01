#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Finance Models❯━━━━━━━━━
# SFAP: planos (referência preços/lucro) e movimentos (receita/gasto)
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import Optional, List
from pydantic import BaseModel, Field


class PlanoCreate(BaseModel):
    tipo_plano: str = Field(..., min_length=1, max_length=50)
    preco_unit_usd: float = Field(..., ge=0)
    taxa_stripe_unit_usd: float = Field(0, ge=0)
    taxa_stripe_total_10k_usd: float = Field(0, ge=0)
    lucro_100_usd: float = Field(0)
    lucro_1000_usd: float = Field(0)
    lucro_10000_usd: float = Field(0)


class PlanoUpdate(BaseModel):
    tipo_plano: Optional[str] = Field(None, max_length=50)
    preco_unit_usd: Optional[float] = Field(None, ge=0)
    taxa_stripe_unit_usd: Optional[float] = Field(None, ge=0)
    taxa_stripe_total_10k_usd: Optional[float] = Field(None, ge=0)
    lucro_100_usd: Optional[float] = None
    lucro_1000_usd: Optional[float] = None
    lucro_10000_usd: Optional[float] = None


class PlanoResponse(BaseModel):
    id: str
    tipo_plano: str
    preco_unit_usd: float
    taxa_stripe_unit_usd: float
    taxa_stripe_total_10k_usd: float
    lucro_100_usd: float
    lucro_1000_usd: float
    lucro_10000_usd: float


class MovimentoCreate(BaseModel):
    data: str  # ISO date
    tipo: str = Field(..., pattern="^(ganho|gasto)$")
    categoria: str = Field("outros", max_length=50)
    descricao: str = Field("", max_length=500)
    valor_usd: float = Field(..., ge=0)
    moeda: str = Field("USD", max_length=10)
    notas: str = Field("", max_length=1000)
    recorrencia: str = Field("único", max_length=20)
    recorrencia_intervalo: Optional[int] = None
    recorrencia_unidade: Optional[str] = None
    plano_tipo: Optional[str] = None
    plano_preco: Optional[float] = None
    num_usuarios: Optional[int] = None


class MovimentoUpdate(BaseModel):
    data: Optional[str] = None
    tipo: Optional[str] = Field(None, pattern="^(ganho|gasto)$")
    categoria: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = Field(None, max_length=500)
    valor_usd: Optional[float] = Field(None, ge=0)
    moeda: Optional[str] = Field(None, max_length=10)
    notas: Optional[str] = Field(None, max_length=1000)
    recorrencia: Optional[str] = Field(None, max_length=20)
    recorrencia_intervalo: Optional[int] = None
    recorrencia_unidade: Optional[str] = None
    plano_tipo: Optional[str] = None
    plano_preco: Optional[float] = None
    num_usuarios: Optional[int] = None


class MovimentoResponse(BaseModel):
    id: str
    data: str
    tipo: str
    categoria: str
    descricao: str
    valor_usd: float
    moeda: str
    notas: Optional[str] = None
    recorrencia: Optional[str] = None
    recorrencia_intervalo: Optional[int] = None
    recorrencia_unidade: Optional[str] = None
    plano_tipo: Optional[str] = None
    plano_preco: Optional[float] = None
    num_usuarios: Optional[int] = None


class DashboardResponse(BaseModel):
    receita_total_usd: float
    custo_total_usd: float
    saldo_usd: float
