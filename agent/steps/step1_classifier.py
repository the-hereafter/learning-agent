"""
Step1Classifier — 教材预读：领域分类 + 质量评估 + 策略参数选择。
"""

from agent.step_base import StepBase


class Step1Classifier(StepBase):
    name = "step1_classifier"

    # 默认策略参数（LLM 调用失败时的 fallback）
    DEFAULT_STRATEGY = {
        "primary_learning_mode": "deductive_verification",
        "question_focus": ["boundary_conditions", "counterexamples"],
        "consistency_check_mode": "logical",
    }

    def __init__(self, llm_client, prompt_loader):
        self.llm = llm_client
        self.prompts = prompt_loader

    def run(self, chapter_text: str, state: "AgentState") -> dict:  # noqa: F821
        """分析教材文本，返回分类结果并写入 state。"""
        # 只看前 3000 字做快速扫描
        preview = chapter_text[:3000]

        system = self.prompts.load_raw("step1_classifier")
        user = f"以下是教材文本的开头部分：\n\n{preview}"

        result = None
        try:
            result = self.llm.call_json(system, user, temperature=0.3)
        except Exception:
            pass

        if not result or result.get("_parse_error"):
            result = self._fallback()

        # 写入 state
        state.raw["chapter"]["domain"] = result.get("domain", "unknown")
        state.raw["chapter"]["strategy_params"] = result.get(
            "strategy_parameters", self.DEFAULT_STRATEGY
        )
        state.raw["chapter"]["textbook_quality"] = result.get("textbook_quality", {})
        state.raw["chapter"]["language"] = result.get("language", "unknown")

        return result

    def _fallback(self) -> dict:
        return {
            "domain": "unknown",
            "domain_confidence": 0.0,
            "language": "unknown",
            "textbook_quality": {},
            "strategy_parameters": dict(self.DEFAULT_STRATEGY),
        }
