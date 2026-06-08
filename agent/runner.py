"""
Runner — 主编排模块。

负责：
  Step 1: 教材预读（领域分类 + 策略参数选择）
  Step 2: 命题提取（章节级）
  Step 3: 六类问题生成 + 自答（节点级）
  Step 4: 理解验证（节点级，含 ≤2 次重试）
  Step 5: 跨节点一致性检查（章节级）
  Step 6: 知识图构建（章节级）
"""

import json
import sys
from pathlib import Path

from agent.llm_client import LLMClient
from agent.prompt_loader import PromptLoader
from agent.state import AgentState
from agent.steps.step1_classifier import Step1Classifier
from agent.steps.step2_extractor import Step2Extractor
from agent.steps.step3_qa import Step3QAGenerator
from agent.steps.step4_test import Step4UnderstandingTest
from agent.steps.step5_consistency import Step5ConsistencyChecker
from agent.steps.step6_graph import Step6GraphBuilder


class Runner:
    """Phase 1 MVP 主编排器。"""

    MAX_RETRIES = 3  # 每个节点最多尝试 3 次 Step3→4

    def __init__(self, output_base: str = "output"):
        self.output_base = output_base
        self.llm = LLMClient()
        self.prompts = PromptLoader()
        self.state: AgentState | None = None

    def run(self, chapter_path: str) -> str:
        """执行完整 Pipeline。

        Returns:
            understanding_report.json 的路径
        """
        # 初始化
        chapter_text = Path(chapter_path).read_text(encoding="utf-8")
        self.state = AgentState(self.output_base)
        self.state.raw["chapter"]["raw_text"] = chapter_text

        print(f"=== Learning Agent MVP v0.1 ===")
        print(f"Run ID: {self.state.run_id}")
        print(f"Chapter: {chapter_path} ({len(chapter_text)} chars)\n")

        # Step 1: 教材预读
        self._run_step1(chapter_text)

        # Step 2: 命题提取
        self._run_step2(chapter_text)

        # Step 3 → 4: 逐节点 Q&A + 理解验证（含重试）
        self._run_step3_4_loop()

        # Step 5: 跨节点一致性检查
        self._run_step5()

        # Step 6: 知识图构建
        self._run_step6()

        # 输出报告
        report_path = self.state.save_report()
        self._print_summary()

        print(f"\n报告: {report_path}")
        print(f"日志: {self.state.output_dir / 'learning_log.jsonl'}")
        return report_path

    # ------------------------------------------------------------------
    # Step 1
    # ------------------------------------------------------------------
    def _run_step1(self, chapter_text: str) -> None:
        print("[Step 1] 教材预读...")
        step1 = Step1Classifier(self.llm, self.prompts)
        result = step1.run(chapter_text, self.state)

        domain = result.get("domain", "unknown")
        conf = result.get("domain_confidence", 0)
        mode = result.get("strategy_parameters", {}).get("primary_learning_mode", "?")
        quality = result.get("textbook_quality", {})
        expl = quality.get("explicitness", "?")
        flow = quality.get("logical_flow", "?")

        self.state.log_step(
            "step1_classifier",
            {"chapter_chars": len(chapter_text), "preview_chars": min(3000, len(chapter_text))},
            {"domain": domain, "confidence": conf, "learning_mode": mode,
             "explicitness": expl, "logical_flow": flow},
        )
        print(f"  领域: {domain} (confidence={conf})")
        print(f"  学习模式: {mode}  清晰度: {expl}/5  逻辑流: {flow}/5\n")

    # ------------------------------------------------------------------
    # Step 2
    # ------------------------------------------------------------------
    def _run_step2(self, chapter_text: str) -> None:
        print("[Step 2] 提取命题...")
        step2 = Step2Extractor(self.llm, self.prompts)
        propositions = step2.run(chapter_text, self.state)

        for i, prop in enumerate(propositions):
            node = self.state.add_node(
                statement=prop["statement"],
                source_paragraph=prop.get("source_paragraph", i + 1),
            )
            node["name"] = prop.get("name", node["id"])

        self.state.log_step(
            "step2_extractor",
            {"chapter_chars": len(chapter_text)},
            {"proposition_count": len(propositions)},
        )
        print(f"  提取到 {len(propositions)} 个命题\n")

    # ------------------------------------------------------------------
    # Step 3 → 4 loop
    # ------------------------------------------------------------------
    def _run_step3_4_loop(self) -> None:
        nodes = self.state.get_nodes("EXTRACTED")
        total = len(nodes)
        print(f"[Step 3→4] 逐节点生成 Q&A 并验证 ({total} 个节点)...")

        step3 = Step3QAGenerator(self.llm, self.prompts)
        step4 = Step4UnderstandingTest(self.llm, self.prompts)

        for idx, node in enumerate(nodes):
            print(f"  [{idx + 1}/{total}] {node['id']} ...", end=" ", flush=True)

            for attempt in range(1, self.MAX_RETRIES + 1):
                # Step 3
                step3.run(node, self.state)

                # Step 4
                step4.run(node, self.state)

                if node["process_state"] == "VALIDATED":
                    depth = node["understanding_test_result"]["final_understanding_depth"]
                    print(f"✓ (attempt {attempt}, {depth})")
                    break
                else:
                    if attempt < self.MAX_RETRIES:
                        print(f"↻", end=" ", flush=True)
                    else:
                        print(f"✗ flagged after {attempt} attempts")
                        node["flagged"] = True

            self.state.log_step(
                f"step3_4_node_{node['id']}",
                {"node_id": node["id"], "statement": node["content"]["statement"][:80]},
                {
                    "process_state": node["process_state"],
                    "qa_count": len(node.get("qa_pairs", [])),
                    "understanding_depth": (
                        node["understanding_test_result"]["final_understanding_depth"]
                        if node.get("understanding_test_result")
                        else None
                    ),
                },
            )

        validated = len(self.state.get_nodes("VALIDATED"))
        flagged = len(self.state.get_nodes("FLAGGED"))
        print(f"  完成: {validated} 通过, {flagged} 标记\n")

    # ------------------------------------------------------------------
    # Step 5
    # ------------------------------------------------------------------
    def _run_step5(self) -> None:
        print("[Step 5] 跨节点一致性检查...")
        step5 = Step5ConsistencyChecker(self.llm, self.prompts)
        valid_nodes = self.state.get_validated_nodes()

        if len(valid_nodes) < 2:
            print("  节点不足 2 个，跳过\n")
            self.state.set_step5_result([])
            return

        contradictions = step5.run(valid_nodes, self.state)
        self.state.log_step(
            "step5_consistency",
            {"node_count": len(valid_nodes)},
            {"contradiction_count": len(contradictions)},
        )
        print(f"  检测到 {len(contradictions)} 个矛盾\n")

    # ------------------------------------------------------------------
    # Step 6
    # ------------------------------------------------------------------
    def _run_step6(self) -> None:
        print("[Step 6] 构建知识图...")
        step6 = Step6GraphBuilder(self.llm, self.prompts)
        graph = step6.run(self.state.raw["nodes"], self.state)

        # 保存知识图
        graph_path = self.state.output_dir / "knowledge_graph.json"
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False)

        self.state.log_step(
            "step6_graph",
            {"node_count": len(graph["nodes"])},
            {"edge_count": len(graph["edges"])},
        )
        print(f"  节点: {len(graph['nodes'])}  边: {len(graph['edges'])}\n")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def _print_summary(self) -> None:
        nodes = self.state.raw["nodes"]
        validated = [n for n in nodes if n["process_state"] == "VALIDATED"]
        flagged = [n for n in nodes if n["process_state"] == "FLAGGED"]

        depths = {}
        for n in validated:
            if n.get("understanding_test_result"):
                d = n["understanding_test_result"]["final_understanding_depth"]
                depths[d] = depths.get(d, 0) + 1

        print("=== Summary ===")
        print(f"  总节点:   {len(nodes)}")
        print(f"  已验证:   {len(validated)}")
        print(f"  已标记:   {len(flagged)}")
        if depths:
            print(f"  理解分布: {depths}")
