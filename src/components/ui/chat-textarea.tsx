import * as React from "react";
import { cn } from "@/lib/utils";

const MAX_HEIGHT = 384; // ~24rem

export interface ChatTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  onSend?: () => void;
}

const ChatTextarea = React.forwardRef<HTMLTextAreaElement, ChatTextareaProps>(
  ({ className, value, onChange, onKeyDown, onSend, ...props }, ref) => {
    const internalRef = React.useRef<HTMLTextAreaElement | null>(null);
    const mergedRef = (el: HTMLTextAreaElement | null) => {
      (internalRef as React.MutableRefObject<HTMLTextAreaElement | null>).current = el;
      if (typeof ref === "function") ref(el);
      else if (ref) (ref as React.MutableRefObject<HTMLTextAreaElement | null>).current = el;
    };

    const adjustHeight = React.useCallback(() => {
      const el = internalRef.current;
      if (!el) return;
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
    }, []);

    React.useEffect(() => {
      adjustHeight();
    }, [value, adjustHeight]);

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange?.(e);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onSend?.();
      } else {
        onKeyDown?.(e);
      }
    };

    return (
      <textarea
        ref={mergedRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        className={cn(
          "flex min-h-[44px] w-full rounded-lg border border-white/10 bg-background px-4 py-3 text-[15px] ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50 overflow-y-auto break-words",
          "resize-none",
          className,
        )}
        style={{ maxHeight: MAX_HEIGHT }}
        rows={1}
        {...props}
      />
    );
  },
);
ChatTextarea.displayName = "ChatTextarea";

export { ChatTextarea };
