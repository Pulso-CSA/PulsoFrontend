import { Folder, Wifi, Settings, Shield } from "lucide-react";

const btnBase = {
  padding: "10px 24px",
  borderRadius: 8,
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
  transition: "all 0.2s",
  border: "none",
};

const permissions = [
  {
    icon: Folder,
    title: "Acesso a arquivos",
    desc: "Leitura e gravação no diretório de instalação e dados do aplicativo.",
  },
  {
    icon: Wifi,
    title: "Acesso à rede",
    desc: "Conexão com servidores para sincronização e atualizações.",
  },
  {
    icon: Settings,
    title: "Configurações do sistema",
    desc: "Registro de atalhos e associações de arquivo (opcional).",
  },
  {
    icon: Shield,
    title: "Execução em segundo plano",
    desc: "Notificações e verificações de atualização automática.",
  },
];

export default function PermissionsScreen({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  return (
    <div
      className="animate-fade-in installer-pulso-bg"
      style={{
        padding: 32,
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: `hsl(var(--fg))` }}>
        Permissões necessárias
      </h2>
      <p style={{ fontSize: 14, color: `hsl(var(--muted-fg))`, marginBottom: 24 }}>
        O Pulso precisa das seguintes permissões para funcionar corretamente:
      </p>
      <div
        style={{
          flex: 1,
          overflow: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          marginBottom: 24,
        }}
      >
        {permissions.map((p, i) => {
          const Icon = p.icon;
          return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 16,
              padding: 16,
              background: `hsl(var(--card))`,
              borderRadius: 12,
              border: `1px solid hsl(var(--border) / 0.5)`,
              transition: "transform 0.2s, box-shadow 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateX(4px)";
              e.currentTarget.style.boxShadow = "0 4px 20px hsl(0 0% 0% / 0.15)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateX(0)";
              e.currentTarget.style.boxShadow = "none";
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 10,
                background: `hsl(var(--primary) / 0.15)`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <Icon size={22} style={{ color: `hsl(var(--primary))` }} />
            </div>
            <div>
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4, color: `hsl(var(--fg))` }}>{p.title}</h3>
              <p style={{ fontSize: 13, color: `hsl(var(--muted-fg))`, lineHeight: 1.5 }}>{p.desc}</p>
            </div>
          </div>
          );
        })}
      </div>
      <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
        <button
          onClick={onBack}
          style={{
            ...btnBase,
            background: `hsl(var(--muted))`,
            color: `hsl(var(--fg))`,
            border: `1px solid hsl(var(--border))`,
          }}
        >
          Voltar
        </button>
        <button onClick={onNext} className="btn-pulso" style={btnBase}>
          Continuar
        </button>
      </div>
    </div>
  );
}
