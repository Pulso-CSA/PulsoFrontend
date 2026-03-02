# Elemento — Card de Progresso de Download (Glassmorphism)

## O que é

Card flutuante estilo glassmorphism que exibe o progresso do download do instalador. Inspirado em UIs premium de upload/download com:
- Ícone do arquivo + etiqueta de tipo (EXE)
- Nome do arquivo + tamanho
- Barra de progresso luminosa (gradiente primary/secondary)
- Status "Baixando..." com spinner
- Botão de fechar (dismissível)
- Brilho sutil nas bordas (primary/secondary)

## Especificação visual

| Elemento | Estilo |
|----------|--------|
| **Card** | Fundo cinza escuro translúcido, backdrop-blur, bordas arredondadas (rounded-2xl), box-shadow com glow roxo/azul |
| **Ícone** | Documento/instalador em container com bg-primary/10, ícone em text-primary |
| **Etiqueta** | "EXE" ou "INSTALLER" em badge pequeno, bg-primary/20, text-primary |
| **Nome** | Font weight 600, text-foreground, truncate se longo |
| **Tamanho** | text-muted-foreground, text-sm |
| **Barra** | Trilha: bg-muted/50; preenchimento: gradiente primary→secondary, box-shadow glow |
| **Spinner** | Ícone de seta circular giratória ao lado de "Baixando..." |
| **Fechar** | Botão circular com X, hover: bg-muted |

## HTML de referência

```html
<div class="download-progress-card">
  <button type="button" class="download-progress-card__close" aria-label="Fechar">
    <X />
  </button>
  <div class="download-progress-card__file">
    <div class="download-progress-card__icon">
      <FileDown />
    </div>
    <span class="download-progress-card__type">EXE</span>
    <span class="download-progress-card__name">Pulso-Setup.exe</span>
    <span class="download-progress-card__size">85 MB</span>
  </div>
  <div class="download-progress-card__progress">
    <div class="download-progress-card__status">
      <Loader2 class="animate-spin" />
      <span>Baixando...</span>
    </div>
    <div class="download-progress-card__bar">
      <div class="download-progress-card__bar-fill" style="width: 74%"></div>
    </div>
    <span class="download-progress-card__percent">74%</span>
  </div>
</div>
```

## Uso

- **PulsoFrontend:** Overlay ao clicar em "Baixar Pulso" na DownloadPage
- **pulso-download-hub:** Overlay ao clicar no botão de download

O progresso é simulado (0→100% em ~2s) pois o download real via `window.open` ou `<a download>` não expõe progresso. Alternativa: usar `fetch` + `ReadableStream` para download real com progresso (mais complexo).

## Arquivos

- **CSS:** `src/styles/components-showcase.css` — classe `.download-progress-card`
- **Componente:** `src/components/ui/DownloadProgressCard.tsx` (opcional, pode ser inline na página)
