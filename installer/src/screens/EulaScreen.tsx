import eulaText from "../../../PULSO TECH - EULA (Contrato de Licença de Usuário Final).docx.md?raw";

const btnBase = {
  padding: "10px 24px",
  borderRadius: 8,
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
  transition: "all 0.2s",
  border: "none",
};

export default function EulaScreen({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
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
      <h2
        style={{
          fontSize: 22,
          fontWeight: 700,
          marginBottom: 16,
          color: "hsl(var(--fg))",
        }}
      >
        Contrato de Licença (EULA)
      </h2>
      <div
        className="scrollbar-thin"
        style={{
          flex: 1,
          overflow: "auto",
          padding: 20,
          background: "hsl(var(--muted))",
          borderRadius: 12,
          border: "1px solid hsl(var(--border) / 0.5)",
          marginBottom: 24,
          fontSize: 13,
          lineHeight: 1.7,
          color: "hsl(var(--muted-fg))",
        }}
      >
        <pre
          style={{
            margin: 0,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
          }}
        >
          {eulaText}
        </pre>
      </div>
      <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
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
        <button onClick={onNext} className="btn-pulso" style={btnBase}>
          Aceito
        </button>
      </div>
    </div>
  );
}
