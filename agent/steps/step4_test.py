"""
Step4UnderstandingTest — 覆盖检查 + 深度挑战 + 评分。
"""

import json

from agent.step_base import StepBase


class Step4UnderstandingTest(StepBase):
    name = "step4_understanding_test"

    def __init__(self, llm_client, prompt_loader):
        self.llm = llm_client
        self.prompts = prompt_loader

    def run(self, node: dict, state: "AgentState") -> None:  # noqa: F821
        qa_pairs = node.get("qa_pairs", [])
        statement = node["content"]["statement"]

        if not qa_pairs:
            node["process_state"] = "FLAGGED"
            node["understanding_test_result"] = {
                "final_understanding_depth": "superficial",
                "score_breakdown": {"coverage": 0.0, "depth": 0.0, "consistency": 0.0},
                "gaps_identified": ["No Q&A pairs generated"],
                "backtracking_recommended": True,
            }
            return

        # 4a: 覆盖检查 + 4b: 深度挑战（合并为一次调用）
        challenge_result = self._run_depth_challenge(statement, qa_pairs)

        # 4d: 评分
        score = self._score(statement, qa_pairs, challenge_result)

        # 判定
        coverage = score.get("coverage", 0)
        depth = score.get("depth", 0)

        if coverage >= 0.6 and depth >= 0.3:
            node["process_state"] = "VALIDATED"
            backtracking = False
        else:
            node["process_state"] = "FLAGGED"
            backtracking = True

        node["understanding_test_result"] = {
            "final_understanding_depth": score.get("understanding_level", "superficial"),
            "score_breakdown": {
                "coverage": coverage,
                "depth": depth,
                "consistency": score.get("consistency", 0),
            },
            "gaps_identified": score.get("gaps", []),
            "backtracking_recommended": backtracking,
        }

    def _run_depth_challenge(self, statement: str, qa_pairs: list[dict]) -> dict:
        system = self.prompts.load_raw("step4/depth_challenge")
        user = f"知识点：{statement}\n\n已有 Q&A：\n{json.dumps(qa_pairs, ensure_ascii=False, indent=2)}"

        try:
            return self.llm.call_json(system, user, temperature=0.3)
        except Exception:
            return {}

    def _score(self, statement: str, qa_pairs: list[dict], challenge_result: dict) -> dict:
        system = self.prompts.load_raw("step4/score")
        user = (
            f"知识点：{statement}\n\n"
            f"Q&A 对：\n{json.dumps(qa_pairs, ensure_ascii=False, indent=2)}\n\n"
            f"深度挑战结果：\n{json.dumps(challenge_result, ensure_ascii=False, indent=2)}"
        )

        try:
            return self.llm.call_json(system, user, temperature=0.2)
        except Exception:
            return {
                "understanding_level": "superficial",
                "coverage": 0.5,
                "depth": 0.3,
                "consistency": 0.5,
                "gaps": [],
            }
