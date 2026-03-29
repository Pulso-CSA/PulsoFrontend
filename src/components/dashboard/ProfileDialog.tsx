import { useState, useEffect } from "react";
import { User, Camera, Mail, Save, Lock, Eye, EyeOff, CreditCard, Crown, Key, Globe } from "lucide-react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ProfileManagement from "./ProfileManagement";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { authApi } from "@/lib/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getStoredUiLanguage,
  setStoredUiLanguage,
  UI_LANGUAGE_OPTIONS,
  uiLanguageLabel,
} from "@/lib/uiLanguages";
import { useTranslation } from "react-i18next";
import i18n from "@/i18n";
import { resolveInitialI18nLng } from "@/lib/i18nLanguages";

interface ProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ProfileDialog = ({ open, onOpenChange }: ProfileDialogProps) => {
  const { t } = useTranslation();
  const { toast } = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    avatarUrl: "",
    openaiApiKey: "",
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [accountCategory, setAccountCategory] = useState<
    "perfil" | "api" | "plano" | "seguranca" | "idiomas"
  >("perfil");
  const [uiLang, setUiLang] = useState(() => getStoredUiLanguage());

  useEffect(() => {
    if (!open) return;
    const stored = getStoredUiLanguage();
    setUiLang(stored);
    const lng = resolveInitialI18nLng(stored);
    if (i18n.language !== lng) {
      void i18n.changeLanguage(lng);
    }
  }, [open]);

  useEffect(() => {
    if (open && user) {
      setFormData((prev) => ({
        ...prev,
        name: user.name || "",
        email: user.email || "",
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      }));
    }
  }, [open, user?.name, user?.email]);

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
    if (accountCategory === "idiomas" || accountCategory === "plano") {
      return;
    }
    setLoading(true);

