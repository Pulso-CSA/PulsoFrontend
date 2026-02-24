import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Formata data de forma segura. Retorna "—" se inválida ou ausente. */
export function formatarData(
  valor: string | undefined | null,
  opts?: { long?: boolean }
): string {
  if (valor == null || valor === "") return "—";
  const d = new Date(valor);
  if (isNaN(d.getTime())) return "—";
  return opts?.long
    ? d.toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })
    : d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
}
