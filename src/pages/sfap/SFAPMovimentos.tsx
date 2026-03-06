import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { sfapApi, type MovimentoItem, type MovimentoCreate } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Pencil, Trash2, Download } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const CATEGORIAS_GASTO = ["infra", "taxa", "marketing", "folha", "outros"];
const CATEGORIAS_RECEITA = ["receita_plano", "outros"];
const RECORRENCIAS = ["único", "mensal", "anual", "personalizado"];

function defaultMovimento(): MovimentoCreate {
  return {
    data: new Date().toISOString().slice(0, 10),
    tipo: "gasto",
    categoria: "outros",
    descricao: "",
    valor_usd: 0,
    moeda: "USD",
    notas: "",
    recorrencia: "único",
  };
}

export function SFAPMovimentos() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [movimentos, setMovimentos] = useState<MovimentoItem[]>([]);
  const [filters, setFilters] = useState<{ tipo?: string; categoria?: string; data_inicio?: string; data_fim?: string }>({});
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<MovimentoCreate>(defaultMovimento());
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const list = await sfapApi.movimentos.list({
        tipo: filters.tipo,
        categoria: filters.categoria,
        data_inicio: filters.data_inicio,
        data_fim: filters.data_fim,
      });
      setMovimentos(list);
    } catch (e) {
      toast({
        title: "Erro ao carregar movimentos",
        description: e instanceof Error ? e.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filters.tipo, filters.categoria, filters.data_inicio, filters.data_fim]);

  const openCreate = () => {
    setEditingId(null);
    setForm(defaultMovimento());
    setDialogOpen(true);
  };

  const openEdit = (m: MovimentoItem) => {
    setEditingId(m.id);
    setForm({
      data: m.data.slice(0, 10),
      tipo: m.tipo,
      categoria: m.categoria,
      descricao: m.descricao,
      valor_usd: m.valor_usd,
      moeda: m.moeda,
      notas: m.notas ?? "",
      recorrencia: m.recorrencia ?? "único",
      recorrencia_intervalo: m.recorrencia_intervalo,
      recorrencia_unidade: m.recorrencia_unidade,
      plano_tipo: m.plano_tipo,
      plano_preco: m.plano_preco,
      num_usuarios: m.num_usuarios,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload: MovimentoCreate = {
        ...form,
        data: form.data.length === 10 ? `${form.data}T12:00:00.000Z` : form.data,
      };
      if (editingId) {
        await sfapApi.movimentos.update(editingId, payload);
        toast({ title: "Movimento atualizado" });
      } else {
        await sfapApi.movimentos.create(payload);
        toast({ title: "Movimento criado" });
      }
      setDialogOpen(false);
      load();
    } catch (e) {
      toast({
        title: editingId ? "Erro ao atualizar" : "Erro ao criar",
        description: e instanceof Error ? e.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await sfapApi.movimentos.delete(id);
      toast({ title: "Movimento removido" });
      setDeleteId(null);
      load();
    } catch (e) {
      toast({
        title: "Erro ao remover",
        description: e instanceof Error ? e.message : "Erro desconhecido",
        variant: "destructive",
      });
    }
  };

  const exportCsv = () => {
    const headers = ["Data", "Tipo", "Categoria", "Descrição", "Valor (USD)", "Moeda", "Recorrência"];
    const rows = movimentos.map((m) =>
      [m.data.slice(0, 10), m.tipo, m.categoria, m.descricao, m.valor_usd, m.moeda, m.recorrencia ?? ""].join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sfap-movimentos-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast({ title: "Exportado", description: "Arquivo CSV baixado." });
  };

  const categorias = form.tipo === "ganho" ? CATEGORIAS_RECEITA : CATEGORIAS_GASTO;

  return (
    <Card className="border-border bg-card">
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>Movimentos (receita e gastos)</CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          <Select value={filters.tipo || "todos"} onValueChange={(v) => setFilters((f) => ({ ...f, tipo: v === "todos" ? undefined : v }))}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Todos</SelectItem>
              <SelectItem value="ganho">Ganho</SelectItem>
              <SelectItem value="gasto">Gasto</SelectItem>
            </SelectContent>
          </Select>
          <Input
            type="date"
            placeholder="Início"
            className="w-[140px]"
            value={filters.data_inicio || ""}
            onChange={(e) => setFilters((f) => ({ ...f, data_inicio: e.target.value || undefined }))}
          />
          <Input
            type="date"
            placeholder="Fim"
            className="w-[140px]"
            value={filters.data_fim || ""}
            onChange={(e) => setFilters((f) => ({ ...f, data_fim: e.target.value || undefined }))}
          />
          <Button variant="outline" size="sm" onClick={exportCsv} className="gap-1">
            <Download className="h-4 w-4" />
            Exportar
          </Button>
          <Button onClick={openCreate} size="sm" className="gap-1">
            <Plus className="h-4 w-4" />
            Novo movimento
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Categoria</TableHead>
                <TableHead>Descrição</TableHead>
                <TableHead className="text-right">Valor (USD)</TableHead>
                <TableHead>Recorrência</TableHead>
                <TableHead className="w-[80px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {movimentos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                    Nenhum movimento encontrado.
                  </TableCell>
                </TableRow>
              ) : (
                movimentos.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell>{m.data.slice(0, 10)}</TableCell>
                    <TableCell className={m.tipo === "ganho" ? "text-green-600" : "text-destructive"}>{m.tipo}</TableCell>
                    <TableCell>{m.categoria}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{m.descricao}</TableCell>
                    <TableCell className="text-right font-medium">${m.valor_usd.toFixed(2)}</TableCell>
                    <TableCell>{m.recorrencia ?? "—"}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(m)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() => setDeleteId(m.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg border-border max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingId ? "Editar movimento" : "Novo movimento"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Tipo</Label>
                <Select value={form.tipo} onValueChange={(v: "ganho" | "gasto") => setForm((f) => ({ ...f, tipo: v, categoria: v === "ganho" ? "receita_plano" : "outros" }))}>
                  <SelectTrigger aria-label="Tipo (ganho ou gasto)">
                    <SelectValue placeholder="Tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ganho">Ganho</SelectItem>
                    <SelectItem value="gasto">Gasto</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Categoria</Label>
                <Select value={form.categoria} onValueChange={(v) => setForm((f) => ({ ...f, categoria: v }))}>
                  <SelectTrigger aria-label="Categoria">
                    <SelectValue placeholder="Categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    {categorias.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Data</Label>
                <Input
                  type="date"
                  value={form.data.slice(0, 10)}
                  onChange={(e) => setForm((f) => ({ ...f, data: e.target.value }))}
                />
              </div>
              <div>
                <Label>Valor (USD)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={form.valor_usd || ""}
                  onChange={(e) => setForm((f) => ({ ...f, valor_usd: parseFloat(e.target.value) || 0 }))}
                />
              </div>
            </div>
            <div>
              <Label>Descrição</Label>
              <Input
                value={form.descricao}
                onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
                placeholder="Descrição do movimento"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Recorrência</Label>
                <Select value={form.recorrencia || "único"} onValueChange={(v) => setForm((f) => ({ ...f, recorrencia: v }))}>
                  <SelectTrigger aria-label="Recorrência">
                    <SelectValue placeholder="Recorrência" />
                  </SelectTrigger>
                  <SelectContent>
                    {RECORRENCIAS.map((r) => (
                      <SelectItem key={r} value={r}>{r}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {(form.recorrencia === "personalizado") && (
                <>
                  <div>
                    <Label>Intervalo</Label>
                    <Input
                      type="number"
                      min={1}
                      value={form.recorrencia_intervalo ?? ""}
                      onChange={(e) => setForm((f) => ({ ...f, recorrencia_intervalo: parseInt(e.target.value, 10) || undefined }))}
                    />
                  </div>
                  <div>
                    <Label>Unidade</Label>
                    <Select value={form.recorrencia_unidade || "meses"} onValueChange={(v) => setForm((f) => ({ ...f, recorrencia_unidade: v }))}>
                      <SelectTrigger aria-label="Unidade de recorrência">
                        <SelectValue placeholder="Unidade" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="meses">Meses</SelectItem>
                        <SelectItem value="dias">Dias</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}
            </div>
            {form.tipo === "ganho" && (
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Tipo plano</Label>
                  <Input
                    value={form.plano_tipo ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, plano_tipo: e.target.value || undefined }))}
                    placeholder="ex: MENSAL"
                  />
                </div>
                <div>
                  <Label>Preço plano</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={form.plano_preco ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, plano_preco: parseFloat(e.target.value) || undefined }))}
                  />
                </div>
                <div>
                  <Label>Nº usuários</Label>
                  <Input
                    type="number"
                    min={0}
                    value={form.num_usuarios ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, num_usuarios: parseInt(e.target.value, 10) || undefined }))}
                  />
                </div>
              </div>
            )}
            <div>
              <Label>Notas</Label>
              <Textarea
                value={form.notas ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, notas: e.target.value }))}
                placeholder="Notas opcionais"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salvar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover movimento?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deleteId && handleDelete(deleteId)}
            >
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
