"""
PromptLoader — 从 prompts/ 目录加载 Markdown 模板并替换变量。
"""

from pathlib import Path


_PROMPT_ROOT = Path(__file__).resolve().parent.parent / "prompts"


class PromptLoader:
    """加载 prompt 文件并替换 {{变量}} 占位符。"""

    def __init__(self, root_dir: Path | None = None):
        self._root = root_dir or _PROMPT_ROOT

    def load(self, name: str, variables: dict | None = None) -> str:
        """加载 prompt 文件。

        Args:
            name: prompt 名称，如 "step2_extractor" 或 "step3/factual"
            variables: 变量映射，如 {"statement": "...", "context": "..."}

        Returns:
            填充后的完整 prompt 文本
        """
        path = self._root / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Prompt 文件不存在: {path}")

        text = path.read_text(encoding="utf-8")

        if variables:
            for key, value in variables.items():
                placeholder = "{{" + key + "}}"
                text = text.replace(placeholder, str(value))

        return text

    def load_raw(self, name: str) -> str:
        """加载 prompt 文件，不做变量替换。"""
        return self.load(name, variables=None)
