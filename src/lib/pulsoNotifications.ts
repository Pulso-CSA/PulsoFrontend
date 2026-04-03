/**
 * Notificações in-app (badge + painel). Disparar de qualquer sítio sem importar React.
 */
export type PulsoNotificationKind = "success" | "info" | "update" | "error";

export type PulsoNotificationDetail = {
  title: string;
  body?: string;
  kind?: PulsoNotificationKind;
};

export const PULSO_INAPP_NOTIFY_EVENT = "pulso-inapp-notify";

export function emitPulsoNotification(detail: PulsoNotificationDetail): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(PULSO_INAPP_NOTIFY_EVENT, { detail }));
}
