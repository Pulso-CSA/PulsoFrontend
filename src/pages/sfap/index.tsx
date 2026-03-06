import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, LayoutDashboard, List, Receipt } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/contexts/AuthContext";
import { useSfapAllowed } from "@/hooks/useSfapAllowed";
import { SFAPDashboard } from "./SFAPDashboard";
import { SFAPPlanos } from "./SFAPPlanos";
import { SFAPMovimentos } from "./SFAPMovimentos";

export default function SFAPPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const allowed = useSfapAllowed();

  useEffect(() => {
    if (isAuthenticated && !allowed) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, allowed, navigate]);

  if (isAuthenticated && !allowed) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1200px] mx-auto px-4 py-6 space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)} aria-label="Voltar">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              SFAP — Sistema Financeiro Administrativo Pulso
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Dashboard, planos e movimentos financeiros
            </p>
          </div>
        </div>

        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="bg-muted border border-border">
            <TabsTrigger value="dashboard" className="gap-2 data-[state=active]:bg-background data-[state=active]:text-foreground">
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="planos" className="gap-2 data-[state=active]:bg-background data-[state=active]:text-foreground">
              <List className="h-4 w-4" />
              Planos
            </TabsTrigger>
            <TabsTrigger value="movimentos" className="gap-2 data-[state=active]:bg-background data-[state=active]:text-foreground">
              <Receipt className="h-4 w-4" />
              Movimentos
            </TabsTrigger>
          </TabsList>
          <TabsContent value="dashboard" className="mt-6">
            <SFAPDashboard />
          </TabsContent>
          <TabsContent value="planos" className="mt-6">
            <SFAPPlanos />
          </TabsContent>
          <TabsContent value="movimentos" className="mt-6">
            <SFAPMovimentos />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
