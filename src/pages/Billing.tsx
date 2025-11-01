import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  ArrowLeft, 
  Check, 
  CreditCard, 
  QrCode, 
  FileText, 
  Building2,
  Smartphone,
  Zap,
  Crown,
  Star,
  Sparkles
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import DashboardHeader from "@/components/dashboard/DashboardHeader";

const plans = [
  {
    name: "Basic",
    priceMonthly: 29.99,
    priceYearly: 24.99,
    features: [
      "Até 10 projetos",
      "Blueprint básico",
      "5 GB de armazenamento",
      "Suporte por email"
    ],
    popular: false,
    icon: Zap,
    color: "text-muted-foreground"
  },
  {
    name: "Plus",
    priceMonthly: 44.77,
    priceYearly: 34.77,
    features: [
      "Até 50 projetos",
      "Blueprint avançado",
      "FinOps básico",
      "20 GB de armazenamento",
      "Suporte prioritário"
    ],
    popular: true,
    icon: Star,
    color: "text-primary"
  },
  {
    name: "Pro",
    priceMonthly: 59.77,
    priceYearly: 49.77,
    features: [
      "Projetos ilimitados",
      "Blueprint + FinOps + Analytics",
      "100 GB de armazenamento",
      "Suporte 24/7",
      "API Access"
    ],
    popular: false,
    icon: Crown,
    color: "text-finops"
  },
  {
    name: "Elite",
    priceMonthly: 69.77,
    priceYearly: 54.77,
    features: [
      "Tudo do Pro",
      "IA personalizada",
      "500 GB de armazenamento",
      "Gerente de conta dedicado",
      "SLA garantido",
      "Treinamento customizado"
    ],
    popular: false,
    icon: Sparkles,
    color: "text-dataAi"
  }
];

const paymentMethods = [
  {
    id: "credit-card",
    name: "Cartão de Crédito",
    icon: CreditCard,
    description: "Visa, Mastercard, Amex, Elo",
    color: "primary"
  },
  {
    id: "pix",
    name: "PIX",
    icon: QrCode,
    description: "Pagamento instantâneo",
    color: "finops"
  },
  {
    id: "boleto",
    name: "Boleto Bancário",
    icon: FileText,
    description: "Vencimento em 3 dias úteis",
    color: "dataAi"
  },
  {
    id: "paypal",
    name: "PayPal",
    icon: Building2,
    description: "Pagamento internacional",
    color: "secondary"
  }
];

