# 📐 Struc Anal Router - Análise Estrutural

<div align="center">

![Analysis](https://img.shields.io/badge/Structural-FF5722?style=for-the-badge)
![Scanner](https://img.shields.io/badge/Scanner-4CAF50?style=for-the-badge)

**Endpoints para análise estrutural de projetos**

</div>

---

## 📋 Visão Geral

Endpoints para **análise estrutural** de projetos existentes.

## 📁 Estrutura

```
struc_anal/
└── 📄 struc_anal_router.py    # Endpoints de análise
```

## 🌐 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/struc-anal/scan` | Escanear estrutura |
| `POST` | `/struc-anal/plan` | Planejar mudanças |

## 🧪 Testes via cURL

> Base: `http://localhost:8000`

```bash
# Plano de análise estrutural
curl -s -X POST http://localhost:8000/struc-anal/plan -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"root_path\":\"/caminho/projeto\",\"prompt\":\"adicionar módulo de autenticação\",\"usuario\":\"teste\"}"
```

## 🔗 Links Relacionados

- [🔧 Struc Anal Services](../../services/struc_anal/README.md)
- [📊 Struc Anal Models](../../models/struc_anal/README.md)

---

<div align="center">

**📐 Análise estrutural inteligente**

</div>
