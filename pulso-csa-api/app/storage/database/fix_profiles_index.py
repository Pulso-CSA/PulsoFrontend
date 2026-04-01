#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Script para remover índice id_requisicao da coleção profiles❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Script para remover o índice único id_requisicao da coleção profiles.
Execute este script uma vez para corrigir o problema de chave duplicada.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()
load_dotenv(dotenv_path=".env")

# Detecta ambiente
RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID")

if RAILWAY:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pulso_database")
else:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pulso_database")

def fix_profiles_index():
    """Remove o índice id_requisicao da coleção profiles."""
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
        db = client[MONGO_DB_NAME]
        profiles_collection = db["profiles"]
        
        print(f"Conectado ao MongoDB: {MONGO_DB_NAME}")
        print(f"Verificando índices da coleção 'profiles'...")
        
        # Lista todos os índices
        indexes = list(profiles_collection.list_indexes())
        print(f"\nÍndices encontrados:")
        for idx in indexes:
            print(f"  - {idx.get('name')}: {idx.get('key')}")
        
        # Remove índices que contêm id_requisicao
        removed_count = 0
        for index in indexes:
            index_key = index.get("key", {})
            if "id_requisicao" in index_key:
                index_name = index.get("name")
                try:
                    profiles_collection.drop_index(index_name)
                    print(f"\n✅ Índice '{index_name}' removido com sucesso!")
                    removed_count += 1
                except Exception as e:
                    # Tenta remover pelo campo diretamente
                    try:
                        profiles_collection.drop_index([("id_requisicao", 1)])
                        print(f"\n✅ Índice 'id_requisicao' removido pelo campo!")
                        removed_count += 1
                    except Exception as e2:
                        print(f"\n❌ Erro ao remover índice '{index_name}': {e2}")
        
        if removed_count == 0:
            print("\n✅ Nenhum índice 'id_requisicao' encontrado. Nada a fazer.")
        else:
            print(f"\n✅ Total de índices removidos: {removed_count}")
        
        # Lista índices após a remoção
        print(f"\nÍndices após remoção:")
        indexes_after = list(profiles_collection.list_indexes())
        for idx in indexes_after:
            print(f"  - {idx.get('name')}: {idx.get('key')}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao MongoDB: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Script de correção do índice profiles")
    print("=" * 60)
    fix_profiles_index()
    print("\n" + "=" * 60)
    print("Concluído!")
    print("=" * 60)
