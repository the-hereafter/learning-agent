# Learning Agent — 项目启动文档

> 版本：v1.1
> 状态：Phase 1 启动
> 最后更新：2026-06-10
> 本版变更：Step 3 六类问题体系 + Step 4 Understanding Test 新增

---

## 目录

1. [项目定义](#1-项目定义)
2. [核心理念](#2-核心理念)
3. [研究假设](#3-研究假设)
4. [架构设计](#4-架构设计)
5. [知识表示](#5-知识表示)
6. [认知处理 Pipeline](#6-认知处理-pipeline)
   - 6.2.3 [Step 3: Self-Q&A Generator（六类问题体系）](#step-3-self-qa-generator六类问题体系)
   - 6.2.4 [Step 4: Understanding Test（理解验证关卡）](#step-4-understanding-test理解验证关卡)
7. [评估体系](#7-评估体系)
8. [分阶段路线图](#8-分阶段路线图)
9. [Phase 1 MVP](#9-phase-1-mvp)
10. [设计原则与约束](#10-设计原则与约束)
11. [已知风险与开放问题](#11-已知风险与开放问题)
12. [附录：关键概念定义](#12-附录关键概念定义)

---

## 1. 项目定义

### 1.1 项目名称

Learning Agent

### 1.2 一句话定位

探索"学习是如何发生的"，并构建一个能真正形成理解的 AI Agent。

### 1.3 与现有 AI 产品的本质区别

| 现有产品 | Learning Agent |
|---------|---------------|
| 提供知识 | 形成理解 |
| 回答用户问题 | 自己问自己问题 |
| 检索 + 生成 | 认知处理 + 迭代修正 |
| 产物是一次性回答 | 产物是可演化的知识结构 + 完整学习过程日志 |
| 不知道用户为什么不会 | 建模困惑、断层、误解 |

### 1.4 项目目标（分阶段）

- **Phase 1（当前）**：Agent 如何从教材中形成自己的理解（知识层）
- **Phase 2（中期）**：Agent 如何将知识转化为技能（技能层）
- **Phase 3（远期）**：Agent 如何形成可迁移的认知模型（认知模型层）

---

## 2. 核心理念

### 2.1 基本信念

```
知识 ≠ 理解 ≠ 掌握 ≠ 技能 ≠ 创新
```

但这些层次**不是线性递进关系**。它们相互强化：

- 技能练习会反向加深理解
- 创新往往来自跨领域类比迁移
- 理解深度的标志是能识别"自己不理解的边界"

### 2.2 学习是什么（本项目的操作化定义）

**学习 = 可观测的认知状态变化**

具体表现为：

1. **知识覆盖度提升**：已知命题数量增加
2. **理解深度递进**：从能复述 → 能解释 → 能关联 → 能推导
3. **困惑的发现与解决**：从"不知道自己不知道"到"精确知道困惑在哪"
4. **知识结构的重组**：新信息触发旧理解的修正（回溯更新）
5. **问题质量提升**：从问"是什么"到问"为什么"到问"什么情况下不成立"

### 2.3 三个核心问题

1. **认知深度问题**：多轮认知处理是否比单次处理产生更高质量的理解？
2. **过程可观测性问题**：学习过程的中间状态能否被精确建模和记录？
3. **知识演化问题**：当新信息与旧理解冲突时，如何触发和追踪知识的修正？

---

## 3. 研究假设

### 3.1 核心假设（H1）

> **多轮认知处理假设**：在自问自答 + 一致性检测 + 困惑建模的多轮处理后，Agent 产出的知识图在覆盖率、深层关系识别率和问题质量上**显著优于**单次摘要 baseline。

### 3.2 辅助假设

| 编号 | 假设 | 验证时机 |
|------|------|---------|
| H2 | 困惑的类型化建模（术语/逻辑/因果/整合/边界）比二值"理解/不理解"提供更丰富的学习状态信息 | Phase 1 |
| H3 | 反事实自问比费曼式复述产生更深层的理解 | Phase 1 |
| H4 | 当新章节与旧理解冲突时，回溯更新能提升旧节点的准确性 | Phase 1 后期 |
| H5 | 不同知识领域需要不同的学习策略参数 | Phase 2 |
| H6 | 技能练习能反向深化知识层的理解 | Phase 2 |
| H7 | 跨领域类比迁移需要独立的认知模型层 | Phase 3 |

### 3.3 可证伪性

每个假设都附带**失败条件**：

- H1 失败条件：Agent 在任何评估维度上未能超越 single-pass baseline
- H3 失败条件：反事实自问产出的问题被人工评定为"深层"的比例 ≤ 费曼式复述的问题
- H4 失败条件：更新后的节点人工评分不高于更新前

**如果 H1 被证伪，项目方向需要根本性反思。**

---

## 4. 架构设计

### 4.1 三层分离架构

```
┌──────────────────────────────────────────┐
│          Cognitive Model Layer           │  ← Phase 3（远期）
│     类比映射 + 因果模型 + 反事实推理       │
│                                          │
│              ↕ Interface: "为什么"         │
│                                          │
├──────────────────────────────────────────┤
│             Skill Layer                  │  ← Phase 2（中期）
│     条件-动作规则 + 练习循环 + 反馈信号     │
│                                          │
│              ↕ Interface: "怎么做"         │
│                                          │
├──────────────────────────────────────────┤
│           Knowledge Layer                │  ← Phase 1（当前）
│     带状态知识图 + 学习过程日志            │
│                                          │
└──────────────────────────────────────────┘
```

### 4.2 层间关系

- 三层**不是**线性递进——上层可以反哺下层
- 每层有独立的表示形式、时间尺度和更新机制
- **Phase 1 只实现 Knowledge Layer**，但 schema 预留上层接口

### 4.3 层间接口（预留，当前不实现）

```
Knowledge → Skill:
  ActionableNode { concept, conditions[], procedure[] }

Skill → Cognitive Model:
  SkillPattern { skills[], common_structure }
```

---

## 5. 知识表示

### 5.1 核心表示：带状态知识图（Stateful Knowledge Graph）

### 5.2 节点 Schema

```json
{
  "id": "node-042",
  "type": "concept | claim | procedure | example | misconception",

  "content": {
    "statement": "向量空间封闭于加法和标量乘法",
    "source": { "chapter": 1, "section": 2, "paragraph": 3 }
  },

  "confidence": 0.85,

  "structure": {
    "prerequisites": ["node-010", "node-015"],
    "consequences": ["node-051"],
    "related": ["node-033"]
  },

  "understanding": {
    "status": "superficial | operational | connected | generative",
    "iteration_count": 2,
    "updated_from": ["node-051"]
  },

  "confusions": [
    {
      "type": "terminology | logic | causality | integration | boundary",
      "description": "教材声称'任意矩阵可对角化'，但已知并非所有矩阵都可对角化",
      "triggered_by": "consistency_check",
      "resolved": false,
      "attempted_resolution": "需要查阅后续章节或外部验证",
      "resolution": null
    }
  ],

  "qa_pairs": [
    {
      "id": "qa-node042-001",
      "question_type": "boundary",
      "question": "如果仅保留加法封闭性而去掉标量乘法封闭性，这个集合是否可能是向量空间？",
      "answer": "不是。向量空间定义要求同时满足加法和标量乘法封闭性。仅满足加法的集合是加法群（additive group），但缺少标量乘法封闭性意味着它不满足向量空间的完整公理体系。反例：考虑整数集 Z 对加法封闭，但对标量乘法（如实数乘法）不封闭——0.5 × 1 = 0.5 不在 Z 中。",
      "understanding_level": "connected",
      "bloom_level": 4,
      "confidence": 0.85,
      "iteration": 1,
      "related_nodes": ["node-010", "node-015"],
      "created_at_step": "3-self-qa",
      "updated_at_step": null
    },
    {
      "id": "qa-node042-002",
      "question_type": "compression",
      "question": "用一句话总结向量空间的本质特征。",
      "answer": "向量空间是一个对加法和标量乘法封闭的集合，使得其中的元素可以像几何向量一样进行线性组合。",
      "understanding_level": "operational",
      "bloom_level": 2,
      "confidence": 0.9,
      "iteration": 1,
      "related_nodes": [],
      "created_at_step": "3-self-qa",
      "updated_at_step": null
    }
  ],
  "qa_summary": {
    "total_questions": 6,
    "question_type_distribution": {
      "factual": 1, "counterfactual": 1, "boundary": 1,
      "transfer": 1, "compression": 1, "elaboration": 1
    },
    "max_bloom_level": 4,
    "avg_confidence": 0.83
  },
  "understanding_test_result": {
    "tested_at_step": "4-understanding-test",
    "final_understanding_level": "connected",
    "score_breakdown": { "coverage": 0.9, "depth": 0.8, "consistency": 0.85 },
    "gaps_identified": ["未测试标量乘法与加法之间的分配律关系"],
    "backtracking_recommended": false,
    "next_action": "建议在 Step 5 一致性检查中验证与 node-010 的逻辑自洽性"
  },

  "meta": {
    "created_at_step": "2-extract",
    "last_modified_step": "6-backtrack",
    "version": 2
  }
}
```

### 5.3 边 Schema

```json
{
  "id": "edge-107",
  "source": "node-042",
  "target": "node-051",
  "type": "prerequisite_of | consequence_of | related_to | contradicts | exemplifies",
  "confidence": 0.9,
  "explanation": "理解特征向量需要先理解向量空间的基本运算"
}
```

### 5.4 理解状态的四级梯度

| 状态 | 含义 | 判断标准 |
|------|------|---------|
| `superficial` | 能复述 | 能用自己的话重述概念 |
| `operational` | 能解释 | 能回答"为什么需要它""它解决什么问题" |
| `connected` | 能关联 | 能识别前置/后置依赖，能与已有知识建立联系 |
| `generative` | 能推导 | 能在未见过的情境中应用，能预测边界外的行为 |

### 5.5 困惑的五种类型

| 类型 | 含义 | 检测 Prompt 方向 |
|------|------|-----------------|
| `terminology` | 术语未定义或定义模糊 | "文中有哪些术语没有明确定义？" |
| `logic` | 两个结论似乎矛盾 | "文中哪些结论在特定条件下可能冲突？" |
| `causality` | 论证步骤有跳跃 | "从 A 到 B 的推理链条完整吗？缺了什么？" |
| `integration` | 概念间关系不清晰 | "这个概念和本章其他概念有何关系？" |
| `boundary` | 结论的适用范围不明确 | "这个结论在什么条件下不成立？" |

---

## 6. 认知处理 Pipeline

### 6.1 Pipeline 总览

```
教材章节输入
      ↓
┌─────────────────────────┐
│ Step 1: Pre-read         │  领域分类 + 教材质量评估 + 策略参数选择
│         Classifier       │
├─────────────────────────┤
│ Step 2: Read & Parse     │  分段提取命题 + 识别显式依赖
│         Extractor        │
├─────────────────────────┤
│ Step 3: Self-Q&A         │  六类问题生成 + 质量过滤 + 自答
│         Generator        │
├─────────────────────────┤
│ Step 4: Understanding    │  验证理解质量 + 理解评分 + 回溯推荐
│         Test             │
├─────────────────────────┤
│ Step 5: Consistency      │  跨节点逻辑矛盾 / 论证跳跃 / 隐含假设
│         Checker          │
├─────────────────────────┤
│ Step 6: Graph            │  命题 + 关系 → 节点 + 边
│         Builder          │
├─────────────────────────┤
│ Step 7: Backtracking     │  根据 Understanding Test 推荐回溯更新旧节点
│         Engine           │
└─────────────────────────┘
      ↓
知识图 + 学习过程日志 + 理解测试报告
```

### 6.2 各步骤详解

#### Step 1: Pre-read Classifier

**输入**：原始教材文本
**输出**：

```json
{
  "domain": "mathematics",
  "domain_confidence": 0.9,
  "textbook_quality": {
    "explicitness": 4,
    "logical_flow": 3,
    "missing_prerequisites": ["线性方程组求解"],
    "potential_oversimplifications": [
      { "claim": "所有矩阵可对角化", "caveat": "实际仅可对角化矩阵" }
    ],
    "implicit_assumptions": ["假设读者已理解向量空间公理"]
  },
  "strategy_parameters": {
    "primary_learning_mode": "deductive_verification",
    "question_focus": ["boundary_conditions", "counterexamples"],
    "consistency_check_mode": "logical"
  }
}
```

#### Step 2: Read & Parse Extractor

**输入**：教材文本 + 策略参数
**处理**：按段落/节分段，提取每个命题
**输出**：命题列表，每个命题包含：
- 原文陈述
- 出处定位
- 显式的前置引用
- 初始置信度

**自评**：提取完整性估计（"我可能遗漏了什么？"）

#### Step 3: Self-Q&A Generator（六类问题体系）

**定位**：Pipeline 的核心认知处理步骤。Agent 对每个知识节点生成六类互补问题并自答，从不同角度探测理解的深度和边界。

**输入**：命题列表（Step 2 输出）+ 策略参数（Step 1 输出）

##### 3.1 六类问题定义

| # | 问题类型 | 英文 | 核心问题模板 | 认知目标 |
|---|---------|------|-------------|---------|
| 1 | **事实性** | Factual | "X 是什么？定义是什么？核心原理是什么？" | 验证知识记忆与复述 |
| 2 | **反事实** | Counterfactual | "如果条件/前提变动，会发生什么？去掉假设 A 后结论还成立吗？" | 探测因果依赖，区分必要条件与充分条件 |
| 3 | **边界** | Boundary | "结论在什么条件下成立？在什么条件下不成立？适用范围边界在哪？" | 精确定义知识的有效域 |
| 4 | **迁移** | Transfer | "这个概念可以映射到其他什么情境？与另一个领域的概念有何相似/不同？" | 建立跨概念连接，为类比推理打基础 |
| 5 | **压缩** | Compression | "用一句话/30 字以内总结核心是什么？最精简的表述是什么？" | 检验是否抓住本质而非记住细节 |
| 6 | **展开** | Elaboration | "请给出详细推导/具体实例/步骤分解。从基本定义推导到结论。" | 检验是否能从第一原理重建论证 |

**六类问题的互补关系**：

```
          事实性（是什么）
              ↓
    压缩 ← → 展开
    （本质）   （细节）
              ↓
    边界 ← → 反事实
  （在哪成立）（如果改变会怎样）
              ↓
          迁移（还像什么）
```

##### 3.2 生成流程

```
对于每个知识节点：

Step 3a: 问题生成
  基于命题内容，生成六类问题各 1 个候选（共 6 个候选问题/节点）
  每类问题的 prompt 不同（见下文 3.3）

Step 3b: 问题质量过滤
  对每个候选问题评分：
    - Bloom 层级（1-6）
    - 可回答性："浅层" vs "深层"
    - 特异性：是否与该节点密切相关（非泛泛而谈）
  通过条件：Bloom ≥ 2 且 特异性 = "高"
  事实性问题的 Bloom 阈值放宽为 ≥ 1（记忆类问题天然层级低）

Step 3c: 自答
  逐题回答
  每个回答必须包含：
    - 答案正文
    - 引用的原文依据或推理路径
    - 自评置信度（0-1）

Step 3d: 理解层级标注
  根据六类问题的回答质量，标注该节点的暂定理解层级：
    superficial | operational | connected | generative
  （此标注为暂定，Step 4 Understanding Test 会最终确认）
```

##### 3.3 六类问题的 Prompt 设计方向

| 类型 | Prompt 核心指令 | 示例输出（以"向量空间"为例） |
|------|----------------|---------------------------|
| 事实性 | "请基于以下命题，生成一个直接检验知识记忆的问题。问题应该是'是什么/定义是什么/核心原理是什么'类型。" | "向量空间的八条公理分别是什么？" |
| 反事实 | "请生成一个反事实问题：改变或移除命题中的一个前提条件，询问结论是否仍然成立。" | "如果去掉标量乘法分配律 a(u+v)=au+av 这条公理，仅保留其余七条，集合是否仍然是向量空间？" |
| 边界 | "请生成一个边界探测问题：询问这个结论在什么极端/退化/边界条件下成立或不成立。" | "零向量空间 {0} 是否满足向量空间的所有公理？它是维度最小的向量空间吗？" |
| 迁移 | "请生成一个类比迁移问题：将这个概念映射到一个不同的数学结构或现实情境中。" | "向量空间的公理体系与群的公理体系有何对应关系？向量空间是加了什么结构的群？" |
| 压缩 | "请用一个不超过 30 字的句子总结这个命题的核心含义。然后检查这个总结是否丢失了关键信息。" | "向量空间 = 集合 + 线性运算 + 八条公理保证运算自洽。" |
| 展开 | "请从最基础的定义出发，逐步推导或构造一个具体实例来说明这个命题。" | "以 R² 平面为例，逐一验证八条公理成立：(1) 加法封闭......(8) 标量乘法单位元......" |

##### 3.4 输出结构

每个知识节点的 Q&A 输出：

```json
{
  "node_id": "node-042",
  "qa_pairs": [
    {
      "id": "qa-node042-001",
      "question_type": "boundary",
      "question": "零向量空间 {0} 是否满足向量空间所有公理？",
      "answer": "是。逐一验证...",
      "answer_rationale": "引用公理定义+逐条检验",
      "understanding_level": "connected",
      "bloom_level": 4,
      "confidence": 0.85,
      "iteration": 1,
      "related_nodes": ["node-010"],
      "created_at_step": "3-self-qa",
      "updated_at_step": null
    }
    // ... 其余 5 类问题
  ],
  "qa_summary": {
    "total_questions": 6,
    "question_type_distribution": {
      "factual": 1, "counterfactual": 1, "boundary": 1,
      "transfer": 1, "compression": 1, "elaboration": 1
    },
    "max_bloom_level": 4,
    "avg_confidence": 0.83,
    "provisional_understanding_level": "connected"
  }
}
```

##### 3.5 迭代更新机制

当后续章节产生新理解时，Step 3 的输出可以被回溯更新：

- `iteration` 字段递增
- `updated_at_step` 记录触发更新的步骤
- 不覆盖原始 Q&A，而是新增 `qa_pairs` 条目（旧条目保留在日志中）
- 更新触发源：Step 4 Understanding Test 回溯推荐 或 Step 7 Backtracking Engine

#### Step 4: Understanding Test（理解验证关卡）

**定位**：Step 3 与 Step 5 之间的质量关卡。不产生新知识，只验证 Step 3 产出的理解质量是否达标。理解测试不通过 → 标记回溯，不流入后续步骤。

##### 4.1 设计原则

1. **独立性**：Understanding Test 只评价，不修改 Step 3 产出。所有修改建议写入报告，由 Step 7 执行。
2. **多维度评分**：单一分数不可靠。至少从覆盖度、深度、自洽性三个维度打分。
3. **阈值驱动**：每个维度有最低通过线。不达标的节点标记为"需回溯"。
4. **可追溯**：每条扣分必须有明确的理由（哪个问题没覆盖、哪个推理有跳跃）。

##### 4.2 验证流程

```
输入：Step 3 产出的全部 Q&A 对 + 原始命题列表

┌─────────────────────────────────────────┐
│ Sub-step 4a: Coverage Check             │
│   检查 Step 3 的 Q&A 是否覆盖了 Step 2  │
│   提取的全部命题                         │
│   输出：每个命题的覆盖状态               │
│         covered / partially / missed     │
├─────────────────────────────────────────┤
│ Sub-step 4b: Depth Challenge            │
│   对每个节点，生成 3 个对抗性测试问题：   │
│     - 一个反事实挑战                      │
│     - 一个边界挑战                        │
│     - 一个跨概念综合挑战                  │
│   这些问题 Step 3 没有问过               │
│   要求 Agent 现场回答                    │
│   评估回答质量 → 判定真实理解层级         │
├─────────────────────────────────────────┤
│ Sub-step 4c: Cross-node Consistency      │
│   检查不同节点的 Q&A 回答是否逻辑自洽     │
│   例：node-042 说"A 是 B 的必要条件"     │
│        node-051 说"B 独立于 A"           │
│   → 标记为矛盾，需回溯修正               │
├─────────────────────────────────────────┤
│ Sub-step 4d: Scoring & Classification    │
│   综合 4a/4b/4c 结果                     │
│   为每个节点评定最终理解层级              │
│   生成回溯推荐列表                       │
└─────────────────────────────────────────┘
      ↓
理解测试报告
```

##### 4.3 理解层级评分标准

| 层级 | 评分条件（全部满足） | 典型得分阈值 |
|------|--------------------|------------|
| `superficial` | 事实性问题正确 + 压缩问题可接受 | coverage ≥ 0.6 |
| `operational` | 以上 + 展开问题正确（能从定义推导） | coverage ≥ 0.7, depth ≥ 0.5 |
| `connected` | 以上 + 边界问题正确 + 迁移问题合理 | coverage ≥ 0.8, depth ≥ 0.7 |
| `generative` | 以上 + 反事实问题正确 + Depth Challenge 全部通过 | coverage ≥ 0.9, depth ≥ 0.85 |

##### 4.4 输出结构

```json
{
  "step": "4-understanding-test",
  "timestamp": "2026-06-10T12:00:05Z",
  "node_results": [
    {
      "node_id": "node-042",
      "coverage": { "status": "covered", "score": 0.9 },
      "depth_challenge": {
        "passed": 2,
        "failed": 1,
        "failed_question": "如果向量空间定义在有限域上，加法封闭性是否自动蕴含标量乘法封闭性？",
        "failure_reason": "Agent 未考虑有限域的特殊性，默认假设了实数域"
      },
      "cross_node_consistency": { "status": "consistent", "conflicts": [] },
      "final_understanding_level": "connected",
      "score_breakdown": { "coverage": 0.9, "depth": 0.8, "consistency": 0.85 },
      "gaps_identified": [
        "未测试有限域上的向量空间行为",
        "未测试标量乘法与加法之间的分配律关系"
      ],
      "backtracking_recommended": false,
      "next_action": "通过。建议在 Step 5 一致性检查中验证与 node-010 的逻辑自洽性"
    },
    {
      "node_id": "node-015",
      "coverage": { "status": "partial", "score": 0.5 },
      "depth_challenge": { "passed": 0, "failed": 3 },
      "cross_node_consistency": {
        "status": "conflict",
        "conflicts": [
          {
            "with_node": "node-042",
            "description": "node-015 声称线性相关定义不依赖基的选择，但 node-042 隐含假设了标准基"
          }
        ]
      },
      "final_understanding_level": "superficial",
      "score_breakdown": { "coverage": 0.5, "depth": 0.2, "consistency": 0.4 },
      "gaps_identified": [
        "Step 3 仅生成了事实性问题，缺少反事实和边界问题",
        "与 node-042 存在逻辑矛盾"
      ],
      "backtracking_recommended": true,
      "backtracking_reason": "覆盖率不足 + 深度挑战全部失败 + 跨节点矛盾",
      "next_action": "建议回到 Step 3，针对 node-015 重新生成反事实和边界问题，重点解决基选择问题"
    }
  ],
  "summary": {
    "total_nodes": 15,
    "passed": 12,
    "backtracking_recommended": 3,
    "understanding_distribution": {
      "superficial": 2, "operational": 5, "connected": 5, "generative": 3
    }
  }
}
```

##### 4.5 回溯推荐机制

Understanding Test 不执行回溯（由 Step 7 执行），但输出精确的回溯推荐：

| 回溯原因 | 推荐行动 | 目标步骤 |
|---------|---------|---------|
| 覆盖率不足 | 该节点的 Step 2 命题提取可能遗漏，建议重新提取 | Step 2 |
| 深度挑战失败 | Q&A 质量不够，建议重新生成反事实/边界问题 | Step 3 |
| 跨节点矛盾 | 矛盾双方的节点理解不准确，建议两个节点都重新处理 | Step 3 + Step 5 |
| 多种问题同时存在 | 标记为"高优先级回溯"，暂停该节点相关的下游处理 | 全流程 |

---

#### Step 5: Consistency Checker

**输入**：命题列表 + Q&A 结果（含 Step 4 的 depth challenge 结果）+ 已有知识图（如有）
**检测项**：

- 逻辑矛盾：两个命题在什么条件下冲突？
- 论证跳跃：A→B 的推理链是否完整？
- 隐含假设：命题依赖了哪些未声明的假设？
- 遗漏：本章应有但未涉及的知识点？
- 术语模糊：定义是否精确、无歧义？

**输出**：问题列表，每个问题标记类型和严重程度

#### Step 6: Graph Builder

**输入**：命题列表 + Q&A 结果（含 Step 4 通过验证的节点）+ Step 5 一致性检测结果
**处理**：

- 每个命题 → 一个节点
- 显式依赖 → `prerequisite_of` / `consequence_of` 边
- Q&A 揭示的关系 → `related_to` 边
- Step 5 一致性检测的矛盾 → `contradicts` 边

**自评**：结构完整性（孤立节点比例、最大连通分量占比）

#### Step 7: Backtracking Engine

**触发条件**：
1. Step 4 Understanding Test 输出 `backtracking_recommended: true`
2. 或 Step 5 一致性检测发现旧节点的信息不完整或不准确（多章节场景）

**处理**：

- 读取 Step 4 / Step 5 的回溯推荐
- 定位受影响节点
- 根据推荐的目标步骤重新处理（回 Step 2 或 Step 3）
- 生成更新（非覆盖，而是新版本）
- 记录 diff
- 更新 `understanding.updated_from` 字段

### 6.3 一步一自评

每个 Step 的输出都包含自评元数据：

| Step | 自评维度 |
|------|---------|
| 1. Classifier | 领域分类置信度（0-1） |
| 2. Extractor | 提取完整性估计 + 可能遗漏的内容 |
| 3. Q&A Generator | 六类问题分布 + Bloom 层级分布 + 回答置信度均值 + 暂定理解层级 |
| 4. Understanding Test | 覆盖度/深度/一致性三维得分 + 通过率 + 回溯推荐比例 |
| 5. Consistency Checker | 检测项数量 + 假阳性风险自评 |
| 6. Graph Builder | 孤立节点比例 + 语义密度 |
| 7. Backtracking | 更新幅度 + 预期改进程度 |

---

## 7. 评估体系

### 7.1 评估金字塔

```
         ┌──────────┐
         │ 外部评估  │  ← 人工标注 ground truth 对比
         │          │     应用题测试
         ├──────────┤
         │ 交叉评估  │  ← 与其他方法（baseline）对比
         │          │
         ├──────────┤
         │ 内在评估  │  ← Pipeline 每步自评
         │          │     一致性、完整性指标
         └──────────┘
```

### 7.2 Phase 1 评估维度

| 维度 | 指标 | 测量方式 |
|------|------|---------|
| 知识覆盖度 | 召回率 vs 人工标注 ground truth | 节点数 / 总知识点数 |
| 问题多样性 | 六类问题的分布均匀度（任意类型占比 < 10% 为不合格） | 自动统计 qa_summary.type_distribution |
| 理解深度 | 深层问题占比（Bloom ≥ 3） + Understanding Test 通过率 | 自动 + 人工抽样校准 |
| 概念关联 | 关系边数量 vs baseline | 对比知识图的边密度 |
| 困惑发现 | 检测到的困惑数量与类型分布 | 困惑数组统计 |
| 自洽性 | 跨节点逻辑矛盾数量 | Step 5 Consistency Checker + Step 4 跨节点一致性 |
| 回溯有效性 | 更新后节点准确率变化 + 回溯推荐是否被验证有效 | 人工对比新旧节点 |
| Understanding Test 精度 | Step 4 的评分与人工评分的 Spearman 相关性 | 人工标注 20% 样本对比 |

### 7.3 Baseline 定义

**Single-pass Baseline**：

```
Prompt: "请详细总结本章的所有知识点，列出它们之间的关系，以 JSON 格式输出。"
```

在与 Agent 相同的模型上执行，用相同的 JSON schema 约束输出。

**对比维度**：
- 知识点数量
- 关系数量与精度
- 问题质量（对 baseline 的输出，额外请求它生成自测问题）

### 7.4 人工评估标注标准

**问题深度判定**：

| 层级 | 判定标准 | 示例 |
|------|---------|------|
| 浅层 | 答案可在原文中直接找到 | "向量加法的交换律是什么？" |
| 中层 | 需要用自己的话重组，但不需要推理 | "请用自己的话解释向量空间的定义" |
| 深层 | 需要推理、跨段落综合、或边界探测 | "如果仅保留加法和标量乘法之一封闭，它还是向量空间吗？" |

---

## 8. 分阶段路线图

### 8.1 Phase 1：知识层（当前阶段）

**目标**：验证 H1（多轮处理优于单次摘要）

**范围**：
- 单一领域（数学/计算机科学基础）
- 单一章节 → 知识图
- Pipeline Step 1-5（Step 6 回溯暂不做）
- 学习日志完整记录
- Baseline 对比评估

**不做**：
- 多章节
- 回溯更新
- 技能层
- 认知模型层
- 多领域泛化
- 任何 UI/API/存储层

### 8.2 Phase 2：技能层（中期）

**前置条件**：H1 验证通过

**目标**：验证 H5、H6
- 知识节点 → 可操作化的练习
- 练习 + 反馈循环
- 技能习得对知识理解的逆向强化
- 多领域策略参数化

### 8.3 Phase 3：认知模型层（远期）

**前置条件**：Phase 2 完成

**目标**：验证 H7
- 跨领域类比检测
- 认知模型的显式化
- 迁移学习：新领域学习效率提升

---

## 9. Phase 1 MVP

### 9.1 MVP 精确规格

```
┌─────────────────────────────────────────────┐
│                Phase 1 MVP                   │
├─────────────────────────────────────────────┤
│                                              │
│  输入：                                      │
│    一个领域的教材第一章（≤ 5000 字）          │
│    推荐：线性代数第一章 或 数据结构第一章     │
│                                              │
│  处理：                                      │
│    Pipeline Step 1 → 2 → 3 → 4 → 5 → 6     │
│    （Step 7 回溯在多章节阶段启用）            │
│                                              │
│  输出：                                      │
│    1. knowledge_graph.json                   │
│    2. learning_log.jsonl                     │
│    3. understanding_test_report.json         │
│    4. baseline_comparison.json               │
│                                              │
│  成功标准（全部满足）：                       │
│    ☐ 知识覆盖率 > baseline + 15%             │
│    ☐ 六类问题每类占比 ≥ 10%（无类型缺失）     │
│    ☐ 深层问题（Bloom ≥ 3）占比 > 30%          │
│    ☐ Understanding Test 通过率 > 70%          │
│    ☐ Step 5 一致性检测发现 ≥ 1 个隐含假设     │
│    ☐ 过程可复现（同章跑 3 次结果稳定）         │
│                                              │
│  失败标准（任一触发方法反思）：               │
│    ☐ 任何维度 Agent ≤ baseline               │
│    ☐ 深层问题占比 < 10%                       │
│    ☐ Understanding Test 通过率 < 40%          │
│    ☐ 知识图节点 < 10 个                       │
│                                              │
└─────────────────────────────────────────────┘
```

### 9.2 MVP 技术实现方向

- 使用现有 LLM API（Claude / GPT），不训练任何模型
- Pipeline 为一组精心设计的 prompt chain
- 每步有明确的输入/输出 JSON schema
- 学习日志为 JSONL 格式，每行一个 step 的完整输入输出
- 不引入向量数据库、图数据库等基础设施——JSON 文件足够

### 9.3 MVP 产出物的研究价值

**最重要的产出可能不是知识图，而是学习日志。**

日志用途：
1. **开发阶段**：定位 pipeline 瓶颈（哪个 step 是质量天花板）
2. **分析阶段**：对比成功/失败案例的日志模式差异
3. **未来训练**：如果后续要 fine-tune 专门做深度学习的模型，日志就是训练数据

---

## 10. 设计原则与约束

### 10.1 设计原则

1. **过程优先于产物**
   知识图是副产物。学习过程的完整日志（每一步的 prompt、response、自评）是一等公民。

2. **可观测性优先**
   每个内部状态（理解程度、困惑类型、修正原因）必须可检查、可追踪。

3. **评估内建，非事后**
   每一步都有自评。不自评的步骤不可信任。

4. **可证伪性**
   每个假设都有明确的失败条件。方法有效性可以被反驳。

5. **最小依赖**
   不引入不必要的技术栈。Phase 1 用纯 prompt engineering + JSON 文件。

6. **领域意识**
   不假设所有知识的学习方式相同。策略参数化，支持领域特化。

### 10.2 约束

- **当前只做知识层**。技能层和认知模型层是独立阶段，不在 Phase 1 范围。
- **当前不做"教人"的功能**。Phase 1 只关注 Agent 自身如何学习。
- **当前不做多章节回溯**。先验证单章方法有效。
- **当前不做多领域泛化**。先在一个领域做到极致。

---

## 11. 已知风险与开放问题

### 11.1 已知风险

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| H1 被证伪（多轮不比单次好） | 致命 | 先跑 MVP，尽早发现；如果证伪，分析原因后决定是否调整方法或放弃 |
| 自问自答质量受限于 LLM 先验知识 | 高 | Question Quality Filter + 人工校准 + 考虑引入外部知识源 |
| Prompt chain 过长导致 context 膨胀 | 中 | 每步压缩中间结果；只传递摘要而非完整文本 |
| 评估标准主观性强 | 中 | 多评估者标注 + 标注标准文档 + inter-rater reliability 检查 |
| 知识图规模膨胀（节点数接近原文句子数） | 低 | 设置节点粒度标准 + 合并冗余节点 |

### 11.2 开放问题

1. **问题质量是否能仅靠 prompt engineering 保证？** 如果 Question Quality Filter 本身也不可靠，是否需要外部验证器？

2. **困惑的"解决"机制是什么？** 当 Agent 检测到困惑（如教材可能 oversimplify），它如何解决？是标记"待验证"还是主动搜索外部信息？

3. **知识图的稀疏性 vs 完备性**：是否应该主动丢弃低价值节点以保持图的可操作性？丢弃标准是什么？

4. **领域分类的粒度**：数学内部（线性代数 vs 概率论）是否需要不同的策略参数？还是仅在数学/历史/编程这种大粒度上区分？

5. **回溯更新的触发条件**：什么程度的"不一致"才触发回溯？阈值如何设定？

6. **人类学习者的角色**：未来是否引入人类反馈（如标注 Agent 的理解是否正确）？还是追求完全自动化？

---

## 12. 附录：关键概念定义

### 12.1 知识（Knowledge）
"知道什么"。陈述性事实、概念及其关系。可表示为命题和图结构。

### 12.2 理解（Understanding）
"为什么是这样"。不是二值的，而是渐进的（肤浅 → 操作 → 关联 → 生成）。标志是能在新情境中正确应用知识。

### 12.3 技能（Skill）
"能做什么"。条件-动作规则的集合，通过练习和反馈信号强化。

### 12.4 认知模型（Mental Model）
"如何看世界"。对领域本质结构的抽象直觉，支持类比迁移和反事实推理。

### 12.5 困惑（Confusion）
"知道自己不知道什么"。不是理解的缺失，而是对理解边界和断层位置的精确感知。元认知的核心。

### 12.6 学习（Learning）
可观测的认知状态变化。包括：知识覆盖度增加、理解深度递进、困惑的发现与解决、知识结构的重组。

---

> **相关文档**：
> - [RUNTIME_ARCHITECTURE.md](RUNTIME_ARCHITECTURE.md) — 运行时架构（Agent 如何存在）
> - [KNOWLEDGE_REPRESENTATION.md](KNOWLEDGE_REPRESENTATION.md) — 统一知识表示规范（知识如何表示）
>
> **下一步**：
> 1. 确定 MVP 教材章节
> 2. 编写 `prompts/` 下的 prompt 模板
> 3. 实现 `agent/` 核心代码（Week 1-4 路线图见 RUNTIME_ARCHITECTURE.md §9）
>
> 本文档随项目进展持续更新。
