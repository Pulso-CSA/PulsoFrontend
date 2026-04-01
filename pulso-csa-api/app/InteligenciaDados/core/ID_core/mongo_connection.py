# Conexão com MongoDB externo (Inteligência de Dados – bases do usuário)
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

__all__ = ["MongoConnection"]

DEFAULT_TIMEOUT_MS = 30_000


class MongoConnection:
    """
    Conexão read-only com MongoDB externo para captura de estrutura.
    Usado pelo subsistema ID para listar coleções, contar documentos e obter amostras.
    """

    def __init__(self, db_config: Dict[str, Any]) -> None:
        if not isinstance(db_config, dict):
            raise ValueError("db_config must be a dictionary")
        self._db_config = db_config
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def _get_client(self) -> MongoClient:
        if self._client is not None:
            return self._client
        uri = self._db_config.get("uri")
        if uri:
            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=self._db_config.get("timeout_ms", DEFAULT_TIMEOUT_MS),
            )
            db_name = self._db_config.get("database") or uri.split("/")[-1].split("?")[0] or "test"
        else:
            host = self._db_config["host"]
            port = self._db_config.get("port", 27017)
            database = self._db_config["database"]
            user = self._db_config.get("user")
            password = self._db_config.get("password")
            auth = f"{user}:{password}@" if user and password else ""
            uri = f"mongodb://{auth}{host}:{port}/{database}"
            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=self._db_config.get("timeout_ms", DEFAULT_TIMEOUT_MS),
            )
            db_name = database
        self._db = self._client[db_name]
        return self._client

    @property
    def db(self) -> Database:
        self._get_client()
        assert self._db is not None
        return self._db

    def list_collection_names(self) -> List[str]:
        try:
            return self.db.list_collection_names()
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB error: {e}") from e

    def get_collection(self, name: str) -> Collection:
        return self.db[name]

    def count_documents(self, collection_name: str, filter: Optional[Dict[str, Any]] = None) -> int:
        filter = filter or {}
        try:
            return self.db[collection_name].count_documents(filter)
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB error: {e}") from e

    def find_sample(
        self,
        collection_name: str,
        limit: int = 100,
        projection: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            cursor = self.db[collection_name].find(projection=projection or {}).limit(limit)
            return list(cursor)
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB error: {e}") from e

    def get_indexes(self, collection_name: str) -> List[Dict[str, Any]]:
        try:
            return list(self.db[collection_name].list_indexes())
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB error: {e}") from e

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
