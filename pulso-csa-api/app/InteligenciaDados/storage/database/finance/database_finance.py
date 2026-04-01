#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Finance Database❯━━━━━━━━━
# Coleção Financeiro em pulso_database: planos (referência) + movimentos (receita/gasto)
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import anyio
from typing import Any, Dict, List, Optional
from bson import ObjectId
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from app.storage.database.database_core import get_collection

COLL_FINANCEIRO = get_collection("financeiro")

try:
    COLL_FINANCEIRO.create_index([("tipo_doc", ASCENDING)])
    COLL_FINANCEIRO.create_index([("tipo_doc", ASCENDING), ("data", DESCENDING)])
    COLL_FINANCEIRO.create_index([("tipo_doc", ASCENDING), ("categoria", ASCENDING)])
except Exception:
    pass


async def _run_sync(fn, *args, **kwargs):
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))


def _serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    out = dict(doc)
    out["id"] = str(doc["_id"])
    del out["_id"]
    for k in ("data", "created_at", "updated_at"):
        if k in out and isinstance(out[k], datetime):
            out[k] = out[k].isoformat()
    return out


# ─── Planos (tabela de preços / lucro por escala) ───────────────────────────
async def list_planos(filtro_tipo: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    q = {"tipo_doc": "plano"}
    if filtro_tipo:
        q["tipo_plano"] = {"$in": filtro_tipo}

    def _find():
        return list(COLL_FINANCEIRO.find(q).sort("tipo_plano", ASCENDING).sort("preco_unit_usd", ASCENDING))

    docs = await _run_sync(_find)
    return [_serialize_doc(d) for d in docs]


async def insert_plano(payload: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow()
    doc = {
        "tipo_doc": "plano",
        "tipo_plano": payload.get("tipo_plano", ""),
        "preco_unit_usd": float(payload.get("preco_unit_usd", 0)),
        "taxa_stripe_unit_usd": float(payload.get("taxa_stripe_unit_usd", 0)),
        "taxa_stripe_total_10k_usd": float(payload.get("taxa_stripe_total_10k_usd", 0)),
        "lucro_100_usd": float(payload.get("lucro_100_usd", 0)),
        "lucro_1000_usd": float(payload.get("lucro_1000_usd", 0)),
        "lucro_10000_usd": float(payload.get("lucro_10000_usd", 0)),
        "created_at": now,
        "updated_at": now,
    }
    result = await _run_sync(COLL_FINANCEIRO.insert_one, doc)
    doc["id"] = str(result.inserted_id)
    doc["created_at"] = doc["created_at"].isoformat()
    doc["updated_at"] = doc["updated_at"].isoformat()
    return _serialize_doc(doc)


async def update_plano(plano_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not plano_id or not ObjectId.is_valid(plano_id):
        return None
    now = datetime.utcnow()
    upd = {"$set": {"updated_at": now}}
    for k in ("tipo_plano", "preco_unit_usd", "taxa_stripe_unit_usd", "taxa_stripe_total_10k_usd",
              "lucro_100_usd", "lucro_1000_usd", "lucro_10000_usd"):
        if k in payload:
            upd["$set"][k] = float(payload[k]) if k.startswith(("preco", "taxa", "lucro")) else payload[k]
    result = await _run_sync(COLL_FINANCEIRO.update_one, {"_id": ObjectId(plano_id), "tipo_doc": "plano"}, upd)
    if result.modified_count == 0:
        return None
    doc = await _run_sync(COLL_FINANCEIRO.find_one, {"_id": ObjectId(plano_id)})
    return _serialize_doc(doc)


async def delete_plano(plano_id: str) -> bool:
    if not plano_id or not ObjectId.is_valid(plano_id):
        return False
    result = await _run_sync(COLL_FINANCEIRO.delete_one, {"_id": ObjectId(plano_id), "tipo_doc": "plano"})
    return result.deleted_count > 0


# ─── Movimentos (receita = ganho, gasto = custo operação) ──────────────────
async def list_movimentos(
    tipo: Optional[str] = None,
    categoria: Optional[List[str]] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = {"tipo_doc": "movimento"}
    if tipo:
        q["tipo"] = tipo
    if categoria:
        q["categoria"] = {"$in": categoria}
    if data_inicio or data_fim:
        q["data"] = {}
        if data_inicio:
            q["data"]["$gte"] = datetime.fromisoformat(data_inicio.replace("Z", "+00:00"))
        if data_fim:
            q["data"]["$lte"] = datetime.fromisoformat(data_fim.replace("Z", "+00:00"))

    def _find():
        return list(COLL_FINANCEIRO.find(q).sort("data", DESCENDING))

    docs = await _run_sync(_find)
    return [_serialize_doc(d) for d in docs]


async def insert_movimento(payload: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.utcnow()
    data_val = payload.get("data")
    if isinstance(data_val, str):
        try:
            data_dt = datetime.fromisoformat(data_val.replace("Z", "+00:00"))
        except ValueError:
            data_dt = now
    else:
        data_dt = now
    doc = {
        "tipo_doc": "movimento",
        "data": data_dt,
        "tipo": payload.get("tipo", "gasto"),
        "categoria": payload.get("categoria", "outros"),
        "descricao": payload.get("descricao", ""),
        "valor_usd": float(payload.get("valor_usd", 0)),
        "moeda": payload.get("moeda", "USD"),
        "notas": payload.get("notas", ""),
        "recorrencia": payload.get("recorrencia") or "único",
        "recorrencia_intervalo": payload.get("recorrencia_intervalo"),
        "recorrencia_unidade": payload.get("recorrencia_unidade"),
        "plano_tipo": payload.get("plano_tipo"),
        "plano_preco": payload.get("plano_preco"),
        "num_usuarios": payload.get("num_usuarios"),
        "created_at": now,
        "updated_at": now,
    }
    result = await _run_sync(COLL_FINANCEIRO.insert_one, doc)
    doc["id"] = str(result.inserted_id)
    doc["data"] = doc["data"].isoformat()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["updated_at"] = doc["updated_at"].isoformat()
    return _serialize_doc(doc)


async def update_movimento(movimento_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not movimento_id or not ObjectId.is_valid(movimento_id):
        return None
    now = datetime.utcnow()
    upd = {"$set": {"updated_at": now}}
    for k in ("data", "tipo", "categoria", "descricao", "valor_usd", "moeda", "notas",
              "recorrencia", "recorrencia_intervalo", "recorrencia_unidade", "plano_tipo", "plano_preco", "num_usuarios"):
        if k in payload:
            if k == "data" and isinstance(payload[k], str):
                try:
                    upd["$set"][k] = datetime.fromisoformat(payload[k].replace("Z", "+00:00"))
                except ValueError:
                    pass
            else:
                upd["$set"][k] = float(payload[k]) if k == "valor_usd" else payload[k]
    result = await _run_sync(COLL_FINANCEIRO.update_one, {"_id": ObjectId(movimento_id), "tipo_doc": "movimento"}, upd)
    if result.modified_count == 0:
        return None
    doc = await _run_sync(COLL_FINANCEIRO.find_one, {"_id": ObjectId(movimento_id)})
    return _serialize_doc(doc)


async def delete_movimento(movimento_id: str) -> bool:
    if not movimento_id or not ObjectId.is_valid(movimento_id):
        return False
    result = await _run_sync(COLL_FINANCEIRO.delete_one, {"_id": ObjectId(movimento_id), "tipo_doc": "movimento"})
    return result.deleted_count > 0


async def get_dashboard_totals() -> Dict[str, Any]:
    def _agg():
        pipeline = [
            {"$match": {"tipo_doc": "movimento"}},
            {"$group": {"_id": "$tipo", "total": {"$sum": "$valor_usd"}}},
        ]
        cursor = COLL_FINANCEIRO.aggregate(pipeline)
        return list(cursor)

    rows = await _run_sync(_agg)
    receita = next((r["total"] for r in rows if r["_id"] == "ganho"), 0.0)
    gasto = next((r["total"] for r in rows if r["_id"] == "gasto"), 0.0)
    return {"receita_total_usd": receita, "custo_total_usd": gasto, "saldo_usd": receita - gasto}
