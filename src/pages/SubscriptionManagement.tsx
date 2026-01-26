import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowLeft,
  CreditCard,
  Calendar,
  AlertTriangle,
  ExternalLink,
  RefreshCw,
  XCircle,
  CheckCircle,
  Loader2,
  FileText,
  Zap,
  Star,
  Crown,
  Sparkles
} from "lucide-react";
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
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import { useSubscription } from "@/hooks/useSubscription";
import { useToast } from "@/hooks/use-toast";
import { PlanType, SubscriptionStatus } from "@/types";

const planDetails: Record<PlanType, { name: string; icon: typeof Zap; color: string }> = {
  basic: { name: "Basic", icon: Zap, color: "text-muted-foreground" },
  plus: { name: "Plus", icon: Star, color: "text-primary" },
  pro: { name: "Pro", icon: Crown, color: "text-finops" },
  elite: { name: "Elite", icon: Sparkles, color: "text-dataAi" },
};

const statusLabels: Record<SubscriptionStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  active: { label: "Ativa", variant: "default" },
  canceled: { label: "Cancelada", variant: "destructive" },
  past_due: { label: "Pagamento Pendente", variant: "destructive" },
  trialing: { label: "Período de Teste", variant: "secondary" },
  incomplete: { label: "Incompleta", variant: "outline" },
  incomplete_expired: { label: "Expirada", variant: "destructive" },
  unpaid: { label: "Não Paga", variant: "destructive" },
};

