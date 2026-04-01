#━━━━━━━━━❮Relatório PDF – Partes relevantes do chat + marca d'água Pulso❯━━━━━━━
"""
Gera PDF com trechos relevantes do histórico de chat por área.
Marca d'água: logo Pulso (PULSO_LOGO_PATH) ou texto "PULSO".
"""
import os
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any, Optional

# service_id usado no chat_history para cada área
REPORT_SERVICE_IDS = {
    "pulsocsa": "codigo",
    "cloud-iac": "infraestrutura",
    "finops": "finops",
    "inteligencia-dados": "id",
}

REPORT_TITLES = {
    "pulsocsa": "Relatório PulsoCSA – Criação e Correção de Código",
    "cloud-iac": "Relatório Cloud IAC – Infraestrutura",
    "finops": "Relatório FinOps – Custos e Otimização",
    "inteligencia-dados": "Relatório Inteligência de Dados",
}


def _relevant_excerpts(messages: List[Dict[str, Any]], max_messages: int = 50) -> List[str]:
    """Extrai trechos relevantes: últimas mensagens usuário + assistente (resumidas se muito longas)."""
    lines: List[str] = []
    for i, doc in enumerate(reversed(messages[: max_messages * 2])):
        if i >= max_messages * 2:
            break
        user = (doc.get("mensagem_user") or "").strip()
        assistant = (doc.get("mensagem_assistant") or "").strip()
        ts = doc.get("timestamp", "")
        if hasattr(ts, "strftime"):
            ts = ts.strftime("%Y-%m-%d %H:%M")
        else:
            ts = str(ts)[:19] if ts else ""
        if user:
            excerpt = user[:2000] + ("..." if len(user) > 2000 else "")
            lines.append(f"[{ts}] Usuário: {excerpt}")
        if assistant:
            excerpt = assistant[:3000] + ("..." if len(assistant) > 3000 else "")
            lines.append(f"[{ts}] Assistente: {excerpt}")
        if user or assistant:
            lines.append("")
    return lines[: 80 * 2]


def _add_watermark(canvas, width: float, height: float, logo_path: Optional[str] = None) -> None:
    """Adiciona marca d'água central (logo ou texto PULSO)."""
    c = canvas
    c.saveState()
    c.setFillColorRGB(0.85, 0.85, 0.88)
    c.setFont("Helvetica-Bold", 48)
    c.translate(width / 2, height / 2)
    c.rotate(45)
    if logo_path and os.path.isfile(logo_path):
        try:
            from reportlab.lib.utils import ImageReader
            img = ImageReader(logo_path)
            iw, ih = img.getSize()
            scale = min(150 / max(iw, 1), 150 / max(ih, 1))
            c.drawImage(logo_path, -iw * scale / 2, -ih * scale / 2, width=iw * scale, height=ih * scale)
        except Exception:
            c.drawString(-70, -12, "PULSO")
    else:
        c.drawString(-70, -12, "PULSO")
    c.restoreState()


def build_report_pdf(area: str, messages: List[Dict[str, Any]]) -> bytes:
    """
    Gera PDF do relatório da área com mensagens relevantes e marca d'água Pulso.
    area: pulsocsa | cloud-iac | finops | inteligencia-dados
    messages: lista de docs do chat_history (mensagem_user, mensagem_assistant, timestamp).
    Retorna bytes do PDF.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted

    title = REPORT_TITLES.get(area, f"Relatório {area}")
    lines = _relevant_excerpts(messages)

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        name="ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Gerado em: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))
    if not lines:
        story.append(Paragraph("Nenhuma conversa encontrada para esta área no período.", body_style))
    else:
        text_block = "\n".join(lines)
        story.append(Preformatted(text_block, body_style))

    logo_path = os.getenv("PULSO_LOGO_PATH")
    if not logo_path:
        # api/app/services/report_services -> api/app/assets
        logo_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "pulso_logo.png"))
    if logo_path and not os.path.isfile(logo_path):
        logo_path = None

    def _watermark_cb(canvas, _doc):
        _add_watermark(canvas, A4[0], A4[1], logo_path)

    doc.build(story, onFirstPage=_watermark_cb, onLaterPages=_watermark_cb)
    return buf.getvalue()
