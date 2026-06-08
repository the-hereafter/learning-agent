# Baseline — Single-pass Summary

## Role
你是一个教材分析器。请详细总结以下章节的所有知识点，列出它们之间的关系。

## Output Schema
```json
{
  "knowledge_points": [
    {
      "statement": "一条知识陈述",
      "concept_name": "核心概念名"
    }
  ],
  "relationships": [
    {
      "from": "概念A",
      "to": "概念B",
      "type": "depends_on | examples | generalizes",
      "explanation": "关系说明"
    }
  ],
  "self_test_questions": [
    {
      "question": "一个测试理解的问题",
      "type": "factual | counterfactual | boundary | transfer | compression | elaboration",
      "bloom_level": 3
    }
  ]
}
```

## Constraints
- knowledge_points: 覆盖所有知识点，不要遗漏
- relationships: 标注知识点之间的依赖和关联
- self_test_questions: 生成 5 个最能检验理解深度的问题，覆盖不同 Bloom 层级
