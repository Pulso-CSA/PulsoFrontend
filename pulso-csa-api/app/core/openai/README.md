# 🤖 OpenAI Core - Integração com IA

<div align="center">

![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-00ADD8?style=for-the-badge)

**Núcleo de integração com OpenAI e sistema RAG**

</div>

---

## 📋 Visão Geral

O módulo `openai/` centraliza a **integração com IA**:

- 🤖 Cliente OpenAI com retry e logging
- 🧬 Classe base para agentes
- 📚 Sistema RAG com FAISS
- 🎓 Treinamento generativo

## 📁 Estrutura

```
openai/
├── 📄 openai_client.py       # Cliente OpenAI wrapper
├── 📄 agent_base.py          # Classe base para agentes
├── 📄 rag_trainer.py         # Treinamento RAG com FAISS
└── 📄 generative_trainer.py  # Treinamento generativo
```

## 🔍 Componentes

### `openai_client.py`

Wrapper do cliente OpenAI com funcionalidades extras.

```python
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenAIClient:
    """
    Cliente OpenAI com retry, logging e rate limiting.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL  # gpt-4-turbo
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Gera resposta usando GPT.
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Prompt de sistema (opcional)
            temperature: Criatividade (0-1)
            max_tokens: Limite de tokens
            
        Returns:
            Resposta gerada
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def get_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Gera embeddings para textos.
        """
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]
```

### `agent_base.py`

Classe base abstrata para todos os agentes.

```python
from abc import ABC, abstractmethod

class AgentBase(ABC):
    """
    Classe base para agentes de IA.
    """
    
    def __init__(self):
        self.client = OpenAIClient()
        self.prompts = self.load_prompts()
    
    @abstractmethod
    async def process(self, input: dict) -> dict:
        """
        Processa entrada e retorna resultado.
        Deve ser implementado por subclasses.
        """
        pass
    
    def load_prompts(self) -> dict:
        """Carrega templates de prompts."""
        pass
    
    async def _call_llm(
        self,
        prompt_name: str,
        variables: dict
    ) -> str:
        """
        Chama LLM com template de prompt.
        """
        prompt = self.prompts[prompt_name].format(**variables)
        return await self.client.generate(prompt)
```

### `rag_trainer.py`

Sistema de RAG (Retrieval-Augmented Generation).

```python
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings

class RAGTrainer:
    """
    Gerencia treinamento e indexação para RAG.
    """
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
    
    async def train(
        self,
        documents_path: str,
        index_path: str
    ) -> None:
        """
        Treina índice RAG a partir de documentos.
        
        Args:
            documents_path: Caminho dos documentos
            index_path: Caminho para salvar índice
        """
        # Carregar documentos
        docs = self._load_documents(documents_path)
        
        # Dividir em chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(docs)
        
        # Criar índice FAISS
        self.vectorstore = FAISS.from_documents(
            chunks,
            self.embeddings
        )
        
        # Salvar índice
        self.vectorstore.save_local(index_path)
    
    async def query(
        self,
        question: str,
        k: int = 5
    ) -> List[Document]:
        """
        Busca documentos relevantes.
        """
        return self.vectorstore.similarity_search(question, k=k)
    
    def load_index(self, index_path: str) -> None:
        """Carrega índice existente."""
        self.vectorstore = FAISS.load_local(
            index_path,
            self.embeddings
        )
```

### `generative_trainer.py`

Treinamento de modelos generativos.

```python
class GenerativeTrainer:
    """
    Treinamento e fine-tuning de modelos generativos.
    """
    
    async def prepare_training_data(
        self,
        input_path: str,
        output_path: str
    ) -> None:
        """Prepara dados para fine-tuning."""
        pass
    
    async def create_fine_tune_job(
        self,
        training_file: str,
        model: str = "gpt-3.5-turbo"
    ) -> str:
        """Cria job de fine-tuning na OpenAI."""
        pass
    
    async def check_fine_tune_status(
        self,
        job_id: str
    ) -> dict:
        """Verifica status do fine-tuning."""
        pass
```

## 🔧 Configuração

Variáveis de ambiente necessárias:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## 🔗 Links Relacionados

- [🤖 Agents](../../agents/README.md)
- [📚 Datasets](../../datasets/README.md)
- [📝 Prompts](../../prompts/README.md)
- [💾 Storage](../../storage/README.md)

---

<div align="center">

**🤖 Inteligência Artificial de ponta**

</div>
