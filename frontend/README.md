# Frontend – Inteligência de Dados

Componentes React elegantes e profissionais para exibir o chat de Inteligência de Dados. Integra com a API `POST /inteligencia-dados/chat` e o payload `IDChatOutput`.

## Estrutura

```
frontend/
├── design-system/
│   └── tokens.ts      # Cores, tipografia, espaçamento, sombras
├── components/
│   ├── ChatBubble.tsx
│   ├── MetricCard.tsx
│   ├── ConfusionMatrix.tsx
│   ├── ChartCard.tsx
│   ├── ModelsTable.tsx
│   ├── PredictionsDisplay.tsx
│   ├── IDResponseView.tsx   # Componente principal
│   └── index.ts
└── README.md
```

## Uso

### 1. Instalação

Copie a pasta `frontend` para seu projeto React/TypeScript e instale as dependências (se usar Chart.js/Recharts):

```bash
npm install recharts  # ou chart.js
```

### 2. Integração básica

```tsx
import { IDResponseView } from './frontend/components';

// Após receber resposta do POST /inteligencia-dados/chat
const response = await api.post('/inteligencia-dados/chat', payload);

<IDResponseView
  resposta_texto={response.data.resposta_texto}
  analise_estatistica={response.data.analise_estatistica}
  modelo_ml={response.data.modelo_ml}
  previsoes={response.data.previsoes}
  distribuicao_previsoes={response.data.distribuicao_previsoes}
  exemplos_previsao={response.data.exemplos_previsao}
  timestamp={new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
/>
```

### 3. Gráficos com Recharts

```tsx
import { BarChart, Bar, XAxis, YAxis, ScatterChart, Scatter } from 'recharts';

const ChartRenderer: React.FC<ChartRendererProps> = ({ tipo, titulo, labels, values, x, y }) => {
  if (tipo === 'dispersao' && x && y) {
    const data = x.map((xi, i) => ({ x: xi, y: y[i] }));
    return (
      <ScatterChart width={300} height={200}>
        <XAxis dataKey="x" />
        <YAxis dataKey="y" />
        <Scatter data={data} fill="#3b82f6" />
      </ScatterChart>
    );
  }
  const data = (labels ?? []).map((l, i) => ({ name: l, value: values?.[i] ?? 0 }));
  return (
    <BarChart width={300} height={200} data={data}>
      <XAxis dataKey="name" />
      <YAxis />
      <Bar dataKey="value" fill="#3b82f6" />
    </BarChart>
  );
};

<IDResponseView {...props} ChartRenderer={ChartRenderer} />
```

## Design System

- **Cores:** fundo `#1a1625`, cards `#2d2640`, destaque `#3b82f6`, sucesso `#22c55e`  
- **Tipografia:** Inter/DM Sans, JetBrains Mono para métricas  
- **Transições:** 0.2s ease em cards, hover com `translateY(-2px)`  

## Checklist de implementação

- [ ] Substituir markdown cru por `IDResponseView`
- [ ] Cards de métricas com `MetricCard`
- [ ] Matriz de confusão com `ConfusionMatrix`
- [ ] Tabela de modelos com `ModelsTable`
- [ ] Previsões com `PredictionsDisplay`
- [ ] Gráficos com `ChartRenderer` (Recharts/Chart.js)
- [ ] Loading/skeleton durante treino e previsão
