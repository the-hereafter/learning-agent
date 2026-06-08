"""
StepBase — 统一 Step 接口。

每个 Step 模块继承 StepBase，实现 run() 方法。
"""

from abc import ABC, abstractmethod
from typing import Any


class StepBase(ABC):
    """Step 基类。

    子类只需实现：
      - name: str          — Step 名称（日志用）
      - run(input, state)  — 核心逻辑
    """

    name: str = "base"

    @abstractmethod
    def run(self, input_data: Any, state: "AgentState") -> Any:  # noqa: F821
        """执行 Step 逻辑。

        Args:
            input_data: Step 特定输入（节点 dict / 节点列表 / 文本）
            state: 全局 AgentState（可读写）

        Returns:
            Step 特定输出（节点 / 结果 dict / None）
        """
        ...
