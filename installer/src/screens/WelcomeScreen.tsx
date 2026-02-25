const btnBase = {
  padding: "12px 28px",
  borderRadius: 10,
  fontWeight: 600,
  fontSize: 15,
  cursor: "pointer",
  transition: "all 0.2s",
  border: "none",
};

export default function WelcomeScreen({ onNext }: { onNext: () => void }) {
  return (
    <div
      className="animate-fade-in installer-pulso-bg"
      style={{
        padding: 40,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 100,
          height: 100,
          borderRadius: 24,
          background: "linear-gradient(135deg, hsl(178 92% 52% / 0.25), hsl(268 75% 58% / 0.25))",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 28,
          animation: "pulse-glow 2s ease-in-out infinite",
          boxShadow: "0 0 50px hsl(178 92% 52% / 0.2), 0 0 100px hsl(268 75% 58% / 0.1)",
          overflow: "hidden",
        }}
      >
        <img
          src="./App.png"
          alt="Pulso"
          style={{ width: 72, height: 72, objectFit: "contain" }}
        />
      </div>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 12, color: "hsl(var(--fg))", letterSpacing: "-0.02em" }}>
        Bem-vindo ao Pulso
      </h1>
      <p style={{ fontSize: 15, color: "hsl(var(--muted-fg))", maxWidth: 420, lineHeight: 1.65, marginBottom: 36 }}>
        Dashboard operacional inteligente com FinOps, Cloud IaC, Dados & IA. Este assistente irá guiá-lo pela instalação.
      </p>
      <button
        onClick={onNext}
        className="btn-pulso"
        style={btnBase}
        onMouseOver={(e) => {
          e.currentTarget.style.transform = "scale(1.03)";
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.transform = "scale(1)";
        }}
      >
        Começar
      </button>
    </div>
  );
}
