/**
 * Barra de criação por chat — estilo Power BI simplificado.
 * Usuário descreve o gráfico em linguagem natural e o insight é criado.
 */
import { useState } from "react";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { PromptSearchTextarea } from "@/components/ui/PromptSearchTextarea";

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

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue("");
  };

  const handleSuggestion = (s: string) => {
    setValue(s);
  };

  return (
    <div className={cn("pulso-insights-chat-bar", className)}>
      <div className="w-full space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Sparkles className="h-4 w-4 shrink-0 text-primary/80" />
          <span className="text-xs font-medium">Criar por chat</span>
        </div>
        <PromptSearchTextarea
          placeholder={placeholder}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onSend={handleSubmit}
          disabled={disabled}
          aria-label="Descreva o gráfico que deseja criar"
        />
        <div className="flex flex-wrap gap-1.5">
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
