import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { sfapApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Loader2, TrendingUp, TrendingDown, Wallet } from "lucide-react";

export function SFAPDashboard() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<{
    receita_total_usd: number;
    custo_total_usd: number;
    saldo_usd: number;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await sfapApi.dashboard();
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) {
          toast({
            title: "Erro ao carregar dashboard",
            description: e instanceof Error ? e.message : "Erro desconhecido",
            variant: "destructive",
          });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [toast]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const receita = data?.receita_total_usd ?? 0;
  const custo = data?.custo_total_usd ?? 0;
  const saldo = data?.saldo_usd ?? 0;

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card className="border-border bg-card">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Receita total</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-foreground">${receita.toFixed(2)}</p>
          <p className="text-xs text-muted-foreground">USD</p>
        </CardContent>
      </Card>
      <Card className="border-border bg-card">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Custo de operação</CardTitle>
          <TrendingDown className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-foreground">${custo.toFixed(2)}</p>
          <p className="text-xs text-muted-foreground">USD</p>
        </CardContent>
      </Card>
      <Card className="border-border bg-card">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Saldo</CardTitle>
          <Wallet className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <p className={`text-2xl font-bold ${saldo >= 0 ? "text-foreground" : "text-destructive"}`}>
            ${saldo.toFixed(2)}
          </p>
          <p className="text-xs text-muted-foreground">USD</p>
        </CardContent>
      </Card>
    </div>
  );
}
