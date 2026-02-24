import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface DataPreviewTableProps {
  colunas: string[];
  linhas: Record<string, unknown>[];
  titulo?: string;
  maxCellWidth?: number;
}

export function DataPreviewTable({
  colunas,
  linhas,
  titulo = "Primeiras linhas",
  maxCellWidth = 200,
}: DataPreviewTableProps) {
  if (!colunas?.length || !linhas?.length) return null;

  return (
    <div className="mt-4 space-y-2">
      {titulo && (
        <p className="text-sm font-semibold text-foreground">{titulo}</p>
      )}
      <div className="overflow-x-auto rounded-xl border border-white/10 bg-card/50 shadow-md transition-all duration-200 hover:shadow-lg hover:border-white/15">
        <table className="min-w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              {colunas.map((c) => (
                <th
                  key={c}
                  className="px-4 py-2 text-left font-semibold text-foreground"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {linhas.map((row, i) => (
              <tr
                key={i}
                className={
                  i % 2 === 0 ? "bg-background" : "bg-muted/20"
                }
              >
                {colunas.map((c) => {
                  const val = row[c];
                  const str = val != null ? String(val) : "—";
                  const truncated =
                    str.length > 20 ? str.slice(0, 17) + "…" : str;
                  return (
                    <td
                      key={c}
                      className="px-4 py-2 text-foreground tabular-nums"
                      style={{ maxWidth: maxCellWidth }}
                    >
                      {str.length > 20 ? (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="block truncate cursor-help">
                                {truncated}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent
                              side="top"
                              className="max-w-xs break-all"
                            >
                              {str}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      ) : (
                        str
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
