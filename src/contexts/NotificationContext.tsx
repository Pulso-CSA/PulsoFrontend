import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  PULSO_INAPP_NOTIFY_EVENT,
  type PulsoNotificationDetail,
  type PulsoNotificationKind,
} from "@/lib/pulsoNotifications";

const STORAGE_KEY = "pulso_inapp_notifications_v1";
const MAX_ITEMS = 40;

export type InAppNotification = {
  id: string;
  title: string;
  body?: string;
  kind: PulsoNotificationKind;
  createdAt: number;
  read: boolean;
};

type NotificationContextValue = {
  items: InAppNotification[];
  unreadCount: number;
  push: (detail: PulsoNotificationDetail) => void;
  markAllRead: () => void;
  remove: (id: string) => void;
  clearAll: () => void;
};

const NotificationContext = createContext<NotificationContextValue | null>(null);

function loadStored(): InAppNotification[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(
        (x): x is InAppNotification =>
          x &&
          typeof x === "object" &&
          typeof (x as InAppNotification).id === "string" &&
          typeof (x as InAppNotification).title === "string" &&
          typeof (x as InAppNotification).createdAt === "number",
      )
      .slice(0, MAX_ITEMS);
  } catch {
    return [];
  }
}

function persist(items: InAppNotification[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_ITEMS)));
  } catch {
    /* ignore */
  }
}

function tryBrowserNotification(title: string, body?: string) {
  if (typeof window === "undefined" || !("Notification" in window)) return;
  if (document.visibilityState === "visible") return;
  if (Notification.permission !== "granted") return;
  try {
    new Notification(title, { body: body || undefined, icon: `${import.meta.env.BASE_URL}App.png` });
  } catch {
    /* ignore */
  }
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<InAppNotification[]>(() =>
    typeof window !== "undefined" ? loadStored() : [],
  );

  useEffect(() => {
    persist(items);
  }, [items]);

  const push = useCallback((detail: PulsoNotificationDetail) => {
    const id =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `n-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const kind: PulsoNotificationKind = detail.kind ?? "info";
    const entry: InAppNotification = {
      id,
      title: detail.title,
      body: detail.body,
      kind,
      createdAt: Date.now(),
      read: false,
    };
    setItems((prev) => [entry, ...prev].slice(0, MAX_ITEMS));
    tryBrowserNotification(detail.title, detail.body);
  }, []);

  useEffect(() => {
    const onEvent = (ev: Event) => {
      const e = ev as CustomEvent<PulsoNotificationDetail>;
      if (e.detail?.title) push(e.detail);
    };
    window.addEventListener(PULSO_INAPP_NOTIFY_EVENT, onEvent);
    return () => window.removeEventListener(PULSO_INAPP_NOTIFY_EVENT, onEvent);
  }, [push]);

  const markAllRead = useCallback(() => {
    setItems((prev) => prev.map((x) => ({ ...x, read: true })));
  }, []);

  const remove = useCallback((id: string) => {
    setItems((prev) => prev.filter((x) => x.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setItems([]);
  }, []);

  const unreadCount = useMemo(() => items.filter((x) => !x.read).length, [items]);

  const value = useMemo(
    () => ({
      items,
      unreadCount,
      push,
      markAllRead,
      remove,
      clearAll,
    }),
    [items, unreadCount, push, markAllRead, remove, clearAll],
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export function useNotifications(): NotificationContextValue {
  const ctx = useContext(NotificationContext);
  if (!ctx) {
    throw new Error("useNotifications must be used within NotificationProvider");
  }
  return ctx;
}

/** Para componentes que podem estar fora do provider (fallback no-op). */
export function useNotificationsOptional(): NotificationContextValue | null {
  return useContext(NotificationContext);
}
