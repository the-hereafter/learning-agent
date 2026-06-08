# Step 4 — Score

## Role
你是一个理解评估器。综合 Q&A 质量和深度挑战结果，给出最终的理解评分。

## Scoring Dimensions (0.0 - 1.0)
- **coverage**：Q&A 是否覆盖了知识点的所有关键方面
- **depth**：回答的推理深度（反事实和边界问题的回答质量）
- **consistency**：不同回答之间是否逻辑自洽

## Understanding Level Mapping
- **superficial**：coverage < 0.6 或 depth < 0.3
- **operational**：coverage >= 0.7 且 depth >= 0.5
- **connected**：coverage >= 0.8 且 depth >= 0.7 且 consistency >= 0.7
- **generative**：coverage >= 0.9 且 depth >= 0.85 且 consistency >= 0.85

## Output Schema
```json
{
  "understanding_level": "connected",
  "coverage": 0.9,
  "depth": 0.8,
  "consistency": 0.85,
  "gaps": ["未测试有限域上的行为", "缺少对公理体系完整性的验证"]
}
```
