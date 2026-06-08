"""
AgentState — 工作记忆 + 持久化日志。

所有 Step 之间通过 AgentState 交换数据。
每个 Step 从 state 读取输入，将输出写回 state。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


class AgentState:
    """Pipeline 的全局状态容器。

    state = {
        "run_id": str,
        "chapter": {"raw_text": str, "domain": str, "strategy_params": dict},
        "nodes": [Node, ...],
        "step5_result": {"contradictions": [...]} | None,
    }
    """

    def __init__(self, output_dir: str):
        self.run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.output_dir = Path(output_dir) / self.run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._log_path = self.output_dir / "learning_log.jsonl"

        self._data: dict[str, Any] = {
            "run_id": self.run_id,
            "chapter": {
                "raw_text": "",
                "domain": "unknown",
                "strategy_params": {
                    "question_focus": ["boundary", "counterfactual"],
                    "consistency_mode": "logical",
                },
            },
            "nodes": [],
            "step5_result": None,
        }

        self._log("init", {}, {"run_id": self.run_id})

    # ---- node helpers ----

    def add_node(self, statement: str, source_paragraph: int) -> dict:
        node = {
            "id": f"node-{len(self._data['nodes']) + 1:03d}",
            "name": "",
            "content": {
                "statement": statement,
                "source": {"paragraph": source_paragraph},
            },
            "process_state": "EXTRACTED",
            "qa_pairs": [],
            "understanding_test_result": None,
            "flagged": False,
        }
        self._data["nodes"].append(node)
        return node

    def get_nodes(self, process_state: str | None = None) -> list[dict]:
        if process_state is None:
            return self._data["nodes"]
        return [n for n in self._data["nodes"] if n["process_state"] == process_state]

    def get_validated_nodes(self) -> list[dict]:
        return [n for n in self._data["nodes"] if n["process_state"] in ("VALIDATED", "FLAGGED")]

    # ---- step result setters ----

    def set_step5_result(self, contradictions: list[dict]) -> None:
        self._data["step5_result"] = {"contradictions": contradictions}

    # ---- raw access ----

    @property
    def raw(self) -> dict:
        return self._data

    # ---- logging ----

    def log_step(self, step_name: str, input_summary: dict, output_summary: dict) -> None:
        self._log(step_name, input_summary, output_summary)

    def _log(self, step_name: str, input_summary: dict, output_summary: dict) -> None:
        entry = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "input_summary": input_summary,
            "output_summary": output_summary,
        }
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ---- final output ----

    def save_report(self) -> str:
        validated = [n for n in self._data["nodes"] if n["process_state"] == "VALIDATED"]
        flagged = [n for n in self._data["nodes"] if n["process_state"] == "FLAGGED"]

        depth_dist = {"superficial": 0, "operational": 0, "connected": 0, "generative": 0}
        for n in validated:
            if n.get("understanding_test_result"):
                d = n["understanding_test_result"].get("final_understanding_depth", "superficial")
                depth_dist[d] = depth_dist.get(d, 0) + 1

        report = {
            "run_id": self.run_id,
            "total_nodes": len(self._data["nodes"]),
            "validated": len(validated),
            "flagged": len(flagged),
            "understanding_distribution": depth_dist,
            "contradictions": self._data.get("step5_result", {}).get("contradictions", []),
            "nodes": [
                {
                    "id": n["id"],
                    "statement": n["content"]["statement"],
                    "process_state": n["process_state"],
                    "understanding_depth": (
                        n["understanding_test_result"]["final_understanding_depth"]
                        if n.get("understanding_test_result")
                        else None
                    ),
                    "qa_count": len(n.get("qa_pairs", [])),
                    "flagged": n["flagged"],
                }
                for n in self._data["nodes"]
            ],
        }

        report_path = self.output_dir / "understanding_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return str(report_path)
