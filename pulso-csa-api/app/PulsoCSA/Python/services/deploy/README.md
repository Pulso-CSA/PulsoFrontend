# 🚀 Deploy Service - Serviço de Deploy

<div align="center">

![Deploy](https://img.shields.io/badge/Deploy-2196F3?style=for-the-badge&logo=rocket&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Lógica de negócio para deploy automatizado**

</div>

---

## 📋 Visão Geral

O `deploy/` implementa a **lógica de deploy automatizado**:

- 🏗️ Build de imagens Docker
- 🚀 Deploy de containers
- 📊 Monitoramento de status
- 🔙 Rollback de versões

## 📁 Estrutura

```
deploy/
└── 📄 deploy_service.py    # Serviço de deploy
```

## 🔧 Métodos Principais

```python
class DeployService:
    """Serviço de deploy automatizado."""
    
    async def start_deploy(
        self,
        project_id: str,
        environment: str,
        config: DeployConfig
    ) -> Deploy:
        """
        Inicia processo de deploy.
        
        Steps:
        1. Checkout do código
        2. Build da imagem Docker
        3. Execução de testes
        4. Deploy do container
        5. Health check
        """
        pass
    
    async def get_deploy_status(
        self, 
        deploy_id: str
    ) -> DeployStatus:
        """Obtém status atual do deploy."""
        pass
    
    async def rollback(
        self, 
        deploy_id: str
    ) -> Deploy:
        """Executa rollback para versão anterior."""
        pass
    
    async def get_deploy_logs(
        self, 
        deploy_id: str,
        tail: int = 100
    ) -> List[str]:
        """Obtém logs do deploy."""
        pass
    
    async def stop_deploy(
        self, 
        deploy_id: str
    ) -> None:
        """Cancela deploy em execução."""
        pass
```

## 🔄 Pipeline de Deploy

```python
async def _execute_pipeline(self, deploy: Deploy):
    """Executa pipeline de deploy."""
    
    steps = [
        ("checkout", self._checkout_code),
        ("build", self._build_image),
        ("test", self._run_tests),
        ("deploy", self._deploy_container),
        ("health", self._health_check)
    ]
    
    for step_name, step_func in steps:
        deploy.current_step = step_name
        await self._update_status(deploy)
        
        try:
            await step_func(deploy)
        except Exception as e:
            await self._handle_failure(deploy, step_name, e)
            raise
```

## 🔗 Links Relacionados

- [🌐 Deploy Router](../../routers/deploy_router/README.md)
- [📊 Deploy Models](../../models/deploy_models/README.md)
- [🛠️ Docker Utils](../../utils/README.md)

---

<div align="center">

**🚀 Deploy automatizado e confiável**

</div>
