# Elemento 24 - Botão Download (Docs + Download)

## O que é
Botão "Baixar Relatório" com animação em duas camadas: ao passar o mouse, a área superior (Docs) sobe e revela a área de download com ícone animado. Cores adaptadas para a identidade Pulso (ciano/roxo).

## Referência original
From Uiverse.io by barisdogansutcu

## HTML

```html
<button class="download-button">
  <div class="docs">
    <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="16" y1="13" x2="8" y2="13"></line>
      <line x1="16" y1="17" x2="8" y2="17"></line>
      <polyline points="10 9 9 9 8 9"></polyline>
    </svg>
    Docs
  </div>
  <div class="download">
    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
      <polyline points="7 10 12 15 17 10"></polyline>
      <line x1="12" y1="15" x2="12" y2="3"></line>
    </svg>
  </div>
</button>
```

## CSS (adaptado para Pulso)
Arquivo: `src/styles/components-showcase.css` (classe: `.showcase-download-report-btn`)

```css
.showcase-download-report-btn {
  position: relative;
  border-width: 0;
  color: hsl(var(--foreground));
  font-size: 15px;
  font-weight: 600;
  border-radius: 4px;
  z-index: 1;
  overflow: hidden;
}

.showcase-download-report-btn .showcase-docs {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 40px;
  padding: 0 10px;
  border-radius: 4px;
  z-index: 1;
  background-color: hsl(var(--card));
  border: solid 1px hsl(var(--border));
  transition: all 0.5s cubic-bezier(0.77, 0, 0.175, 1);
}

.showcase-download-report-btn:hover:not(:disabled) {
  box-shadow: 0 0 30px hsl(var(--primary) / 0.25),
    hsl(var(--primary) / 0.15) 0px -12px 30px,
    rgba(0, 0, 0, 0.12) 0px 4px 6px;
}

.showcase-download-report-btn .showcase-download {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 90%;
  margin: 0 auto;
  z-index: -1;
  border-radius: 0 0 4px 4px;
  transform: translateY(0%);
  background-color: hsl(var(--primary));
  border: solid 1px hsl(var(--primary) / 0.5);
  color: hsl(var(--primary-foreground));
  transition: all 0.5s cubic-bezier(0.77, 0, 0.175, 1);
  cursor: pointer;
}

.showcase-download-report-btn:hover:not(:disabled) .showcase-download {
  transform: translateY(100%);
}

.showcase-download-report-btn .showcase-download svg polyline,
.showcase-download-report-btn .showcase-download svg line {
  animation: showcase-docs-bounce 1s infinite;
}

@keyframes showcase-docs-bounce {
  0% { transform: translateY(0%); }
  50% { transform: translateY(-15%); }
  100% { transform: translateY(0%); }
}
```

## Uso
Componente: `DownloadReportButton` em `src/components/ui/DownloadReportButton.tsx`

Usado em: CloudChat, DataChat, FinOpsChat, PromptPanel
