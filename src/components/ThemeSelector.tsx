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
import { useThemeContext, type ThemePulso } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";

const themeOptions: { id: ThemePulso; name: string; colors: [string, string, string] }[] = [
  { id: "light", name: "Claro", colors: ["#e8eef4", "#0d9488", "#5b21b6"] },
  { id: "medium", name: "Médio", colors: ["#1a1f2e", "#2dd4bf", "#7c3aed"] },
  { id: "dark", name: "Escuro", colors: ["#0c0e14", "#2dd4bf", "#6d28d9"] },
];

const ThemeSelector = () => {
  const { themePulso, setThemePulso } = useThemeContext();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 rounded-lg hover:bg-muted/80 transition-colors"
          aria-label="Selecionar tema"
        >
          <Palette className="h-5 w-5 text-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44 p-1.5 rounded-lg border border-border shadow-lg bg-popover">
        <DropdownMenuLabel className="text-xs font-medium text-muted-foreground px-2 py-1.5">Tema</DropdownMenuLabel>
        <DropdownMenuSeparator className="my-1" />
        {themeOptions.map((opt) => (
          <DropdownMenuItem
            key={opt.id}
            onClick={() => setThemePulso(opt.id)}
            className={cn(
              "cursor-pointer flex items-center justify-between gap-2 rounded-md py-2 px-2.5 transition-colors",
              themePulso === opt.id && "bg-primary/10"
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
            {themePulso === opt.id && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ThemeSelector;