const SubscriptionManagement = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { 
    subscription, 
    invoices, 
    isLoading, 
    error,
    cancelSubscription, 
    resumeSubscription,
    getCustomerPortalUrl,
    refresh 
  } = useSubscription();
  
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [isCanceling, setIsCanceling] = useState(false);
  const [isResuming, setIsResuming] = useState(false);
  const [isOpeningPortal, setIsOpeningPortal] = useState(false);

  const handleCancelSubscription = async () => {
    setIsCanceling(true);
    try {
      await cancelSubscription(false);
      toast({
        title: "Assinatura cancelada",
        description: "Sua assinatura será cancelada no final do período atual.",
      });
      setShowCancelDialog(false);
    } catch (err) {
      toast({
        title: "Erro ao cancelar",
        description: err instanceof Error ? err.message : "Tente novamente mais tarde",
        variant: "destructive",
      });
    } finally {
      setIsCanceling(false);
    }
  };

  const handleResumeSubscription = async () => {
    setIsResuming(true);
    try {
      await resumeSubscription();
      toast({
        title: "Assinatura reativada",
        description: "Sua assinatura foi reativada com sucesso!",
      });
    } catch (err) {
      toast({
        title: "Erro ao reativar",
        description: err instanceof Error ? err.message : "Tente novamente mais tarde",
        variant: "destructive",
      });
    } finally {
      setIsResuming(false);
    }
  };

  const handleOpenCustomerPortal = async () => {
    setIsOpeningPortal(true);
    try {
      const portalUrl = await getCustomerPortalUrl();
      window.open(portalUrl, "_blank");
    } catch (err) {
      toast({
        title: "Erro",
        description: "Não foi possível abrir o portal. Tente novamente.",
        variant: "destructive",
      });
    } finally {
      setIsOpeningPortal(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    });
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency,
    }).format(amount / 100);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <div className="glass-strong border-b">
          <DashboardHeader />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  const plan = subscription ? planDetails[subscription.planId] : null;
  const PlanIcon = plan?.icon || Zap;
  const statusInfo = subscription ? statusLabels[subscription.status] : null;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <div className="glass-strong border-b">
        <DashboardHeader />
      </div>

      <main className="flex-1 container mx-auto p-4 lg:p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="flex items-center gap-4 animate-fade-in">
            <Button
              variant="outline"
              size="icon"
              onClick={() => navigate("/dashboard")}
              className="glass glass-hover border-2 border-primary/40"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex-1">
              <h1 className="text-3xl font-bold neon-text" style={{ 
                background: 'linear-gradient(135deg, hsl(180 100% 70%) 0%, hsl(150 100% 65%) 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Gerenciar Assinatura
              </h1>
              <p className="text-muted-foreground">Gerencie seu plano e pagamentos</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={refresh}
              className="gap-2 glass glass-hover border-primary/40"
            >
              <RefreshCw className="h-4 w-4" />
              Atualizar
            </Button>
          </div>

          {error && (
            <Card className="p-4 border-destructive/50 bg-destructive/10">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-destructive" />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            </Card>
          )}

          {!subscription ? (
            <Card className="glass-strong p-8 text-center border-2 border-primary/30">
              <h3 className="text-xl font-bold mb-2">Nenhuma assinatura ativa</h3>
              <p className="text-muted-foreground mb-6">
                Você ainda não possui uma assinatura. Escolha um plano para começar!
              </p>
              <Button
                onClick={() => navigate("/billing")}
                className="gap-2 bg-gradient-to-r from-primary/80 to-primary-deep/60 shadow-[0_0_20px_rgba(0,255,255,0.3)]"
              >
                <CreditCard className="h-4 w-4" />
                Ver Planos
              </Button>
            </Card>
          ) : (
            <>
              {/* Current Plan Card */}
              <Card className="glass-strong p-6 border-2 border-primary/30 animate-fade-in" style={{ animationDelay: '0.1s' }}>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <PlanIcon className={`h-12 w-12 ${plan?.color} drop-shadow-[0_0_10px_rgba(0,255,255,0.6)]`} />
                      <div className="absolute inset-0 bg-primary/20 rounded-full blur-lg" />
                    </div>
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="text-2xl font-bold">{plan?.name}</h3>
                        {statusInfo && (
                          <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
                        )}
                      </div>
                      <p className="text-muted-foreground">
                        Cobrança {subscription.billingCycle === 'monthly' ? 'mensal' : 'anual'}
                        {subscription.hasOpenAIKey && ' • Desconto OpenAI ativo'}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => navigate("/billing")}
                    className="gap-2 glass glass-hover border-primary/40"
                  >
                    Alterar Plano
                  </Button>
                </div>

                <Separator className="my-6" />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm text-muted-foreground">Próxima cobrança</p>
                      <p className="font-medium">{formatDate(subscription.currentPeriodEnd)}</p>
                    </div>
                  </div>
                  
                  {subscription.cancelAtPeriodEnd && (
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-5 w-5 text-warning" />
                      <div>
                        <p className="text-sm text-warning">Cancelamento agendado</p>
                        <p className="font-medium text-muted-foreground">
                          Acesso até {formatDate(subscription.currentPeriodEnd)}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              {/* Actions Card */}
              <Card className="glass-strong p-6 border-2 border-primary/30 animate-fade-in" style={{ animationDelay: '0.2s' }}>
                <h3 className="text-lg font-semibold mb-4">Ações</h3>
                <div className="flex flex-wrap gap-3">
                  <Button
                    variant="outline"
                    onClick={handleOpenCustomerPortal}
                    disabled={isOpeningPortal}
                    className="gap-2 glass glass-hover border-primary/40"
                  >
                    {isOpeningPortal ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <CreditCard className="h-4 w-4" />
                    )}
                    Gerenciar Pagamento
                    <ExternalLink className="h-3 w-3" />
                  </Button>

                  {subscription.cancelAtPeriodEnd ? (
                    <Button
                      onClick={handleResumeSubscription}
                      disabled={isResuming}
                      className="gap-2 bg-finops hover:bg-finops/90"
                    >
                      {isResuming ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle className="h-4 w-4" />
                      )}
                      Reativar Assinatura
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      onClick={() => setShowCancelDialog(true)}
                      className="gap-2 border-destructive/40 text-destructive hover:bg-destructive/10 hover:border-destructive"
                    >
                      <XCircle className="h-4 w-4" />
                      Cancelar Assinatura
                    </Button>
                  )}
                </div>
              </Card>

              {/* Invoices Card */}
              <Card className="glass-strong p-6 border-2 border-primary/30 animate-fade-in" style={{ animationDelay: '0.3s' }}>
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="h-5 w-5 text-primary" />
                  <h3 className="text-lg font-semibold">Histórico de Faturas</h3>
                </div>

                {invoices.length === 0 ? (
                  <p className="text-muted-foreground text-center py-4">
                    Nenhuma fatura encontrada
                  </p>
                ) : (
                  <div className="space-y-3">
                    {invoices.map((invoice) => (
                      <div
                        key={invoice.id}
                        className="flex items-center justify-between p-3 rounded-lg glass border border-primary/20"
                      >
                        <div className="flex items-center gap-4">
                          <div>
                            <p className="font-medium">
                              {formatCurrency(invoice.amount, invoice.currency)}
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {formatDate(invoice.createdAt)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge 
                            variant={invoice.status === 'paid' ? 'default' : invoice.status === 'pending' ? 'secondary' : 'destructive'}
                          >
                            {invoice.status === 'paid' ? 'Paga' : invoice.status === 'pending' ? 'Pendente' : 'Falhou'}
                          </Badge>
                          {invoice.invoiceUrl && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => window.open(invoice.invoiceUrl, "_blank")}
                            >
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </>
          )}
        </div>
      </main>

      {/* Cancel Confirmation Dialog */}
      <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-warning" />
              Cancelar Assinatura
            </AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja cancelar sua assinatura? Você continuará tendo acesso 
              até o final do período atual ({subscription && formatDate(subscription.currentPeriodEnd)}).
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancelSubscription}
              disabled={isCanceling}
              className="bg-destructive hover:bg-destructive/90"
            >
              {isCanceling ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : null}
              Sim, cancelar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default SubscriptionManagement;
