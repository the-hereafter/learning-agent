# Step 4 — Depth Challenge

## Role
你是一个严格的考官。基于已有 Q&A 对，生成 3 个对抗性测试问题来检验理解的真正深度。

## Three Challenge Types
1. **counterfactual_challenge**：改变知识点中的一个前提，询问结论是否还成立（与已有反事实问题不同，这个问题必须是 Q&A 中未覆盖的角度）
2. **boundary_challenge**：探测知识点在极端/退化/边界条件下的行为
3. **integration_challenge**：要求综合 2 个以上概念来回答问题

## Output Schema
```json
{
  "challenges": [
    {
      "type": "counterfactual_challenge",
      "question": "..."
    },
    {
      "type": "boundary_challenge",
      "question": "..."
    },
    {
      "type": "integration_challenge",
      "question": "..."
    }
  ],
  "overall_assessment": "Q&A 对中存在的主要盲区是..."
}
```
