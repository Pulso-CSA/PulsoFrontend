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
import { sfapApi, type PlanoItem, type PlanoCreate } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Pencil, Trash2 } from "lucide-react";
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

const defaultPlano: PlanoCreate = {
  tipo_plano: "MENSAL",
  preco_unit_usd: 0,
  taxa_stripe_unit_usd: 0,
  taxa_stripe_total_10k_usd: 0,
  lucro_100_usd: 0,
  lucro_1000_usd: 0,
  lucro_10000_usd: 0,
};

export function SFAPPlanos() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [planos, setPlanos] = useState<PlanoItem[]>([]);
  const [tipoFilter, setTipoFilter] = useState<string>("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<PlanoCreate>(defaultPlano);
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const list = await sfapApi.planos.list(tipoFilter || undefined);
      setPlanos(list);
    } catch (e) {
      toast({
        title: "Erro ao carregar planos",
        description: e instanceof Error ? e.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [tipoFilter]);

  const openCreate = () => {
    setEditingId(null);
    setForm(defaultPlano);
    setDialogOpen(true);
  };

  const openEdit = (p: PlanoItem) => {
    setEditingId(p.id);
    setForm({
      tipo_plano: p.tipo_plano,
      preco_unit_usd: p.preco_unit_usd,
      taxa_stripe_unit_usd: p.taxa_stripe_unit_usd,
      taxa_stripe_total_10k_usd: p.taxa_stripe_total_10k_usd,
      lucro_100_usd: p.lucro_100_usd,
      lucro_1000_usd: p.lucro_1000_usd,
      lucro_10000_usd: p.lucro_10000_usd,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editingId) {
        await sfapApi.planos.update(editingId, form);
        toast({ title: "Plano atualizado" });
      } else {
        await sfapApi.planos.create(form);
        toast({ title: "Plano criado" });
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
      await sfapApi.planos.delete(id);
      toast({ title: "Plano removido" });
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

  return (
    <Card className="border-border bg-card">
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>Planos (tabela de preços)</CardTitle>
        <div className="flex items-center gap-2">
          <Select value={tipoFilter || "todos"} onValueChange={(v) => setTipoFilter(v === "todos" ? "" : v)}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Todos</SelectItem>
              <SelectItem value="MENSAL">MENSAL</SelectItem>
              <SelectItem value="ANUAL">ANUAL</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={openCreate} size="sm" className="gap-1">
            <Plus className="h-4 w-4" />
            Novo plano
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
                <TableHead>Tipo</TableHead>
                <TableHead className="text-right">Preço un. (USD)</TableHead>
                <TableHead className="text-right">Taxa Stripe un.</TableHead>
                <TableHead className="text-right">Lucro 100</TableHead>
                <TableHead className="text-right">Lucro 1k</TableHead>
                <TableHead className="text-right">Lucro 10k</TableHead>
                <TableHead className="w-[80px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {planos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                    Nenhum plano cadastrado.
                  </TableCell>
                </TableRow>
              ) : (
                planos.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.tipo_plano}</TableCell>
                    <TableCell className="text-right">${p.preco_unit_usd.toFixed(2)}</TableCell>
                    <TableCell className="text-right">${p.taxa_stripe_unit_usd.toFixed(2)}</TableCell>
                    <TableCell className="text-right">${p.lucro_100_usd.toFixed(2)}</TableCell>
                    <TableCell className="text-right">${p.lucro_1000_usd.toFixed(2)}</TableCell>
                    <TableCell className="text-right">${p.lucro_10000_usd.toFixed(2)}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(p)} aria-label="Editar plano" title="Editar plano">
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() => setDeleteId(p.id)}
                          aria-label="Excluir plano"
                          title="Excluir plano"
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
        <DialogContent className="max-w-lg border-border">
          <DialogHeader>
            <DialogTitle>{editingId ? "Editar plano" : "Novo plano"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Tipo do plano</Label>
                <Select
                  value={form.tipo_plano}
                  onValueChange={(v) => setForm((f) => ({ ...f, tipo_plano: v }))}
                >
                  <SelectTrigger aria-label="Tipo do plano">
                    <SelectValue placeholder="Tipo do plano" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MENSAL">MENSAL</SelectItem>
                    <SelectItem value="ANUAL">ANUAL</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Preço unit. (USD)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={form.preco_unit_usd || ""}
                  onChange={(e) => setForm((f) => ({ ...f, preco_unit_usd: parseFloat(e.target.value) || 0 }))}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Taxa Stripe unit. (USD)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={form.taxa_stripe_unit_usd || ""}
                  onChange={(e) => setForm((f) => ({ ...f, taxa_stripe_unit_usd: parseFloat(e.target.value) || 0 }))}
                />
              </div>
              <div>
                <Label>Taxa Stripe total 10k (USD)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={form.taxa_stripe_total_10k_usd || ""}
                  onChange={(e) => setForm((f) => ({ ...f, taxa_stripe_total_10k_usd: parseFloat(e.target.value) || 0 }))}
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Lucro 100 (USD)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={form.lucro_100_usd || ""}
                  onChange={(e) => setForm((f) => ({ ...f, lucro_100_usd: parseFloat(e.target.value) || 0 }))}
                />
              </div>
              <div>
                <Label>Lucro 1.000 (USD)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={form.lucro_1000_usd || ""}
                  onChange={(e) => setForm((f) => ({ ...f, lucro_1000_usd: parseFloat(e.target.value) || 0 }))}
                />
              </div>
              <div>
                <Label>Lucro 10.000 (USD)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={form.lucro_10000_usd || ""}
                  onChange={(e) => setForm((f) => ({ ...f, lucro_10000_usd: parseFloat(e.target.value) || 0 }))}
                />
              </div>
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
            <AlertDialogTitle>Remover plano?</AlertDialogTitle>
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
