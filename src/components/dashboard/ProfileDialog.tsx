import { useState } from "react";
import { User, Camera, Mail, Save, Lock, Eye, EyeOff, CreditCard, Crown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";

interface ProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ProfileDialog = ({ open, onOpenChange }: ProfileDialogProps) => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Carregar dados do localStorage
  const savedProfile = JSON.parse(localStorage.getItem("userProfile") || "{}");
  
  const [formData, setFormData] = useState({
    name: savedProfile.name || "",
    email: savedProfile.email || "",
    avatarUrl: savedProfile.avatarUrl || "",
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData({ ...formData, avatarUrl: reader.result as string });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Validar email
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      toast({
        title: "E-mail inválido",
        description: "Informe um e-mail válido",
        variant: "destructive",
      });
      setLoading(false);
      return;
    }

    // Validar senha se estiver tentando alterar
    if (formData.newPassword || formData.confirmPassword || formData.currentPassword) {
      if (!formData.currentPassword) {
        toast({
          title: "Senha atual necessária",
          description: "Informe sua senha atual para alterar a senha",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      if (formData.newPassword !== formData.confirmPassword) {
        toast({
          title: "Senhas não coincidem",
          description: "A nova senha e a confirmação devem ser iguais",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      if (formData.newPassword.length < 8) {
        toast({
          title: "Senha muito curta",
          description: "A senha deve ter pelo menos 8 caracteres",
          variant: "destructive",
        });
        setLoading(false);
        return;
      }
    }

    // Simular salvamento
    setTimeout(() => {
      const profileData = {
        name: formData.name,
        email: formData.email,
        avatarUrl: formData.avatarUrl,
      };
      localStorage.setItem("userProfile", JSON.stringify(profileData));
      
      toast({
        title: "Perfil atualizado",
        description: formData.newPassword 
          ? "Suas informações e senha foram atualizadas com sucesso" 
          : "Suas informações foram salvas com sucesso",
      });
      
      // Limpar campos de senha
      setFormData({
        ...formData,
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
      
      setLoading(false);
      onOpenChange(false);
    }, 500);
  };

  const getInitials = () => {
    if (!formData.name) return "U";
    return formData.name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader className="space-y-3 pb-4">
          <DialogTitle className="text-2xl font-bold neon-text flex items-center gap-2" style={{ color: 'hsl(180 100% 65%)' }}>
            <User className="h-6 w-6" />
            Perfil do Usuário
          </DialogTitle>
          <DialogDescription className="text-base">
            Gerencie suas informações pessoais e configurações de segurança
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 mt-2">
          {/* Avatar Section */}
          <div className="glass-strong rounded-lg p-6 space-y-4 border border-primary/20">
            <div className="flex flex-col items-center gap-4">
              <div className="relative group">
                <Avatar className="h-28 w-28 border-4 border-primary/50 neon-glow transition-all duration-300 group-hover:border-primary group-hover:scale-105">
                  <AvatarImage src={formData.avatarUrl} alt={formData.name} />
                  <AvatarFallback className="bg-primary/20 text-primary text-3xl font-bold">
                    {getInitials()}
                  </AvatarFallback>
                </Avatar>
                <div className="absolute inset-0 rounded-full bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="file"
                  id="avatar-upload"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="hidden"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => document.getElementById("avatar-upload")?.click()}
                  className="gap-2 border-primary/30 hover:border-primary hover:bg-primary/10 transition-all duration-300"
                >
                  <Camera className="h-4 w-4" />
                  Alterar Foto
                </Button>
                {formData.avatarUrl && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setFormData({ ...formData, avatarUrl: "" })}
                    className="hover:text-destructive transition-colors"
                  >
                    Remover
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Personal Info Section */}
          <div className="glass rounded-lg p-5 space-y-4 border border-primary/10">
            <h3 className="text-sm font-semibold text-primary flex items-center gap-2">
              <User className="h-4 w-4" />
              Informações Pessoais
            </h3>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-sm font-medium">
                  Nome Completo
                </Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Seu nome completo"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  className="border-primary/20 focus:border-primary transition-colors"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                  <Mail className="h-3.5 w-3.5" />
                  E-mail
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="seu@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="border-primary/20 focus:border-primary transition-colors"
                />
              </div>
            </div>
          </div>

          {/* Billing & Payments Section */}
          <div className="glass-strong rounded-lg p-5 space-y-4 border-2 border-finops/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Crown className="h-5 w-5 text-finops drop-shadow-[0_0_10px_rgba(0,255,153,0.6)]" />
                <div>
                  <h3 className="text-sm font-semibold text-finops">Plano & Pagamento</h3>
                  <p className="text-xs text-muted-foreground">Gerencie assinatura e métodos de pagamento</p>
                </div>
              </div>
              <Button
                type="button"
                onClick={() => {
                  onOpenChange(false);
                  navigate("/billing");
                }}
                className="glass glass-hover border-2 border-finops/40 hover:border-finops hover:bg-finops/10 gap-2 shadow-[0_0_15px_rgba(0,255,153,0.2)] hover:shadow-[0_0_25px_rgba(0,255,153,0.4)] transition-all duration-300"
              >
                <CreditCard className="h-4 w-4" />
                Upgrade & Pagamentos
              </Button>
            </div>
            <Separator className="bg-finops/20" />
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Plano Atual:</span>
              <span className="font-semibold text-foreground">Gratuito</span>
            </div>
          </div>

          {/* Password Section */}
          <div className="glass rounded-lg p-5 space-y-4 border border-primary/10">
            <div className="flex items-center gap-2 pb-2">
              <Lock className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold text-primary">Segurança</h3>
            </div>
            
            <p className="text-xs text-muted-foreground pb-2">
              Preencha os campos abaixo apenas se deseja alterar sua senha
            </p>

            <div className="space-y-4">
              {/* Current Password */}
              <div className="space-y-2">
                <Label htmlFor="currentPassword" className="text-sm font-medium">Senha Atual</Label>
                <div className="relative">
                  <Input
                    id="currentPassword"
                    type={showCurrentPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.currentPassword}
                    onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
                    className="border-primary/20 focus:border-primary transition-colors pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                    aria-label={showCurrentPassword ? "Ocultar senha" : "Mostrar senha"}
                  >
                    {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* New Password */}
              <div className="space-y-2">
                <Label htmlFor="newPassword" className="text-sm font-medium">Nova Senha</Label>
                <div className="relative">
                  <Input
                    id="newPassword"
                    type={showNewPassword ? "text" : "password"}
                    placeholder="Mínimo 8 caracteres"
                    value={formData.newPassword}
                    onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                    className="border-primary/20 focus:border-primary transition-colors pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                    aria-label={showNewPassword ? "Ocultar senha" : "Mostrar senha"}
                  >
                    {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirmar Nova Senha</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    className="border-primary/20 focus:border-primary transition-colors pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                    aria-label={showConfirmPassword ? "Ocultar senha" : "Mostrar senha"}
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              className="flex-1 border-primary/30 hover:border-primary hover:bg-primary/5 transition-all"
              onClick={() => onOpenChange(false)}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              className="flex-1 gap-2 bg-primary hover:bg-primary/90 neon-glow transition-all duration-300 hover:scale-105"
              disabled={loading}
            >
              <Save className="h-4 w-4" />
              {loading ? "Salvando..." : "Salvar Alterações"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default ProfileDialog;
