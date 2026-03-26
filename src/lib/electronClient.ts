/** App empacotado em Electron (preload expõe window.electronAPI). */
export function isElectronClient(): boolean {
  return typeof window !== "undefined" && !!window.electronAPI;
}

/** Canto superior direito: espaço para os 3 botões da janela (w-11 cada + padding do grupo ~11rem). */
export function themeSelectorPositionClass(): string {
  return isElectronClient() ? "absolute top-4 right-[11.5rem] z-20" : "absolute top-4 right-4 z-20";
}

/** Toolbar fixa (tema + ações): mesmo recuo que `themeSelectorPositionClass`. */
export function electronFloatingToolbarClass(): string {
  return isElectronClient()
    ? "fixed top-4 right-[11.5rem] z-50 flex items-center gap-2"
    : "fixed top-4 right-4 z-50 flex items-center gap-2";
}
