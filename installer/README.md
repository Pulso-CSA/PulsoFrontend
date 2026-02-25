# Instalador Pulso

Instalador com interface customizada: telas, EULA, permissões, tutorial e temas claro/escuro.

## Executar (desenvolvimento)

```bash
npm install
npm run dev              # Vite em http://localhost:5174
npm run installer:dev    # Build + Electron (abre a janela)
```

## Gerar executável para download

```bash
npm run installer:build
```

Saída em `dist-installer/`:
- **win-unpacked/Pulso Installer.exe** — executável principal (rode diretamente)
- **Pulso Installer 1.0.0.exe** — instalador NSIS (se o build completar)
- **pulso-installer-1.0.0-x64.nsis.7z** — instalador compactado

Para distribuir: envie a pasta `win-unpacked` (ou zip) ou o `.exe` do instalador.

## Estrutura

- `src/screens/` — Telas: Welcome, EULA, Permissões, Tutorial, Instalação
- `src/installer.css` — Temas e animações
- `electron/main.js` — Processo principal do Electron

## Personalizar EULA

Edite `src/screens/EulaScreen.tsx` e substitua o conteúdo pelo texto legal real.
