import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Keyboard } from "lucide-react";

const shortcuts = [
  { keys: ["Alt", "P"], desc: "Focar no prompt do Pulso CSA" },
  { keys: ["Alt", "F"], desc: "Focar no chat FinOps" },
  { keys: ["Alt", "D"], desc: "Focar no chat Inteligência de Dados" },
  { keys: ["Alt", "?"], desc: "Abrir este painel de atalhos" },
];

interface ShortcutsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ShortcutsModal({ open, onOpenChange }: ShortcutsModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Atalhos de teclado
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-3 pt-2">
          {shortcuts.map((s, i) => (
            <div
              key={i}
              className="flex items-center justify-between gap-4 rounded-lg border border-border/50 bg-muted/20 px-4 py-3"
            >
              <span className="text-sm text-muted-foreground">{s.desc}</span>
              <div className="flex gap-1.5">
                {s.keys.map((k, j) => (
                  <kbd
                    key={j}
                    className="rounded border border-border bg-muted px-2 py-1 text-xs font-mono font-medium"
                  >
                    {k}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
