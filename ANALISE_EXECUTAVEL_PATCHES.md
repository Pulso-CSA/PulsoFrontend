# Análise: Executável com Patches de Atualização

## 1. É possível transformar em executável?

**Sim.** O projeto (React + Vite) pode ser empacotado como aplicação desktop usando:

### Opção A: Electron (recomendada)
- **electron-builder** ou **electron-forge** empacota o build do Vite em `.exe` (Windows), `.dmg`/`.app` (macOS), `.AppImage`/`.deb` (Linux)
- O app roda o build estático (HTML/JS/CSS) dentro de uma janela Chromium
- Suporta atualizações automáticas via **electron-updater** (delta patches)

### Opção B: Tauri
- Alternativa mais leve (usa WebView do sistema em vez de Chromium)
- Menor tamanho de binário (~3–5 MB vs ~150 MB do Electron)
- Suporta atualizações via **tauri-plugin-updater**

### Opção C: PWA (Progressive Web App)
- Não é executável tradicional, mas pode ser “instalado” no desktop
- Atualizações via service worker e cache
- Funciona bem para apps web que rodam no navegador

---

## 2. Patches de atualização

### Com Electron + electron-updater
- **Delta updates**: envia só as partes alteradas (patches), não o instalador completo
- Servidor de atualizações: GitHub Releases, S3, ou servidor próprio
- Fluxo: app verifica versão → baixa patch → aplica → reinicia

### Com Tauri
- `tauri-plugin-updater` suporta atualizações incrementais
- Formato: arquivo `.tar.gz` ou `.zip` com os binários novos
- Assinatura para garantir integridade

### Implementação sugerida (Electron)
1. Adicionar `electron` e `electron-builder` ao projeto
2. Configurar `electron-builder` com `publish` (ex.: GitHub)
3. Usar `electron-updater` no main process para checar e aplicar updates
4. Manter `latest.yml` (ou similar) no servidor com versão e URL do patch

---

## 3. Instalador profissional

**Sim, é possível.** Tanto Electron quanto Tauri oferecem geradores de instaladores nativos e profissionais.

### Opções disponíveis

| Plataforma | Instalador | Características |
|------------|------------|-----------------|
| **Windows** | NSIS | Padrão do electron-builder. Wizard passo a passo, desinstalador, atalhos, menu Iniciar. |
| **Windows** | WiX (MSI) | Formato corporativo, integração com GPO, reparo/repair. |
| **Windows** | Inno Setup | Customizável, suporta temas e scripts personalizados. |
| **macOS** | DMG | Imagem de disco com arrastar para Applications. |
| **macOS** | PKG | Instalador nativo com permissões de sistema. |
| **Linux** | AppImage | Portátil, sem instalação. |
| **Linux** | deb / rpm | Integração com gerenciadores de pacotes. |

### Recursos profissionais

- **Code signing** (assinatura de código): evita avisos do Windows Defender / SmartScreen e do Gatekeeper no macOS.  
  - Windows: certificado EV ou OV (~$200–400/ano)  
  - macOS: Apple Developer Program ($99/ano)

- **Personalização**: logo, ícone, nome do app, versão, licença no instalador.

- **Instalador silencioso**: para deploy em massa via `PulsoSetup.exe /S`.

- **Atalhos**: desktop, menu Iniciar, barra de tarefas.

### Configuração mínima (electron-builder)

```json
{
  "build": {
    "appId": "com.pulso.app",
    "productName": "Pulso",
    "directories": { "output": "dist" },
    "win": {
      "target": ["nsis", "portable"],
      "icon": "build/icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "installerIcon": "build/icon.ico",
      "uninstallerIcon": "build/icon.ico",
      "installerHeader": "build/installerHeader.bmp",
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    }
  }
}
```

### Recomendação

- **NSIS** (padrão): já oferece bom nível de profissionalismo para a maioria dos casos.
- **WiX (MSI)**: se o público for empresas com políticas de deploy rígidas.
- **Code signing**: essencial para produção; sem isso, o Windows pode bloquear a instalação.

---

## 4. Instalador customizado (pasta `installer/`)

Foi criado um instalador com interface própria, com:

- **Telas**: Welcome → EULA → Permissões → Tutorial → Instalação
- **EULA**: exemplo de contrato (substitua pelo texto real)
- **Permissões**: arquivos, rede, configurações, execução em segundo plano
- **Tutorial**: breve explicação dos três layouts (Grid, Sidebar, Bento)
- **Temas**: claro e escuro (botão no canto superior direito)
- **Efeitos**: animações de fade, slide, glow e progresso

### Como executar

```bash
cd installer
npm install
npm run dev              # Vite em http://localhost:5174
npm run installer:dev    # Build + Electron (abre a janela)
npm run installer:build  # Gera executável em dist-installer/
```

### Gerar executável para download

Após `npm run installer:build`, o executável fica em:
- `dist-installer/win-unpacked/Pulso Installer.exe` — rode diretamente ou distribua a pasta

### Como personalizar o EULA

Edite `installer/src/screens/EulaScreen.tsx` e substitua o conteúdo do bloco de texto pelo texto legal real.

---

## 5. Correção do layout Bento (histórico)

O seletor de layout foi ajustado para garantir que as **três opções** (Grid, Sidebar, Bento) apareçam:

- **Antes**: botões com texto que podiam ser cortados em telas estreitas
- **Agora**: três botões apenas com ícones (8×8), mais compactos
- Ícones: `LayoutGrid` (Grid), `PanelLeft` (Sidebar), `LayoutDashboard` (Bento)

Se ainda não aparecer o Bento:
1. Fazer **hard refresh** (Ctrl+Shift+R) ou limpar cache do navegador
2. Rodar `npm run build` e testar com `npm run preview`
3. Conferir se está na rota `/dashboard` (o layout toggle só existe nessa página)
