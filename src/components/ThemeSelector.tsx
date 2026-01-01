import { Moon, Sun, Palette, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useThemeContext, ThemeVariant } from "@/contexts/ThemeContext";

const themeVariants: { id: ThemeVariant; name: string; colors: string[] }[] = [
  { id: "neon", name: "Neon Cyan", colors: ["#00ffff", "#00ff99", "#bf00ff"] },
  { id: "ocean", name: "Ocean Blue", colors: ["#0ea5e9", "#06b6d4", "#8b5cf6"] },
  { id: "forest", name: "Forest Green", colors: ["#22c55e", "#84cc16", "#f59e0b"] },
];

const ThemeSelector = () => {
  const { themeVariant, themeMode, setThemeVariant, toggleMode } = useThemeContext();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon"
          className="relative"
          aria-label="Selecionar tema"
        >
          <Palette className="h-5 w-5 text-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 glass-strong border-2 border-primary/30">
        <DropdownMenuLabel className="text-foreground/80">Tema</DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {/* Mode Toggle */}
        <DropdownMenuItem 
          onClick={toggleMode}
          className="cursor-pointer flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            {themeMode === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
            <span>{themeMode === "dark" ? "Modo Claro" : "Modo Escuro"}</span>
          </div>
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="text-foreground/80 text-xs">Paleta de Cores</DropdownMenuLabel>
        
        {/* Theme Variants */}
        {themeVariants.map((variant) => (
          <DropdownMenuItem
            key={variant.id}
            onClick={() => setThemeVariant(variant.id)}
            className="cursor-pointer flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <div className="flex gap-0.5">
                {variant.colors.map((color, i) => (
                  <div
                    key={i}
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <span>{variant.name}</span>
            </div>
            {themeVariant === variant.id && (
              <Check className="h-4 w-4 text-primary" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ThemeSelector;
