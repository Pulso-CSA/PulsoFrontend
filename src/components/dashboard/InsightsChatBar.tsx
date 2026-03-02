/**
 * Barra de criação por chat — estilo Power BI simplificado.
 * Usuário descreve o gráfico em linguagem natural e o insight é criado.
 */
import { useState, useRef } from "react";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "Vendas por região",
  "Churn mensal",
  "Top 5 produtos",
  "Evolução de receita",
  "Distribuição por canal",
];

export interface InsightsChatBarProps {
  onSubmit: (prompt: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function InsightsChatBar({
  onSubmit,
  disabled = false,
  placeholder = "Crie um gráfico em linguagem natural...",
  className,
}: InsightsChatBarProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue("");
  };

  const handleSuggestion = (s: string) => {
    setValue(s);
    inputRef.current?.focus();
  };

  return (
    <div className={cn("pulso-insights-chat-bar", className)}>
      <div className="pulso-insights-chat-bar-inner">
        <div className="flex items-center gap-2 text-muted-foreground mb-2">
          <Sparkles className="h-4 w-4 shrink-0 text-primary/80" />
          <span className="text-xs font-medium">Criar por chat</span>
        </div>
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder={placeholder}
            disabled={disabled}
            className="flex-1 min-w-0 h-10 px-4 rounded-xl border border-border bg-background/80 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-all"
            aria-label="Descreva o gráfico que deseja criar"
          />
          <Button
            type="button"
            variant="pulso"
            size="icon"
            className="h-10 w-10 rounded-xl shrink-0 text-white"
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            aria-label="Criar gráfico"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-wrap gap-1.5 mt-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => handleSuggestion(s)}
              disabled={disabled}
              className="text-xs px-2.5 py-1 rounded-full border border-border/60 bg-muted/40 text-muted-foreground hover:bg-muted/70 hover:text-foreground hover:border-border transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
