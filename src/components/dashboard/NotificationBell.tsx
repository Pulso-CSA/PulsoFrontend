/**
 * Campainha + badge estilo WhatsApp Web + painel de notificações.
 */
import { useEffect, useRef } from "react";
import { Bell, CheckCheck, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useNotificationsOptional } from "@/contexts/NotificationContext";

function formatTime(ts: number, locale: string): string {
  try {
    const d = new Date(ts);
    const now = new Date();
    const sameDay =
      d.getDate() === now.getDate() &&
      d.getMonth() === now.getMonth() &&
      d.getFullYear() === now.getFullYear();
    if (sameDay) {
      return d.toLocaleTimeString(locale.replace("_", "-"), { hour: "2-digit", minute: "2-digit" });
    }
    return d.toLocaleString(locale.replace("_", "-"), {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function NotificationBell({ className }: { className?: string }) {
  const { t, i18n } = useTranslation();
  const ctx = useNotificationsOptional();
  const requestedPerm = useRef(false);

  useEffect(() => {
    if (requestedPerm.current) return;
    if (typeof window === "undefined" || !("Notification" in window)) return;
    if (Notification.permission === "default") {
      requestedPerm.current = true;
      void Notification.requestPermission().catch(() => {});
    }
  }, []);

  if (!ctx) return null;

  const { items, unreadCount, markAllRead, remove, clearAll } = ctx;

  const badgeLabel =
    unreadCount > 99 ? "99+" : unreadCount > 0 ? String(unreadCount) : null;

  return (
    <Popover
      onOpenChange={(open) => {
        if (open) markAllRead();
      }}
    >
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className={cn(
            "relative h-9 w-9 shrink-0 rounded-full p-0 text-foreground hover:bg-primary/15",
            className,
          )}
          aria-label={
            unreadCount > 0 ? t("notifications.bellAriaUnread", { count: unreadCount }) : t("notifications.bellAria")
          }
        >
          <Bell className="h-[22px] w-[22px]" strokeWidth={1.75} />
          {badgeLabel !== null && (
            <span
              className={cn(
                "absolute flex min-h-[1.125rem] min-w-[1.125rem] items-center justify-center rounded-full px-1",
                "bg-[#fa6678] text-[10px] font-bold leading-none text-black shadow-sm",
                "-right-0.5 -top-0.5",
              )}
              aria-hidden
            >
              {badgeLabel}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        className="w-[min(100vw-2rem,22rem)] p-0 glass-strong border-border/60 shadow-2xl"
        sideOffset={8}
      >
        <div className="flex items-center justify-between border-b border-border/50 px-3 py-2">
          <span className="text-sm font-semibold text-foreground">{t("notifications.title")}</span>
          <div className="flex items-center gap-1">
            {items.length > 0 && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-8 px-2 text-xs text-muted-foreground"
                onClick={() => clearAll()}
              >
                <Trash2 className="mr-1 h-3.5 w-3.5" />
                {t("notifications.clear")}
              </Button>
            )}
          </div>
        </div>
        {items.length === 0 ? (
          <p className="px-3 py-8 text-center text-sm text-muted-foreground">{t("notifications.empty")}</p>
        ) : (
          <ScrollArea className="max-h-[min(70vh,320px)]">
            <ul className="py-1">
              {items.map((n) => (
                <li
                  key={n.id}
                  className={cn(
                    "group border-b border-border/30 px-3 py-2.5 last:border-0",
                    !n.read && "bg-primary/5",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground leading-snug">{n.title}</p>
                      {n.body && (
                        <p className="mt-0.5 text-xs text-muted-foreground line-clamp-3 whitespace-pre-wrap">
                          {n.body}
                        </p>
                      )}
                      <p className="mt-1 text-[10px] uppercase tracking-wide text-muted-foreground/80">
                        {formatTime(n.createdAt, i18n.language)}
                        {n.kind === "error" && (
                          <span className="ml-2 text-destructive">{t("notifications.kindError")}</span>
                        )}
                        {n.kind === "success" && (
                          <span className="ml-2 text-emerald-600 dark:text-emerald-400">
                            {t("notifications.kindSuccess")}
                          </span>
                        )}
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 shrink-0 p-0 opacity-0 group-hover:opacity-100"
                      onClick={() => remove(n.id)}
                      aria-label={t("notifications.removeAria")}
                    >
                      <span className="sr-only">{t("notifications.removeAria")}</span>
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          </ScrollArea>
        )}
        {items.length > 0 && unreadCount === 0 && (
          <div className="flex items-center gap-1 border-t border-border/50 px-3 py-2 text-xs text-muted-foreground">
            <CheckCheck className="h-3.5 w-3.5" />
            {t("notifications.allRead")}
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
