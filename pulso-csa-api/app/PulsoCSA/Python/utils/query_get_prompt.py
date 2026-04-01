from typing import Dict, List, Optional

from app.prompts.loader import load_prompt


class QueryGetPromptBuilder:
    """
    Prompt builder que monta o prompt a partir de arquivos .txt na pasta prompts/ID_prompts.
    Gera prompts seguros para transformação de linguagem natural em SQL.
    """

    def __init__(
        self,
        database_schema: str,
        few_shot_examples: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        self.database_schema = database_schema
        self.few_shot_examples = few_shot_examples or []

    def build(self, user_prompt: str) -> str:
        """
        Monta o prompt final a partir dos arquivos .txt e variáveis dinâmicas.
        """
        system_rules = load_prompt("ID_prompts/query_get_system_rules")
        schema_ctx = load_prompt("ID_prompts/query_get_schema_context").format(
            database_schema=self.database_schema
        )
        few_shot_block = self._build_few_shot_block()
        few_shot_section = ""
        if few_shot_block:
            few_shot_section = load_prompt("ID_prompts/query_get_few_shot_examples").format(
                few_shot_block=few_shot_block
            )
        user_request = load_prompt("ID_prompts/query_get_user_request").format(
            user_prompt=user_prompt
        )

        parts = [system_rules, schema_ctx]
        if few_shot_section:
            parts.append(few_shot_section)
        parts.append(user_request)
        return "\n\n".join(parts).strip()

    def _build_few_shot_block(self) -> str:
        """Monta o bloco de exemplos few-shot a partir da lista de exemplos."""
        if not self.few_shot_examples:
            return ""
        formatted = []
        for ex in self.few_shot_examples:
            formatted.append(
                f"USER QUESTION:\n{ex.get('question', '')}\n\nSQL QUERY:\n{ex.get('sql', '')}"
            )
        return "\n\n".join(formatted)
