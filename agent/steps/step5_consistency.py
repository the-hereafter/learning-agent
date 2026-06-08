"""
Step5ConsistencyChecker — 跨节点逻辑矛盾检测。
"""

import json

from agent.step_base import StepBase


class Step5ConsistencyChecker(StepBase):
    name = "step5_consistency"

    def __init__(self, llm_client, prompt_loader):
        self.llm = llm_client
        self.prompts = prompt_loader

    def run(self, nodes: list[dict], state: "AgentState") -> list[dict]:  # noqa: F821
        if len(nodes) < 2:
            return []

        # 构建节点摘要
        summaries = [
            {
                "id": n["id"],
                "statement": n["content"]["statement"],
                "understanding_depth": (
                    n["understanding_test_result"]["final_understanding_depth"]
                    if n.get("understanding_test_result")
                    else "unknown"
                ),
            }
            for n in nodes
        ]

        system = self.prompts.load_raw("step5_consistency")
        user = f"节点列表：\n{json.dumps(summaries, ensure_ascii=False, indent=2)}"

        try:
            result = self.llm.call_json(system, user, temperature=0.2)
            contradictions = result.get("contradictions", [])
        except Exception:
            contradictions = []

        state.set_step5_result(contradictions)
        return contradictions
