import { useState, useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff, CheckCircle2, XCircle, Chrome, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { z } from "zod";
import { useAuth } from "@/contexts/AuthContext";
import { useProfiles } from "@/hooks/useProfiles";

const Auth = () => {
  const { t, i18n } = useTranslation();
  const profileSchema = useMemo(
    () =>
      z.object({
        name: z.string().trim().min(1, t("validation.nameRequired")).max(50, t("validation.nameMax")),
        description: z.string().trim().max(200, t("validation.descMax")).optional(),
      }),
    [t, i18n.language]
  );
  const [searchParams] = useSearchParams();
  const [isLogin, setIsLogin] = useState(() => searchParams.get("mode") !== "signup");
  const { isAuthenticated, isLoading: authLoading, login, loginWithGoogle, signup, profiles } = useAuth();
  const { createProfile } = useProfiles();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  useEffect(() => {
    const mode = searchParams.get("mode");
    setIsLogin(mode !== "signup");
  }, [searchParams]);

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      if (profiles.length === 0) {
        setShowProfileDialog(true);
      } else {
        navigate("/profile-selection");
      }
    }
  }, [isAuthenticated, authLoading, profiles, navigate]);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [profileData, setProfileData] = useState({ name: "", description: "" });
  const [profileErrors, setProfileErrors] = useState<{ name?: string; description?: string }>({});
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
    rememberMe: false,
  });

  const passwordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    if (strength <= 1) return { level: t("auth.strengthWeak"), color: "text-destructive" };
    if (strength <= 2) return { level: t("auth.strengthOk"), color: "text-warning" };
    return { level: t("auth.strengthStrong"), color: "text-success" };
  };

  const passwordChecklist = useMemo(
    () => [
      { label: t("auth.checkLen"), valid: formData.password.length >= 8 },
      { label: t("auth.checkUpper"), valid: /[A-Z]/.test(formData.password) },
      { label: t("auth.checkNum"), valid: /[0-9]/.test(formData.password) },
      { label: t("auth.checkSymbol"), valid: /[^A-Za-z0-9]/.test(formData.password) },
    ],
    [t, i18n.language, formData.password]
  );

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const validateProfile = () => {
    try {
      profileSchema.parse(profileData);
      setProfileErrors({});
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: { name?: string; description?: string } = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            newErrors[err.path[0] as keyof typeof newErrors] = err.message;
          }
        });
        setProfileErrors(newErrors);
      }
      return false;
    }
  };

  const handleCreateProfile = async () => {
    if (!validateProfile()) return;

    setLoading(true);
    try {
      await createProfile({
        name: profileData.name.trim(),
        description: profileData.description.trim(),
      });

      setShowProfileDialog(false);
      toast({
        title: t("auth.toastProfileCreated"),
        description: t("auth.toastProfileCreatedDesc", { name: profileData.name }),
      });
      navigate("/profile-selection");
    } catch (error) {
      toast({
        title: t("auth.toastProfileError"),
        description: error instanceof Error ? error.message : t("auth.tryAgain"),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Validações
    if (!validateEmail(formData.email)) {
      toast({
        title: t("auth.toastInvalidEmail"),
        description: t("auth.toastInvalidEmailDesc"),
        variant: "destructive",
      });
      setLoading(false);
      return;
    }

    if (!isLogin) {
      if (formData.password !== formData.confirmPassword) {
        toast({
          title: t("auth.toastPasswordMismatch"),
          description: t("auth.toastPasswordMismatchDesc"),
          variant: "destructive",
        });
        setLoading(false);
        return;
      }

      if (!formData.acceptTerms) {
        toast({
          title: t("auth.toastAcceptTerms"),
          description: t("auth.toastAcceptTermsDesc"),
          variant: "destructive",
        });
        setLoading(false);
        return;
      }
    }

    try {
      if (isLogin) {
        await login(formData.email, formData.password, formData.rememberMe);
        toast({
          title: t("auth.toastLoginOk"),
          description: t("auth.toastWelcomeBack"),
        });
        // Navigation handled by useEffect
      } else {
        await signup(formData.email, formData.password, formData.name, formData.rememberMe);
        // Show profile dialog for new users
        setShowProfileDialog(true);
      }
    } catch (error) {
      console.error("[Auth] erro no submit", isLogin ? "login" : "signup", error);
      toast({
        title: isLogin ? t("auth.toastLoginError") : t("auth.toastSignupError"),
        description: error instanceof Error ? error.message : t("auth.tryAgain"),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      await loginWithGoogle();
    } catch {
      // Error handling is done in the auth context
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pulso-page-container pulso-auth-page min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background — semiesferas PULSO (gradiente roxo→ciano conforme App.png) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 pulso-orb animate-pulse" />
        <div className="absolute bottom-20 right-20 w-72 h-72 pulso-orb animate-pulse" style={{ animationDelay: "1s" }} />
      </div>

      <div className="w-full max-w-md relative z-10 animate-fade-in">
        <div className="text-center mb-8">
          <img
            src={import.meta.env.BASE_URL + "App.png"}
            alt="Pulso"
            className="h-14 w-14 mx-auto mb-4 object-contain"
          />
          <h1 className="text-4xl font-bold mb-2 text-primary">Pulso</h1>
          <p className="text-foreground/80">
            {isLogin ? t("auth.taglineLogin") : t("auth.taglineSignup")}
          </p>
        </div>

        <div className="pulso-page-card pulso-auth-card glass-card glass-strong rounded-2xl p-8 border border-transparent">
          {/* Google Login Button */}
          <button
            type="button"
            className="showcase-sparkle-btn w-full justify-center gap-2 mb-4 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleGoogleLogin}
            disabled={loading}
          >
            <span className="showcase-spark" aria-hidden />
            <span className="pulso-auth-sparkle-inner absolute inset-[0.1em] rounded-[100px] bg-background/80 pointer-events-none" />
            <Chrome className="w-5 h-5 relative z-10" />
            <span className="relative z-10">{t("auth.google")}</span>
          </button>

          <div className="relative my-6">
            <Separator />
            <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-3 text-xs text-muted-foreground rounded-md border border-border/60">
              {t("auth.orEmail")}
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <Label htmlFor="name">{t("auth.name")}</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder={t("auth.namePlaceholder")}
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required={!isLogin}
                />
              </div>
            )}

            <div>
              <Label htmlFor="email">{t("auth.email")}</Label>
              <Input
                id="email"
                type="email"
                placeholder={t("auth.emailPlaceholder")}
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>

            <div>
              <Label htmlFor="password">{t("auth.password")}</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? t("auth.hidePassword") : t("auth.showPassword")}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              
              {!isLogin && formData.password && (
                <div className="mt-2 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">{t("auth.strength")}</span>
                    <span className={`text-sm font-medium ${passwordStrength(formData.password).color}`}>
                      {passwordStrength(formData.password).level}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {passwordChecklist.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-1">
                        {item.valid ? (
                          <CheckCircle2 className="h-3 w-3 text-success" />
                        ) : (
                          <XCircle className="h-3 w-3 text-muted-foreground" />
                        )}
                        <span className={item.valid ? "text-foreground" : "text-muted-foreground"}>
                          {item.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {!isLogin && (
              <div>
                <Label htmlFor="confirmPassword">{t("auth.confirmPassword")}</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    required={!isLogin}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label={showConfirmPassword ? t("auth.hidePassword") : t("auth.showPassword")}
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            )}

            {/* Remember me checkbox */}
            <div className="flex items-center gap-2">
              <Checkbox
                id="rememberMe"
                checked={formData.rememberMe}
                onCheckedChange={(checked) => 
                  setFormData({ ...formData, rememberMe: checked as boolean })
                }
              />
              <Label htmlFor="rememberMe" className="text-sm font-normal cursor-pointer">
                {t("auth.rememberMe")}
              </Label>
            </div>

            {!isLogin && (
              <div className="flex items-start gap-2">
                <Checkbox
                  id="terms"
                  checked={formData.acceptTerms}
                  onCheckedChange={(checked) => 
                    setFormData({ ...formData, acceptTerms: checked as boolean })
                  }
                />
                <Label htmlFor="terms" className="text-sm font-normal cursor-pointer">
                  {t("auth.acceptTerms")}
                </Label>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="showcase-sparkle-btn w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="showcase-spark" aria-hidden />
              <span className="pulso-auth-sparkle-inner absolute inset-[0.1em] rounded-[100px] bg-background/80 pointer-events-none" />
              <span className="relative z-10">{loading ? t("auth.submitLoading") : isLogin ? t("auth.login") : t("auth.signup")}</span>
            </button>
          </form>

          <div className="mt-4 text-center space-y-2">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-primary hover:underline"
            >
              {isLogin ? t("auth.toggleSignup") : t("auth.toggleLogin")}
            </button>
            
            {isLogin && (
              <div>
                <Link
                  to="/forgot-password"
                  className="text-sm pulso-auth-link-muted hover:underline"
                >
                  {t("auth.forgotPassword")}
                </Link>
              </div>
            )}
          </div>

          {!isLogin && (
            <p className="mt-4 text-xs text-muted-foreground text-center">
              {t("auth.passwordHint")}
            </p>
          )}
        </div>
      </div>

      {/* Create First Profile Dialog */}
      <Dialog open={showProfileDialog} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-[500px]" onInteractOutside={(e) => e.preventDefault()}>
          <DialogHeader className="space-y-3">
            <DialogTitle className="text-2xl font-bold flex items-center gap-2 text-primary">
              <UserPlus className="h-6 w-6" />
              {t("auth.dialogFirstProfile")}
            </DialogTitle>
            <DialogDescription className="text-base">
              {t("auth.dialogFirstProfileDesc")}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="profile-name">{t("auth.profileName")}</Label>
              <Input
                id="profile-name"
                placeholder={t("auth.profileNamePlaceholder")}
                value={profileData.name}
                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                className={profileErrors.name ? "border-destructive" : "border-primary/20 focus:border-primary"}
              />
              {profileErrors.name && (
                <p className="text-xs text-destructive">{profileErrors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="profile-description">{t("auth.profileDesc")}</Label>
              <Input
                id="profile-description"
                placeholder={t("auth.profileDescPlaceholder")}
                value={profileData.description}
                onChange={(e) => setProfileData({ ...profileData, description: e.target.value })}
                className={profileErrors.description ? "border-destructive" : "border-primary/20 focus:border-primary"}
              />
              {profileErrors.description && (
                <p className="text-xs text-destructive">{profileErrors.description}</p>
              )}
              <p className="text-xs text-muted-foreground">
                {t("auth.profilesLimitHint")}
              </p>
            </div>

            <Button
              onClick={handleCreateProfile}
              disabled={loading}
              className="w-full gap-2 bg-primary hover:bg-primary/90 pulso-glow-cta transition-all duration-300 hover:scale-105 mt-6"
            >
              <UserPlus className="h-4 w-4" />
              {loading ? t("auth.creating") : t("auth.createProfileStart")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Auth;
