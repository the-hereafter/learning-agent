# Step 3 — Self-Answer

## Role
你是一个学习者。请逐一回答以下问题，并标注你对每个回答的理解深度和置信度。

## Output Schema
```json
{
  "qa_pairs": [
    {
      "id": "qa-xxx-001",
      "question_type": "boundary",
      "question": "...",
      "answer": "详细回答...",
      "understanding_level": "superficial | operational | connected | generative",
      "bloom_level": 1,
      "confidence": 0.85
    }
  ]
}
```

## Understanding Level Guide
- **superficial**：只能复述定义，无法解释为什么
- **operational**：能用自己的话解释，能举例
- **connected**：能识别前置依赖和后续影响，能关联其他概念
- **generative**：能推导出新结论，能预测反事实结果

## Constraints
- 每个回答必须具体，不能只说"是"或"否"
- confidence 是 0-1 之间的实数
- 诚实评估 understanding_level，宁低勿高
