"""
Step3QAGenerator — 六类问题生成 + 质量过滤 + 自答。
"""

import json

from agent.step_base import StepBase


_QUESTION_TYPES = [
    "factual",
    "counterfactual",
    "boundary",
    "transfer",
    "compression",
    "elaboration",
]


class Step3QAGenerator(StepBase):
    name = "step3_qa_generator"

    def __init__(self, llm_client, prompt_loader):
        self.llm = llm_client
        self.prompts = prompt_loader

    def run(self, node: dict, state: "AgentState") -> None:  # noqa: F821
        statement = node["content"]["statement"]

        # 1. 批量生成六类问题
        questions = self._generate_questions(statement)

        # 2. 质量过滤
        filtered = self._filter_questions(statement, questions)

        # 3. 批量自答
        qa_pairs = self._answer_questions(statement, filtered)

        node["qa_pairs"] = qa_pairs
        node["process_state"] = "QA_GENERATED"

    # ------------------------------------------------------------------
    def _generate_questions(self, statement: str) -> list[dict]:
        system = self.prompts.load("step3/all_questions", {"statement": statement})
        user = f"请基于以下知识点，生成六类问题（factual, counterfactual, boundary, transfer, compression, elaboration），每类 1 个。\n\n知识点：{statement}"

        try:
            result = self.llm.call_json(system, user, temperature=0.4)
            return result.get("questions", [])
        except Exception:
            return []

    def _filter_questions(self, statement: str, questions: list[dict]) -> list[dict]:
        if not questions:
            return []

        system = self.prompts.load_raw("step3/filter")
        user = f"知识点：{statement}\n\n候选问题：\n{json.dumps(questions, ensure_ascii=False, indent=2)}"

        try:
            result = self.llm.call_json(system, user, temperature=0.2)
            kept_indices = result.get("keep_indices", [])
            if kept_indices:
                return [q for i, q in enumerate(questions) if i in kept_indices]
        except Exception:
            pass
        return questions

    def _answer_questions(self, statement: str, questions: list[dict]) -> list[dict]:
        if not questions:
            return []

        system = self.prompts.load_raw("step3/answer")
        user = f"知识点：{statement}\n\n问题列表：\n{json.dumps(questions, ensure_ascii=False, indent=2)}"

        try:
            result = self.llm.call_json(system, user, temperature=0.3)
            return result.get("qa_pairs", [])
        except Exception:
            # 降级：只填 question，answer 为空
            return [
                {
                    "id": f"qa-{statement[:10]}-{i:03d}",
                    "question_type": q.get("type", "factual"),
                    "question": q.get("question", ""),
                    "answer": "",
                    "understanding_level": "superficial",
                    "bloom_level": 1,
                    "confidence": 0.0,
                }
                for i, q in enumerate(questions)
            ]
