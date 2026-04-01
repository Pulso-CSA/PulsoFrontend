# 🐍 Venv Service - Serviço de Ambientes Virtuais

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Service](https://img.shields.io/badge/Service-4CAF50?style=for-the-badge)

**Lógica de negócio para gestão de ambientes virtuais**

</div>

---

## 📋 Visão Geral

Serviço para criar e gerenciar **ambientes virtuais Python**.

## 📁 Estrutura

```
venv_service/
└── 📄 venv_service.py    # Serviço principal
```

## 🔧 Métodos

```python
class VenvService:
    """Gerencia ambientes virtuais Python."""
    
    async def create_venv(
        self,
        project_id: str,
        python_version: str = "3.11"
    ) -> VenvInfo:
        """Cria novo ambiente virtual."""
        pass
    
    async def install_packages(
        self,
        venv_id: str,
        packages: List[str]
    ) -> None:
        """Instala pacotes no ambiente."""
        pass
    
    async def delete_venv(
        self,
        venv_id: str
    ) -> None:
        """Remove ambiente virtual."""
        pass
```

## 🔗 Links Relacionados

- [🌐 Venv Router](../../routers/venv_routers/README.md)
- [🛠️ Venv Utils](../../utils/README.md)

---

<div align="center">

**🐍 Ambientes isolados e seguros**

</div>
