"""
Step2Extractor — 从教材原文提取命题列表。
"""

from agent.step_base import StepBase


class Step2Extractor(StepBase):
    name = "step2_extractor"

    def __init__(self, llm_client, prompt_loader):
        self.llm = llm_client
        self.prompts = prompt_loader

    def run(self, chapter_text: str, state: "AgentState") -> list[dict]:  # noqa: F821
        system = self.prompts.load_raw("step2_extractor")
        user = f"以下是教材章节原文：\n\n{chapter_text}"

        try:
            result = self.llm.call_json(system, user, temperature=0.2)
        except Exception:
            result = {}

        propositions = result.get("propositions", [])
        if not propositions:
            return self._fallback(chapter_text)

        return [
            {
                "statement": p.get("statement", ""),
                "source_paragraph": p.get("source_paragraph", i + 1),
                "name": p.get("concept_name", ""),
            }
            for i, p in enumerate(propositions)
        ]

    def _fallback(self, text: str) -> list[dict]:
        """LLM 调用失败时的降级：按段落分割作为命题。"""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return [
            {
                "statement": p[:200],
                "source_paragraph": i + 1,
                "name": "",
            }
            for i, p in enumerate(paragraphs)
        ]
