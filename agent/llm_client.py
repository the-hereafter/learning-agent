"""
LLMClient — DeepSeek API 封装。

所有 Step 通过此模块调用 LLM。
"""

import json
import os

from openai import OpenAI


class LLMClient:
    """DeepSeek API 的薄封装。"""

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY 未设置。请设置环境变量后重试。\n"
                "  export DEEPSEEK_API_KEY=sk-..."
            )

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    def call(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """发送请求，返回 LLM 文本响应。"""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def call_json(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> dict:
        """发送请求，尝试将返回解析为 JSON dict。

        如果 LLM 返回的内容被 markdown 代码块包裹，自动剥离。
        """
        raw = self.call(system_prompt, user_message, temperature=temperature, max_tokens=max_tokens)
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(raw: str) -> dict:
        text = raw.strip()

        # 剥离 ```json ... ``` 包裹
        if text.startswith("```"):
            lines = text.split("\n")
            # 去掉第一行 (```json) 和最后一行 (```)
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试找到第一个 { 和最后一个 }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
            return {"_parse_error": True, "_raw": raw[:500]}
