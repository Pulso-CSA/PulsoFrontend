import { Workflow, CloudCog, TrendingDown, Brain } from "lucide-react";

const btnBase = {
  padding: "10px 24px",
  borderRadius: 8,
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
  transition: "all 0.2s",
  border: "none",
};

const features = [
  {
    icon: Workflow,
    title: "Pulso CSA",
    desc: "Blueprint & Estrutura — gere estrutura de pastas e endpoints via linguagem natural.",
    color: "178 92% 52%",
  },
  {
    icon: CloudCog,
    title: "Cloud IaC",
    desc: "Infraestrutura como código — crie e gerencie AWS, Azure e GCP via chat.",
    color: "198 85% 48%",
  },
  {
    icon: TrendingDown,
    title: "FinOps",
    desc: "Otimização de custos — insights, recomendações e análises em linguagem natural.",
    color: "150 65% 40%",
  },
  {
    icon: Brain,
    title: "Dados & IA",
    desc: "Inteligência de dados — explore estrutura, estatísticas e modelos de IA.",
    color: "268 75% 58%",
  },
];

export default function TutorialScreen({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  return (
    <div
      className="animate-fade-in installer-pulso-bg scrollbar-thin"
      style={{
        padding: 32,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "auto",
      }}
    >
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: "hsl(var(--fg))" }}>
        Como o Pulso organiza seu trabalho
      </h2>
      <p style={{ fontSize: 14, color: "hsl(var(--muted-fg))", marginBottom: 20 }}>
        Quatro camadas integradas em um único dashboard, sempre com o mesmo visual do app principal:
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 28 }}>
        {features.map((f, i) => {
          const Icon = f.icon;
          return (
            <div
              key={i}
              className="card-pulso"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                padding: 14,
                borderRadius: 12,
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: `hsl(${f.color} / 0.2)`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Icon size={22} style={{ color: `hsl(${f.color})` }} />
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 2, color: "hsl(var(--fg))" }}>{f.title}</h3>
                <p style={{ fontSize: 12, color: "hsl(var(--muted-fg))", lineHeight: 1.45 }}>{f.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "hsl(var(--fg))" }}>
        Área de Insights
      </h3>
      <p style={{ fontSize: 13, color: "hsl(var(--muted-fg))", marginBottom: 16 }}>
        Quando nenhuma camada estiver selecionada, o Pulso mostra um painel de Insights com gráficos gerados a partir
        do uso real das camadas. Você pode criar novos gráficos por texto, reorganizar os cards, conectar análises
        relacionadas e exportar um relatório em Markdown — tudo com o mesmo estilo visual da aplicação.
      </p>
      <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginTop: "auto" }}>
        <button
          onClick={onBack}
          style={{
            ...btnBase,
            background: "hsl(var(--muted))",
            color: "hsl(var(--fg))",
            border: "1px solid hsl(var(--border))",
          }}
        >
          Voltar
        </button>
        <button
          onClick={onNext}
          className="btn-pulso"
          style={btnBase}
        >
          Instalar
        </button>
      </div>
    </div>
  );
}
