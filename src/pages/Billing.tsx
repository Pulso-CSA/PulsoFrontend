import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowLeft, 
  Check, 
  Zap,
  Crown,
  Star,
  Sparkles,
  ExternalLink
} from "lucide-react";
import DashboardHeader from "@/components/dashboard/DashboardHeader";

// Stripe Payment Links para planos mensais
const stripePaymentLinks = {
  basic: {
    withoutKey: "https://buy.stripe.com/test_bJe00jdAl89e4fFcim8Zq08", // $29.99
    withKey: "https://buy.stripe.com/test_fZu6oHao989e13tequ8Zq09"     // $24.99
  },
  plus: {
    withoutKey: "https://buy.stripe.com/test_eVq14n67T6164fF96a8Zq0a", // $44.77
    withKey: "https://buy.stripe.com/test_cNibJ153P1KQ3bBdmq8Zq0b"     // $34.77
  },
  pro: {
    withoutKey: "https://buy.stripe.com/test_3cI28rgMx3SY27xgyC8Zq0c", // $59.77
    withKey: "https://buy.stripe.com/test_fZu8wPeEp89ecMb3LQ8Zq0d"     // $49.77
  },
  elite: {
    withoutKey: "https://buy.stripe.com/test_dRmcN5bsdcpu6nN4PU8Zq0e", // $69.77
    withKey: "https://buy.stripe.com/test_bJe28r53PblqfYn0zE8Zq0f"     // $57.77
  }
};

const plans = [
  {
    id: "basic",
    name: "Basic",
    priceMonthly: 29.99,
    priceYearly: 305.05,
    priceMonthlyWithAPI: 24.99,
    priceYearlyWithAPI: 254.90,
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
    id: "plus",
    name: "Plus",
    priceMonthly: 44.77,
    priceYearly: 456.65,
    priceMonthlyWithAPI: 34.77,
    priceYearlyWithAPI: 354.65,
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
    id: "pro",
    name: "Pro",
    priceMonthly: 59.77,
    priceYearly: 609.65,
    priceMonthlyWithAPI: 49.77,
    priceYearlyWithAPI: 507.65,
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
    id: "elite",
    name: "Elite",
    priceMonthly: 69.77,
    priceYearly: 711.65,
    priceMonthlyWithAPI: 57.77,
    priceYearlyWithAPI: 588.65,
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

const Billing = () => {
  const navigate = useNavigate();
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [hasOpenAIKey, setHasOpenAIKey] = useState(false);

  const handleSelectPlan = (planId: string) => {
    if (billingCycle === "yearly") {
      // Planos anuais ainda não disponíveis no Stripe
      alert("Planos anuais serão disponibilizados em breve. Por favor, selecione o plano mensal.");
      return;
    }

    const planLinks = stripePaymentLinks[planId as keyof typeof stripePaymentLinks];
    if (planLinks) {
      const link = hasOpenAIKey ? planLinks.withKey : planLinks.withoutKey;
      window.open(link, "_blank");
    }
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
          <div className="flex flex-col items-center gap-4 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="glass-strong rounded-full p-1 inline-flex gap-1 border-2 border-primary/30">
              <Button
                variant={billingCycle === "monthly" ? "default" : "ghost"}
                size="sm"
                onClick={() => setBillingCycle("monthly")}
                className={billingCycle === "monthly" 
                  ? "rounded-full bg-gradient-to-r from-primary/80 to-primary-deep/60 shadow-[0_0_20px_rgba(0,255,255,0.4)] transition-all duration-200" 
                  : "rounded-full transition-all duration-200"}
              >
                Mensal
              </Button>
              <Button
                variant={billingCycle === "yearly" ? "default" : "ghost"}
                size="sm"
                onClick={() => setBillingCycle("yearly")}
                className={billingCycle === "yearly" 
                  ? "rounded-full bg-gradient-to-r from-finops/80 to-success/60 shadow-[0_0_20px_rgba(0,255,153,0.4)] transition-all duration-200" 
                  : "rounded-full transition-all duration-200"}
              >
                Anual
                <Badge variant="secondary" className="ml-2 text-xs">-15%</Badge>
              </Button>
            </div>

            {/* OpenAI API Key Toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setHasOpenAIKey(!hasOpenAIKey)}
              className={`glass glass-hover border-2 gap-2 transition-all duration-300 ${
                hasOpenAIKey 
                  ? 'border-dataAi bg-gradient-to-r from-dataAi/30 to-secondary/30 shadow-[0_0_20px_rgba(191,0,255,0.5)] scale-105' 
                  : 'border-primary/30 hover:border-dataAi/50 hover:scale-105'
              }`}
            >
              <Sparkles className={`h-5 w-5 transition-all duration-300 ${hasOpenAIKey ? 'text-dataAi animate-pulse' : 'text-muted-foreground'}`} />
              <span className="font-semibold">
                {hasOpenAIKey ? '✓ Desconto OpenAI Ativo (15%)' : 'Tenho Chave API OpenAI'}
              </span>
            </Button>

            {billingCycle === "yearly" && (
              <p className="text-sm text-muted-foreground text-center animate-fade-in">
                ⚠️ Planos anuais serão disponibilizados em breve. Atualmente apenas planos mensais estão disponíveis.
              </p>
            )}
          </div>

          {/* Plans Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan, idx) => {
              const Icon = plan.icon;
              const price = billingCycle === "monthly" 
                ? (hasOpenAIKey ? plan.priceMonthlyWithAPI : plan.priceMonthly)
                : (hasOpenAIKey ? plan.priceYearlyWithAPI : plan.priceYearly);
              
              return (
                <Card
                  key={plan.name}
                  className={`relative glass-strong p-6 border-2 hover:scale-105 transition-all duration-200 animate-fade-in ${
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
                        <span className={`text-3xl font-bold transition-all duration-500 ${hasOpenAIKey ? 'animate-fade-in' : ''}`}>
                          USD$ {price.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {billingCycle === "monthly" ? "por mês" : "por ano"}
                      </p>
                      {(billingCycle === "yearly" || hasOpenAIKey) && (
                        <p className="text-xs text-finops font-semibold animate-fade-in">
                          15% de desconto {hasOpenAIKey && '(OpenAI API)'}
                        </p>
                      )}
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
                      onClick={() => handleSelectPlan(plan.id)}
                      className={`w-full glass-hover border-2 transition-all duration-200 gap-2 ${
                        plan.popular
                          ? 'border-primary bg-gradient-to-r from-primary/80 to-primary-deep/60 shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.5)]'
                          : 'border-primary/40 hover:border-primary/60'
                      }`}
                      disabled={billingCycle === "yearly"}
                    >
                      {billingCycle === "yearly" ? "Em Breve" : (
                        <>
                          Assinar Plano
                          <ExternalLink className="h-4 w-4" />
                        </>
                      )}
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Stripe Badge */}
          <div className="text-center animate-fade-in" style={{ animationDelay: '0.6s' }}>
            <p className="text-xs text-muted-foreground">
              Pagamentos processados de forma segura via{" "}
              <span className="font-semibold text-primary">Stripe</span>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Billing;
