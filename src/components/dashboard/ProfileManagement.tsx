import { useState } from "react";
import { Plus, Trash2, Edit2, Check, X, Users, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { z } from "zod";
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
import { useProfiles } from "@/hooks/useProfiles";
import { useAuth } from "@/contexts/AuthContext";
import { Profile } from "@/types";

const profileSchema = z.object({
  name: z.string()
    .trim()
    .min(1, "Nome é obrigatório")
    .max(50, "Nome deve ter no máximo 50 caracteres"),
  description: z.string()
    .trim()
    .max(200, "Descrição deve ter no máximo 200 caracteres")
    .optional(),
});

interface ProfileManagementProps {
  maxProfiles?: number;
}

const ProfileManagement = ({ 
  maxProfiles = 5 
}: ProfileManagementProps) => {
  const { toast } = useToast();
  const { profiles, isLoading, createProfile, updateProfile, deleteProfile } = useProfiles();
  const { currentProfile, setCurrentProfile } = useAuth();
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({ name: "", description: "" });
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({});
  const [submitting, setSubmitting] = useState(false);

  const validateForm = () => {
    try {
      profileSchema.parse(formData);
      setErrors({});
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: { name?: string; description?: string } = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            newErrors[err.path[0] as keyof typeof newErrors] = err.message;
          }
        });
        setErrors(newErrors);
      }
      return false;
    }
  };

  const handleCreate = async () => {
    if (!validateForm()) return;

    setSubmitting(true);
    try {
      const newProfile = await createProfile({
        name: formData.name.trim(),
        description: formData.description.trim(),
      });

      setFormData({ name: "", description: "" });
      setIsCreating(false);
      setErrors({});

      toast({
        title: "Perfil criado",
        description: `Perfil "${newProfile.name}" criado com sucesso`,
      });
    } catch (error) {
      toast({
        title: "Erro ao criar perfil",
        description: error instanceof Error ? error.message : "Tente novamente",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (id: string) => {
    if (!validateForm()) return;

    setSubmitting(true);
    try {
      await updateProfile(id, {
        name: formData.name.trim(),
        description: formData.description.trim(),
      });

      setEditingId(null);
      setFormData({ name: "", description: "" });
      setErrors({});

      toast({
        title: "Perfil atualizado",
        description: "Alterações salvas com sucesso",
      });
    } catch (error) {
      toast({
        title: "Erro ao atualizar perfil",
        description: error instanceof Error ? error.message : "Tente novamente",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (profiles.length <= 1) {
      toast({
        title: "Não é possível deletar",
        description: "Você deve ter pelo menos 1 perfil",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      await deleteProfile(id);
      setDeletingId(null);

      // If deleting current profile, clear selection
      if (currentProfile?.id === id) {
        setCurrentProfile(null);
      }

      toast({
        title: "Perfil deletado",
        description: "Perfil removido com sucesso",
      });
    } catch (error) {
      toast({
        title: "Erro ao deletar perfil",
        description: error instanceof Error ? error.message : "Tente novamente",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (profile: Profile) => {
    setEditingId(profile.id);
    setFormData({ name: profile.name, description: profile.description });
    setErrors({});
  };

  const cancelEdit = () => {
    setEditingId(null);
    setIsCreating(false);
    setFormData({ name: "", description: "" });
    setErrors({});
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-primary">Meus Perfis</h3>
          <span className="text-sm text-muted-foreground">
            ({profiles.length}/{maxProfiles})
          </span>
        </div>
        {!isCreating && profiles.length < maxProfiles && (
          <Button
            onClick={() => setIsCreating(true)}
            size="sm"
            className="gap-2 bg-primary/20 hover:bg-primary/30 border-2 border-primary/50 text-primary hover:border-primary"
          >
            <Plus className="h-4 w-4" />
            Novo Perfil
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {/* Create Form */}
        {isCreating && (
          <Card className="glass-strong border-2 border-primary/30 p-4">
            <div className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="new-profile-name">Nome do Perfil*</Label>
                <Input
                  id="new-profile-name"
                  placeholder="Ex: Produção, Desenvolvimento"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={errors.name ? "border-destructive" : ""}
                  disabled={submitting}
                />
                {errors.name && (
                  <p className="text-xs text-destructive">{errors.name}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-profile-description">Descrição</Label>
                <Input
                  id="new-profile-description"
                  placeholder="Breve descrição do perfil"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className={errors.description ? "border-destructive" : ""}
                  disabled={submitting}
                />
                {errors.description && (
                  <p className="text-xs text-destructive">{errors.description}</p>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleCreate}
                  size="sm"
                  className="gap-2 bg-primary hover:bg-primary/90"
                  disabled={submitting}
                >
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  Criar
                </Button>
                <Button
                  onClick={cancelEdit}
                  size="sm"
                  variant="outline"
                  className="gap-2"
                  disabled={submitting}
                >
                  <X className="h-4 w-4" />
                  Cancelar
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Profile List */}
        {profiles.map((profile) => (
          <Card
            key={profile.id}
            className="glass border border-primary/20 p-4 hover:border-primary/40 transition-all"
          >
            {editingId === profile.id ? (
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor={`edit-name-${profile.id}`}>Nome do Perfil*</Label>
                  <Input
                    id={`edit-name-${profile.id}`}
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className={errors.name ? "border-destructive" : ""}
                    disabled={submitting}
                  />
                  {errors.name && (
                    <p className="text-xs text-destructive">{errors.name}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`edit-description-${profile.id}`}>Descrição</Label>
                  <Input
                    id={`edit-description-${profile.id}`}
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className={errors.description ? "border-destructive" : ""}
                    disabled={submitting}
                  />
                  {errors.description && (
                    <p className="text-xs text-destructive">{errors.description}</p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => handleUpdate(profile.id)}
                    size="sm"
                    className="gap-2 bg-primary hover:bg-primary/90"
                    disabled={submitting}
                  >
                    {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                    Salvar
                  </Button>
                  <Button
                    onClick={cancelEdit}
                    size="sm"
                    variant="outline"
                    className="gap-2"
                    disabled={submitting}
                  >
                    <X className="h-4 w-4" />
                    Cancelar
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-foreground truncate">{profile.name}</h4>
                  {profile.description && (
                    <p className="text-sm text-muted-foreground mt-1">{profile.description}</p>
                  )}
                  <p className="text-xs text-muted-foreground mt-2">
                    Criado em: {new Date(profile.createdAt).toLocaleDateString('pt-BR')}
                  </p>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => startEdit(profile)}
                    size="sm"
                    variant="outline"
                    className="gap-2 border-primary/30 hover:border-primary hover:bg-primary/10"
                    disabled={isLoading}
                  >
                    <Edit2 className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    onClick={() => setDeletingId(profile.id)}
                    size="sm"
                    variant="outline"
                    className="gap-2 border-destructive/30 hover:border-destructive hover:bg-destructive/10 text-destructive"
                    disabled={profiles.length <= 1 || isLoading}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deletingId} onOpenChange={() => setDeletingId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Deletar Perfil</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja deletar este perfil? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={submitting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deletingId && handleDelete(deletingId)}
              className="bg-destructive hover:bg-destructive/90"
              disabled={submitting}
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Deletar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default ProfileManagement;
