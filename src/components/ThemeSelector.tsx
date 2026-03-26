import { Palette, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useLayoutContext } from "@/contexts/LayoutContext";
import { cn } from "@/lib/utils";

const themeOptions: { id: "light" | "dark"; name: string; colors: [string, string, string] }[] = [
  { id: "light", name: "Claro", colors: ["#f8fafc", "#0f172a", "#10b981"] },
  { id: "dark", name: "Escuro", colors: ["#0c0e14", "#2dd4bf", "#6d28d9"] },
];

const ThemeSelector = () => {
  const { themeMode, setThemeMode } = useLayoutContext();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-9 gap-1.5 px-2 rounded-lg hover:bg-muted/80 transition-colors text-foreground"
          aria-label="Selecionar tema (claro ou escuro)"
          title="Alterar tema"
        >
          <Palette className="h-5 w-5 shrink-0" />
          <span className="hidden sm:inline text-xs font-medium">Tema</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44 p-1.5 rounded-lg border border-border shadow-lg bg-popover">
        <DropdownMenuLabel className="text-xs font-medium text-muted-foreground px-2 py-1.5">Tema</DropdownMenuLabel>
        <DropdownMenuSeparator className="my-1" />
        {themeOptions.map((opt) => (
          <DropdownMenuItem
            key={opt.id}
            onClick={() => setThemeMode(opt.id)}
            className={cn(
              "cursor-pointer flex items-center justify-between gap-2 rounded-md py-2 px-2.5 transition-colors",
              themeMode === opt.id && "bg-primary/10"
            )}
          >
            <div className="flex items-center gap-2.5">
              <div className="flex gap-1">
                {opt.colors.map((hex, i) => (
                  <div key={i} className="w-3 h-3 rounded-md border border-border/40" style={{ backgroundColor: hex }} />
                ))}
              </div>
              <span className="text-sm font-medium">{opt.name}</span>
            </div>
            {themeMode === opt.id && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ThemeSelector;
