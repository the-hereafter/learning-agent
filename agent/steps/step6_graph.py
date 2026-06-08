"""
Step6GraphBuilder — 命题 + 关系 → 知识图节点 + 边。
"""

import json
from agent.step_base import StepBase


class Step6GraphBuilder(StepBase):
    name = "step6_graph_builder"

    def __init__(self, llm_client, prompt_loader):
        self.llm = llm_client
        self.prompts = prompt_loader

    def run(self, nodes: list[dict], state: "AgentState") -> dict:  # noqa: F821
        """从已验证节点构建知识图。

        Returns:
            {"nodes": [...], "edges": [...]}
        """
        valid_nodes = [n for n in nodes if n["process_state"] in ("VALIDATED", "FLAGGED")]
        if len(valid_nodes) < 2:
            return {"nodes": valid_nodes, "edges": []}

        # 构建节点摘要供 LLM 分析
        summaries = [
            {
                "id": n["id"],
                "statement": n["content"]["statement"],
                "depth": (
                    n["understanding_test_result"]["final_understanding_depth"]
                    if n.get("understanding_test_result")
                    else "unknown"
                ),
            }
            for n in valid_nodes
        ]

        system = self.prompts.load_raw("step6_graph")
        user = f"节点列表：\n{json.dumps(summaries, ensure_ascii=False, indent=2)}"

        try:
            result = self.llm.call_json(system, user, temperature=0.2)
        except Exception:
            result = {}

        edges = result.get("edges", [])

        # 标注节点在图中
        for n in valid_nodes:
            if n["process_state"] == "VALIDATED":
                n["process_state"] = "INTEGRATED"

        graph = {
            "nodes": [
                {
                    "id": n["id"],
                    "statement": n["content"]["statement"],
                    "depth": (
                        n["understanding_test_result"]["final_understanding_depth"]
                        if n.get("understanding_test_result")
                        else "unknown"
                    ),
                    "flagged": n.get("flagged", False),
                }
                for n in valid_nodes
            ],
            "edges": edges,
        }

        state.raw["graph"] = graph
        return graph