    // Validar email
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      toast({
        title: t("profile.invalidEmail"),
        description: t("profile.invalidEmailDesc"),
        variant: "destructive",
      });
      setLoading(false);
      return;
    }

    // Validar senha se estiver tentando alterar
    if (formData.newPassword || formData.confirmPassword || formData.currentPassword) {
      if (!formData.currentPassword) {
        toast({
          title: t("profile.currentPasswordRequired"),
          description: t("profile.currentPasswordRequiredDesc"),
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      if (formData.newPassword !== formData.confirmPassword) {
        toast({
          title: t("profile.passwordMismatch"),
          description: t("profile.passwordMismatchDesc"),
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      if (formData.newPassword.length < 8) {
        toast({
          title: t("profile.passwordTooShort"),
          description: t("profile.passwordTooShortDesc"),
          variant: "destructive",
        });
        setLoading(false);
        return;
      }
    }

    try {
      const payload: { name?: string; email?: string; new_password?: string; picture?: string } = {
        name: formData.name.trim(),
        email: formData.email.trim(),
      };
      if (formData.newPassword) {
        payload.new_password = formData.newPassword;
      }
      if (formData.avatarUrl) {
        payload.picture = formData.avatarUrl;
      }

      await authApi.updateMe(payload);
      await refreshUser();
      queryClient.invalidateQueries({ queryKey: ["sfap-visibility"] });

      toast({
        title: t("profile.updated"),
        description: formData.newPassword ? t("profile.updatedWithPassword") : t("profile.updatedInfo"),
      });

      setFormData({
        ...formData,
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });

      onOpenChange(false);
    } catch (error) {
      toast({
        title: t("profile.updateError"),
        description: error instanceof Error ? error.message : t("profile.tryAgain"),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
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
      <DialogContent
        overlayClassName="pulso-dialog-overlay-blur"
        className="w-[min(92vw,960px)] max-w-[92vw] max-h-[78vh] overflow-y-auto overflow-x-hidden glass-strong border border-primary/20 rounded-2xl shadow-[0_0_40px_hsl(var(--primary)/0.12)] p-6 gap-4 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 duration-300"
      >
        <DialogHeader className="space-y-2 pb-6">
          <DialogTitle className="text-2xl font-bold flex items-center gap-3 text-foreground">
            <div className="p-2 rounded-xl bg-primary/10">
              <User className="h-6 w-6 text-primary" />
            </div>
            {t("profile.title")}
          </DialogTitle>
          <DialogDescription className="text-sm text-foreground/75">
            {t("profile.description")}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="account" className="mt-2">
          <TabsList className="grid w-full grid-cols-2 h-11 border border-border bg-muted/30">
            <TabsTrigger
              value="account"
              className="text-foreground/80 data-[state=active]:bg-primary/15 data-[state=active]:text-primary data-[state=active]:font-semibold data-[state=active]:border data-[state=active]:border-primary/30"
            >
              {t("profile.tabAccount")}
            </TabsTrigger>
            <TabsTrigger
              value="profiles"
              className="text-foreground/80 data-[state=active]:bg-primary/15 data-[state=active]:text-primary data-[state=active]:font-semibold data-[state=active]:border data-[state=active]:border-primary/30"
            >
              {t("profile.tabProfiles")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="account" className="mt-6">
            <form onSubmit={handleSubmit} className="space-y-0">
            {/* Navegação por categorias */}
            <div className="flex flex-wrap gap-2 mb-6 pb-4 border-b border-primary/20">
              <button
                type="button"
                onClick={() => setAccountCategory("perfil")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  accountCategory === "perfil"
                    ? "bg-primary/20 text-primary border border-primary/40"
                    : "border border-border bg-card/90 text-foreground/90 hover:bg-muted hover:text-foreground"
                }`}
              >
                <User className="h-4 w-4" />
                {t("profile.catProfile")}
              </button>
              <button
                type="button"
                onClick={() => setAccountCategory("api")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  accountCategory === "api"
                    ? "bg-primary/20 text-primary border border-primary/40"
                    : "border border-border bg-card/90 text-foreground/90 hover:bg-muted hover:text-foreground"
                }`}
              >
                <Key className="h-4 w-4" />
                {t("profile.catApi")}
              </button>
              <button
                type="button"
                onClick={() => setAccountCategory("plano")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  accountCategory === "plano"
                    ? "bg-primary/20 text-primary border border-primary/40"
                    : "border border-border bg-card/90 text-foreground/90 hover:bg-muted hover:text-foreground"
                }`}
              >
                <Crown className="h-4 w-4" />
                {t("profile.catPlan")}
              </button>
              <button
                type="button"
                onClick={() => setAccountCategory("seguranca")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  accountCategory === "seguranca"
                    ? "bg-primary/20 text-primary border border-primary/40"
                    : "border border-border bg-card/90 text-foreground/90 hover:bg-muted hover:text-foreground"
                }`}
              >
                <Lock className="h-4 w-4" />
                {t("profile.catSecurity")}
              </button>
              <button
                type="button"
                onClick={() => setAccountCategory("idiomas")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  accountCategory === "idiomas"
                    ? "bg-primary/20 text-primary border border-primary/40"
                    : "border border-border bg-card/90 text-foreground/90 hover:bg-muted hover:text-foreground"
                }`}
              >
                <Globe className="h-4 w-4" />
                {t("profile.catLanguages")}
              </button>
            </div>

            <div className="space-y-6">
              {/* Categoria: Perfil */}
              {(accountCategory === "perfil") && (
              <>
              {/* Avatar Section */}
              <div className="glass rounded-xl p-6 space-y-4 border border-primary/20">
                <div className="flex flex-col items-center gap-4">
                  <div className="relative group">
                    <div className="absolute inset-0 rounded-full blur-md bg-primary/50 animate-pulse"></div>
                    <Avatar className="h-20 w-20 border-2 border-primary/50 shadow-lg transition-all duration-300 group-hover:scale-105 relative z-10">
                      <AvatarImage src={formData.avatarUrl} alt={formData.name} />
                      <AvatarFallback className="bg-primary/20 text-primary text-xl font-bold">
                        {getInitials()}
                      </AvatarFallback>
                    </Avatar>
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
                      className="gap-2 border-border text-foreground hover:bg-muted"
                    >
                      <Camera className="h-4 w-4" />
                      {t("profile.changePhoto")}
                    </Button>
                    {formData.avatarUrl && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setFormData({ ...formData, avatarUrl: "" })}
                        className="hover:text-destructive transition-colors"
                      >
                        {t("profile.remove")}
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              {/* Personal Info Section */}
              <div className="glass rounded-xl p-5 space-y-4 border border-primary/15">
                <h3 className="text-sm font-semibold text-primary flex items-center gap-2">
                  <User className="h-4 w-4" />
                  {t("profile.accountInfo")}
                </h3>
                
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-sm font-medium">
                      {t("profile.fullName")}
                    </Label>
                    <Input
                      id="name"
                      type="text"
                      placeholder={t("profile.namePlaceholder")}
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      className="border-primary/20 focus:border-primary transition-colors"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                      <Mail className="h-3.5 w-3.5" />
                      {t("profile.email")}
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder={t("profile.emailPlaceholder")}
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                      className="border-primary/20 focus:border-primary transition-colors"
                    />
                  </div>
                </div>
              </div>
              </>
              )}

              {/* Categoria: Chave de API */}
              {(accountCategory === "api") && (
              <>
              {/* OpenAI API Key Section */}
              <div className="glass rounded-xl p-5 space-y-4 border border-primary/15">
                <div className="flex items-center gap-2 pb-2">
                  <Key className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-primary">{t("profile.openaiKeyTitle")}</h3>
                </div>
                
                <p className="text-xs text-muted-foreground pb-2">
                  {t("profile.openaiKeyHint")}
                </p>

                <div className="space-y-2">
                  <Label htmlFor="openaiApiKey" className="text-sm font-medium">{t("profile.apiKeyLabel")}</Label>
                  <div className="relative">
                    <Input
                      id="openaiApiKey"
                      type={showOpenaiKey ? "text" : "password"}
                      placeholder="sk-..."
                      value={formData.openaiApiKey}
                      onChange={(e) => setFormData({ ...formData, openaiApiKey: e.target.value })}
                      className="border-primary/20 focus:border-primary transition-colors pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                      aria-label={showOpenaiKey ? t("profile.hideKey") : t("profile.showKey")}
                    >
                      {showOpenaiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              </div>
              </>
              )}

              {/* Categoria: Plano & Pagamento */}
              {(accountCategory === "plano") && (
              <>
              {/* Billing & Payments Section */}
              <div className="glass rounded-xl p-5 space-y-4 border border-primary/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Crown className="h-5 w-5 text-primary drop-shadow-[0_0_10px_rgba(0,255,255,0.6)]" />
                    <div>
                      <h3 className="text-sm font-semibold text-primary">{t("profile.planTitle")}</h3>
                      <p className="text-xs text-muted-foreground">{t("profile.planSubtitle")}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {/* Elemento 12 - Botão Get Started (Upgrade) */}
                    <div className="relative inline-flex items-center justify-center group">
                      <div className="absolute inset-0 duration-1000 opacity-60 transition-all bg-[linear-gradient(90deg,#2E1A47,#4B2F7F,#6A4BCF,#8E78E6,#B89AF6)] rounded-xl blur-lg filter group-hover:opacity-100 group-hover:duration-200" />
                      <button
                        type="button"
                        onClick={() => {
                          onOpenChange(false);
                          navigate("/billing");
                        }}
                        className="relative inline-flex items-center justify-center gap-2 text-base rounded-xl bg-gray-900 px-6 py-2.5 font-semibold text-white transition-all duration-200 hover:bg-gray-800 hover:shadow-lg hover:-translate-y-0.5 hover:shadow-gray-600/30"
                      >
                        <CreditCard className="w-5 h-5" />
                        {t("profile.upgrade")}
                        <svg aria-hidden viewBox="0 0 10 10" height="10" width="10" fill="none" className="mt-0.5 -mr-1 stroke-white stroke-2">
                          <path d="M0 5h7" className="transition opacity-0 group-hover:opacity-100" />
                          <path d="M1 1l4 4-4 4" className="transition group-hover:translate-x-[3px]" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
                <Separator className="bg-primary/20" />
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{t("profile.currentPlan")}</span>
                  <span className="font-semibold text-foreground">{t("profile.planFree")}</span>
                </div>
              </div>
              </>
              )}

              {/* Categoria: Segurança */}
              {(accountCategory === "seguranca") && (
              <>
              {/* Password Section */}
              <div className="glass rounded-lg p-5 space-y-4 border border-primary/10">
                <div className="flex items-center gap-2 pb-2">
                  <Lock className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-primary">{t("profile.securityTitle")}</h3>
                </div>
                
                <p className="text-xs text-muted-foreground pb-2">
                  {t("profile.securityHint")}
                </p>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="currentPassword" className="text-sm font-medium">{t("profile.currentPassword")}</Label>
                    <div className="relative">
                      <Input
                        id="currentPassword"
                        type={showCurrentPassword ? "text" : "password"}
                        placeholder={t("profile.passwordPlaceholder")}
                        value={formData.currentPassword}
                        onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
                        className="border-primary/20 focus:border-primary transition-colors pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                      >
                        {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="newPassword" className="text-sm font-medium">{t("profile.newPassword")}</Label>
                    <div className="relative">
                      <Input
                        id="newPassword"
                        type={showNewPassword ? "text" : "password"}
                        placeholder={t("profile.newPasswordPlaceholder")}
                        value={formData.newPassword}
                        onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                        className="border-primary/20 focus:border-primary transition-colors pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                      >
                        {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword" className="text-sm font-medium">{t("profile.confirmPassword")}</Label>
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
                      >
                        {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              </>
              )}

              {/* Categoria: Idiomas */}
              {accountCategory === "idiomas" && (
                <div className="glass rounded-xl p-5 space-y-4 border border-primary/15">
                  <div className="flex items-center gap-2 pb-1">
                    <Globe className="h-4 w-4 text-primary" />
                    <h3 className="text-sm font-semibold text-primary">{t("profile.uiLanguageTitle")}</h3>
                  </div>
                  <p className="text-xs text-foreground/75">
                    {t("profile.uiLanguageHint")}
                  </p>
                  <div className="space-y-2">
                    <Label htmlFor="ui-language" className="text-sm font-medium text-foreground">
                      {t("profile.languageLabel")}
                    </Label>
                    <Select
                      value={uiLang}
                      onValueChange={(value) => {
                        setUiLang(value);
                        setStoredUiLanguage(value);
                        void i18n.changeLanguage(value);
                        toast({
                          title: t("profile.toastLanguageSaved"),
                          description: t("profile.toastLanguageSavedDesc", { label: uiLanguageLabel(value) }),
                        });
                      }}
                    >
                      <SelectTrigger id="ui-language" className="border-primary/20">
                        <SelectValue placeholder={t("profile.selectPlaceholder")} />
                      </SelectTrigger>
                      <SelectContent className="max-h-[min(60vh,320px)]">
                        {UI_LANGUAGE_OPTIONS.map((opt) => (
                          <SelectItem key={opt.code} value={opt.code}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

              {/* Submit Button - visível em Perfil, API e Segurança */}
              {(accountCategory === "perfil" || accountCategory === "api" || accountCategory === "seguranca") && (
              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1 border-border text-foreground bg-background hover:bg-muted"
                  onClick={() => onOpenChange(false)}
                >
                  {t("profile.cancel")}
                </Button>
                <Button
                  type="submit"
                  disabled={loading}
                  className="flex-1 gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  <Save className="w-5 h-5" />
                  {loading ? t("profile.saving") : t("profile.save")}
                </Button>
              </div>
              )}
              {accountCategory === "idiomas" && (
                <div className="flex gap-3 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1 border-border text-foreground bg-background hover:bg-muted"
                    onClick={() => setAccountCategory("perfil")}
                  >
                    {t("profile.back")}
                  </Button>
                  <Button
                    type="button"
                    className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90"
                    onClick={() => onOpenChange(false)}
                  >
                    {t("profile.close")}
                  </Button>
                </div>
              )}
            </div>
            </form>
          </TabsContent>

          <TabsContent value="profiles" className="mt-6">
            <ProfileManagement maxProfiles={5} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default ProfileDialog;
