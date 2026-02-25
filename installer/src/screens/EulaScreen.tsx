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
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 16, color: "hsl(var(--fg))" }}>
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
        <p style={{ marginBottom: 12 }}>
          <strong>EXEMPLO DE EULA — Substitua pelo texto real</strong>
        </p>
        <p style={{ marginBottom: 12 }}>
          Este Acordo de Licença de Usuário Final (EULA) é um contrato legal entre você e a Pulso Tech
          (Licenciador) relativo ao software Pulso (Software).
        </p>
        <p style={{ marginBottom: 12 }}>
          <strong>1. Concessão de Licença.</strong> O Licenciador concede a você uma licença limitada, não exclusiva
          e intransferível para usar o Software, sujeita aos termos deste EULA.
        </p>
        <p style={{ marginBottom: 12 }}>
          <strong>2. Restrições.</strong> Você concorda em não copiar, modificar, distribuir ou fazer engenharia reversa
          do Software sem autorização prévia por escrito.
        </p>
        <p style={{ marginBottom: 12 }}>
          <strong>3. Propriedade Intelectual.</strong> O Software é protegido por leis de propriedade intelectual.
          Todos os direitos não expressamente concedidos são reservados ao Licenciador.
        </p>
        <p style={{ marginBottom: 12 }}>
          <strong>4. Limitação de Responsabilidade.</strong> O Software é fornecido como está. O Licenciador não
          se responsabiliza por danos indiretos, incidentais ou consequenciais.
        </p>
        <p>
          Ao clicar em Aceito, você concorda com os termos deste contrato. Caso não concorde, cancele a instalação.
        </p>
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
