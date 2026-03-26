/** App empacotado em Electron (preload expõe window.electronAPI). */
export function isElectronClient(): boolean {
  return typeof window !== "undefined" && !!window.electronAPI;
}

/** Canto superior direito: espaço para botões minimizar/maximizar/fechar (sem barra escura). */
export function themeSelectorPositionClass(): string {
  return isElectronClient() ? "absolute top-4 right-[7.5rem] z-20" : "absolute top-4 right-4 z-20";
}

/** Toolbar fixa (tema + ações): mesmo recuo que `themeSelectorPositionClass`. */
export function electronFloatingToolbarClass(): string {
  return isElectronClient()
    ? "fixed top-4 right-[7.5rem] z-50 flex items-center gap-2"
    : "fixed top-4 right-4 z-50 flex items-center gap-2";
}
