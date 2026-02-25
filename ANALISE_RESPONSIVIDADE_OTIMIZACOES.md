# Análise: Responsividade, Otimizações, Segurança e Layout

Documento de análise para aplicativo desktop (PC) com foco em performance, multi-usuário e segurança.

---

## 1. Responsividade (App de PC)

### 1.1 Contexto
- **Alvo:** Desktop first (1024px+)
- **Suporte:** Tablets e mobile como fallback

### 1.2 Breakpoints configurados
| Breakpoint | Largura | Uso |
|------------|---------|-----|
| min | 320px | Mínimo suportado |
| sm | 640px | Mobile landscape |
| md | 768px | Tablet |
| lg | 1024px | Desktop |
| xl | 1280px | Desktop largo |
| 2xl | 1400px | Telas grandes |

### 1.3 Recomendações aplicadas
- Container com `max-width` por breakpoint
- `min-width: 320px` para evitar overflow
- LayerSelection em grid 1 col mobile, 4 col desktop (`md:grid-cols-4`)
- Header com `sticky` e `backdrop-blur`

### 1.4 Melhorias futuras
- [ ] Layout alternativo: sidebar compacta (ver seção 6)
- [ ] Redimensionar painéis (resizable) no dashboard
- [ ] Zoom para gráficos em telas pequenas

---

## 2. Otimizações de Velocidade

### 2.1 Build (Vite)
- **Target:** ES2020
- **Minify:** esbuild (fast)
- **Code splitting:** chunk manual (vendor, ui, charts)
- **Chunk limit:** 600KB

### 2.2 Lazy loading
- Rotas: `lazy()` para Index, Auth, Dashboard, etc.
- Suspense com fallback único

### 2.3 React Query
- `staleTime: 60_000` (1 min)
- `retry: 2` para queries

### 2.4 Cache de API
- `apiCache.ts`: cache em memória com TTL
- Perfis: 2 min
- Assinatura: 5 min
- Invalidação em create/update/delete de perfis

---

## 3. Compatibilidade Multi-Usuário

### 3.1 Perfis
- `profile_id` no storage (localStorage/sessionStorage)
- Troca de perfil sem logout
- `currentProfile` no AuthContext

### 3.2 Isolamento por sessão
- `rememberMe`: localStorage vs sessionStorage
- Tokens em storage separado por preferência

### 3.3 Melhorias futuras
- [ ] Indicador de "outro usuário editando" (collaborative)
- [ ] Sessões simultâneas por aba (isolamento por tab)

---

## 4. Segurança

### 4.1 Implementado
- Token Bearer no header
- Refresh token automático
- `X-Content-Type-Options: nosniff` no HTML
- Tokens em sessionStorage quando `rememberMe=false`

### 4.2 Recomendações (backend)
- CSP (Content-Security-Policy) no servidor
- HTTPS obrigatório
- Rate limiting em APIs sensíveis
- Sanitização de inputs no backend

### 4.3 Frontend
- Não armazenar credenciais em plaintext
- Logout ao 401 após falha de refresh

---

## 5. Cache

### 5.1 API Cache
- `getCached`, `setCache`, `invalidateCache`
- Endpoints: `/auth/profiles`, `/subscription` (GET)

### 5.2 Uso
```ts
import { invalidateCache } from '@/lib/api';
import { getCached, setCache, CACHE_TTL } from '@/lib/apiCache';
```

---

## 6. Layout Alternativo (Sidebar Compacta)

### 6.1 Proposta
Layout com sidebar fixa à esquerda para seleção de camadas, em vez de grid central.

```
┌─────────────────────────────────────────────────────────────┐
│ Header (logo, tema, usuário)                                 │
├──────────┬──────────────────────────────────────────────────┤
│ Pulso    │                                                    │
│ Cloud    │  Área principal (chat ativo)                      │
│ FinOps   │                                                    │
│ Dados    │                                                    │
│          │                                                    │
└──────────┴──────────────────────────────────────────────────┘
```

### 6.2 Vantagens
- Mais espaço para conteúdo
- Navegação rápida entre camadas
- Visual de app desktop

### 6.3 Implementação
- `LayoutCompact` com `ResizablePanelGroup` (shadcn)
- Sidebar: 64px (ícones) ou 200px (expandida)
- Estado: `activeLayer` único

---

## 7. Temas Profissionais

### 7.1 Ajustes aplicados
- **Modo claro:** fundo 98%, texto 9–11%, muted 38%
- **Modo escuro:** fundo 7–8%, texto 94%
- Saturação reduzida em primárias
- Cores corporativas neutras

### 7.2 Temas
- Neon Cyan | Clássico | Terracotta | Slate Pro | Fuchsia