const Billing = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [selectedPayment, setSelectedPayment] = useState<string | null>(null);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [cardData, setCardData] = useState({
    number: "",
    name: "",
    expiry: "",
    cvv: ""
  });

  const handleSelectPlan = (planName: string) => {
    setSelectedPlan(planName);
    setShowPaymentForm(true);
  };

  const handlePaymentMethodSelect = (methodId: string) => {
    setSelectedPayment(methodId);
  };

  const handleSubmitPayment = () => {
    if (!selectedPayment) {
      toast({
        title: "Selecione um método de pagamento",
        variant: "destructive"
      });
      return;
    }

    if (selectedPayment === "credit-card") {
      if (!cardData.number || !cardData.name || !cardData.expiry || !cardData.cvv) {
        toast({
          title: "Preencha todos os dados do cartão",
          variant: "destructive"
        });
        return;
      }
    }

    toast({
      title: "Upgrade realizado com sucesso! 🎉",
      description: `Plano ${selectedPlan} ativado via ${paymentMethods.find(m => m.id === selectedPayment)?.name}`
    });

    setTimeout(() => {
      navigate("/dashboard");
    }, 2000);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <div className="glass-strong border-b">
        <DashboardHeader />
      </div>

      <main className="flex-1 container mx-auto p-4 lg:p-8">
        <div className="max-w-7xl mx-auto space-y-8">
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
            <div>
              <h1 className="text-3xl font-bold neon-text" style={{ 
                background: 'linear-gradient(135deg, hsl(180 100% 70%) 0%, hsl(150 100% 65%) 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Upgrade de Conta
              </h1>
              <p className="text-muted-foreground">Escolha o plano ideal para seu negócio</p>
            </div>
          </div>

          {/* Billing Cycle Toggle */}
          <div className="flex justify-center animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="glass-strong rounded-full p-1 inline-flex gap-1 border-2 border-primary/30">
              <Button
                variant={billingCycle === "monthly" ? "default" : "ghost"}
                size="sm"
                onClick={() => setBillingCycle("monthly")}
                className={billingCycle === "monthly" 
                  ? "rounded-full bg-gradient-to-r from-primary/80 to-primary-deep/60 shadow-[0_0_20px_rgba(0,255,255,0.4)]" 
                  : "rounded-full"}
              >
                Mensal
              </Button>
              <Button
                variant={billingCycle === "yearly" ? "default" : "ghost"}
                size="sm"
                onClick={() => setBillingCycle("yearly")}
                className={billingCycle === "yearly" 
                  ? "rounded-full bg-gradient-to-r from-finops/80 to-success/60 shadow-[0_0_20px_rgba(0,255,153,0.4)]" 
                  : "rounded-full"}
              >
                Anual
                <Badge variant="secondary" className="ml-2 text-xs">-15%</Badge>
              </Button>
            </div>
          </div>

          {/* Plans Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan, idx) => {
              const Icon = plan.icon;
              const price = billingCycle === "monthly" ? plan.priceMonthly : plan.priceYearly;
              
              return (
                <Card
                  key={plan.name}
                  className={`relative glass-strong p-6 border-2 hover:scale-105 transition-all duration-500 animate-fade-in ${
                    plan.popular 
                      ? 'border-primary shadow-[0_0_30px_rgba(0,255,255,0.3)]' 
                      : 'border-primary/30 hover:border-primary/50'
                  }`}
                  style={{ animationDelay: `${0.2 + idx * 0.1}s` }}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge className="bg-gradient-to-r from-primary/80 to-primary-deep/60 border-0 shadow-[0_0_15px_rgba(0,255,255,0.5)]">
                        Mais Popular
                      </Badge>
                    </div>
                  )}

                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <Icon className={`h-8 w-8 ${plan.color} drop-shadow-[0_0_10px_rgba(0,255,255,0.6)]`} />
                        <div className="absolute inset-0 bg-primary/20 rounded-full blur-lg" />
                      </div>
                      <h3 className="text-xl font-bold">{plan.name}</h3>
                    </div>

                    <div>
                      <div className="flex items-baseline gap-1">
                        <span className="text-3xl font-bold">USD$ {price.toFixed(2)}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        por {billingCycle === "monthly" ? "mês" : "mês (cobrado anualmente)"}
                      </p>
                    </div>

                    <Separator />

                    <ul className="space-y-2">
                      {plan.features.map((feature, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <Check className="h-4 w-4 text-finops mt-0.5 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <Button
                      onClick={() => handleSelectPlan(plan.name)}
                      className={`w-full glass-hover border-2 ${
                        plan.popular
                          ? 'border-primary bg-gradient-to-r from-primary/80 to-primary-deep/60 shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.5)]'
                          : 'border-primary/40 hover:border-primary/60'
                      }`}
                    >
                      Selecionar Plano
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Payment Form */}
          {showPaymentForm && selectedPlan && (
            <div className="glass-strong border-2 border-primary/30 rounded-2xl p-8 shadow-[0_0_30px_rgba(0,255,255,0.2)] animate-fade-in">
              <h2 className="text-2xl font-bold mb-6 text-primary">Finalizar Pagamento - {selectedPlan}</h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Payment Methods */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold mb-4">Método de Pagamento</h3>
                  <div className="grid grid-cols-1 gap-3">
                    {paymentMethods.map((method) => {
                      const MethodIcon = method.icon;
                      return (
                        <button
                          key={method.id}
                          onClick={() => handlePaymentMethodSelect(method.id)}
                          className={`glass glass-hover p-4 rounded-xl border-2 transition-all duration-300 text-left ${
                            selectedPayment === method.id
                              ? 'border-primary shadow-[0_0_20px_rgba(0,255,255,0.3)] scale-105'
                              : 'border-primary/30 hover:border-primary/50'
                          }`}
                        >
                          <div className="flex items-center gap-4">
                            <div className="relative">
                              <MethodIcon className={`h-8 w-8 text-${method.color}`} />
                              <div className="absolute inset-0 bg-primary/20 rounded-full blur-lg" />
                            </div>
                            <div>
                              <div className="font-semibold">{method.name}</div>
                              <div className="text-xs text-muted-foreground">{method.description}</div>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Card Form (if credit card selected) */}
                <div className="space-y-4">
                  {selectedPayment === "credit-card" && (
                    <>
                      <h3 className="text-lg font-semibold mb-4">Dados do Cartão</h3>
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="card-number">Número do Cartão</Label>
                          <Input
                            id="card-number"
                            placeholder="0000 0000 0000 0000"
                            value={cardData.number}
                            onChange={(e) => setCardData({ ...cardData, number: e.target.value })}
                            className="glass border-2 border-primary/30"
                            maxLength={19}
                          />
                        </div>
                        <div>
                          <Label htmlFor="card-name">Nome no Cartão</Label>
                          <Input
                            id="card-name"
                            placeholder="NOME COMPLETO"
                            value={cardData.name}
                            onChange={(e) => setCardData({ ...cardData, name: e.target.value.toUpperCase() })}
                            className="glass border-2 border-primary/30"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="card-expiry">Validade</Label>
                            <Input
                              id="card-expiry"
                              placeholder="MM/AA"
                              value={cardData.expiry}
                              onChange={(e) => setCardData({ ...cardData, expiry: e.target.value })}
                              className="glass border-2 border-primary/30"
                              maxLength={5}
                            />
                          </div>
                          <div>
                            <Label htmlFor="card-cvv">CVV</Label>
                            <Input
                              id="card-cvv"
                              placeholder="123"
                              type="password"
                              value={cardData.cvv}
                              onChange={(e) => setCardData({ ...cardData, cvv: e.target.value })}
                              className="glass border-2 border-primary/30"
                              maxLength={4}
                            />
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  {selectedPayment === "pix" && (
                    <div className="text-center py-8 space-y-4">
                      <div className="flex justify-center">
                        <div className="relative">
                          <QrCode className="h-32 w-32 text-finops drop-shadow-[0_0_20px_rgba(0,255,153,0.8)]" />
                          <div className="absolute inset-0 bg-finops/20 rounded-lg blur-xl" />
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        QR Code gerado ao confirmar pagamento
                      </p>
                    </div>
                  )}

                  {selectedPayment === "boleto" && (
                    <div className="text-center py-8 space-y-4">
                      <div className="flex justify-center">
                        <div className="relative">
                          <FileText className="h-32 w-32 text-dataAi drop-shadow-[0_0_20px_rgba(191,0,255,0.8)]" />
                          <div className="absolute inset-0 bg-dataAi/20 rounded-lg blur-xl" />
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Boleto gerado ao confirmar pagamento
                      </p>
                    </div>
                  )}

                  {selectedPayment === "paypal" && (
                    <div className="text-center py-8 space-y-4">
                      <div className="flex justify-center">
                        <div className="relative">
                          <Building2 className="h-32 w-32 text-secondary drop-shadow-[0_0_20px_rgba(128,128,255,0.8)]" />
                          <div className="absolute inset-0 bg-secondary/20 rounded-lg blur-xl" />
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Você será redirecionado ao PayPal
                      </p>
                    </div>
                  )}

                  <Button
                    onClick={handleSubmitPayment}
                    disabled={!selectedPayment}
                    className="w-full glass-strong border-2 border-primary bg-gradient-to-r from-primary/80 to-primary-deep/60 shadow-[0_0_20px_rgba(0,255,255,0.4)] hover:shadow-[0_0_30px_rgba(0,255,255,0.6)] hover:scale-105 transition-all duration-300"
                  >
                    Confirmar Pagamento
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Billing;
