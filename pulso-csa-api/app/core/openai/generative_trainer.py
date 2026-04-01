# Treinamento IA Generativa
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
from app.core.openai.openai_client import get_openai_client

#━━━━━━━━━❮Treinamento IA Generativa❯━━━━━━━━━
def refine_prompt_with_llm(prompt: str) -> str:
    """
    Usa o cliente OpenAI (singleton) para refinar prompts
    com base em boas práticas de engenharia de prompt e compliance.
    """
    client = get_openai_client()
    system = (
        "Você é um assistente especialista em governança, compliance e gestão de requisitos. "
        "Recebe um prompt e o melhora para clareza, precisão e aderência a normas (COBIT, ISO, ITIL, LGPD)."
    )
    return client.generate_text(prompt, system_prompt=system, use_fast_model=True).strip()
