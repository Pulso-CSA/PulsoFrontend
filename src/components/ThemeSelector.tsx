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

const themePulsoOptions: { id: ThemePulso; name: string; colors: string[] }[] = [
  { id: "light", name: "Claro", colors: ["#FAFAFA", "#00BEC8", "#522A6F"] },
  { id: "medium", name: "Médio", colors: ["#0D0E12", "#00BEC8", "#8B5CF6"] },
  { id: "dark", name: "Escuro", colors: ["#0D0E12", "#00BEC8", "#8B5CF6"] },
];

const ThemeSelector = () => {
  const { themePulso, setThemePulso } = useThemeContext();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9 transition-all duration-300 ease-out hover:scale-105"
          aria-label="Selecionar tema"
        >
          <Palette className="h-5 w-5 text-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 glass-strong border-2 border-primary/30">
        <DropdownMenuLabel className="text-foreground/80">Tema PULSO</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {themePulsoOptions.map((opt) => (
          <DropdownMenuItem
            key={opt.id}
            onClick={() => setThemePulso(opt.id)}
            className="cursor-pointer flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <div className="flex gap-0.5">
                {opt.colors.map((color, i) => (
                  <div
                    key={i}
                    className="w-3 h-3 rounded-full ring-1 ring-border/50"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <span>{opt.name}</span>
            </div>
            {themePulso === opt.id && (
              <Check className="h-4 w-4 text-primary" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ThemeSelector;
