# Knowledge Representation Specification v1.0

> 版本：v1.0
> 状态：Phase 1 生效
> 最后更新：2026-06-10
> 作者：Chief Knowledge Architect
> 依赖：STARTUP.md v1.1

---

## 目录

1. [设计原则](#1-设计原则)
2. [核心实体](#2-核心实体)
3. [实体关系](#3-实体关系)
4. [状态模型](#4-状态模型)
5. [Ground Truth Schema](#5-ground-truth-schema)
6. [MVP 阶段保留内容](#6-mvp-阶段保留内容)
7. [MVP 阶段删除推迟内容](#7-mvp-阶段删除推迟内容)
8. [Phase 2 / Phase 3 扩展能力分析](#8-phase-2--phase-3-扩展能力分析)
9. [附录：关键设计决策](#9-附录关键设计决策)

---

## 1. 设计原则

### 原则 1：Concept 是唯一原子

一切——知识、技能、认知模型、误区——都是 Concept 上的不同关系配置。不引入 Concept 之外的原子实体类型。

**为什么**：如果 Knowledge / Skill / Mental Model 是三种独立对象，跨层次推理需要三套同步逻辑。统一为 Concept + Relations 后，Phase 1→2→3 的升级是"加关系类型"而非"重构数据结构"。

### 原则 2：关系比节点更重要

一个 Concept 的"含义"主要来自它与其他 Concept 的关系，而非它自身的文本定义。图的结构承载语义。

**推论**：评估 Agent 理解质量时，错误的关系（连接了错误的前置依赖）比遗漏的定义更严重。

### 原则 3：双轴状态

每个 Concept 同时有**过程状态**（在 Pipeline 的哪个阶段）和**理解深度**（理解到什么程度）。两者正交。

```
过程状态：UNPROCESSED → EXTRACTED → QA_GENERATED → VALIDATED → INTEGRATED
理解深度：SUPERFICIAL → OPERATIONAL → CONNECTED → GENERATIVE
```

一个概念可以处于 `VALIDATED` 过程状态但理解深度仅为 `SUPERFICIAL`（勉强通过测试）。

### 原则 4：渐进标注

Ground Truth 支持最小标注（只有 id + name + short_def + must_understand），也支持完整标注（所有字段）。Agent 产出的知识图和 Ground Truth 结构一致，便于直接对比。

### 原则 5：阶段可扩展

Phase 1 使用 Property Graph（节点 + 二元边）。Phase 2/3 可增加新的 Relation 类型和 Hyperedge 支持，不破坏 Phase 1 的数据。

---

## 2. 核心实体

### 2.1 Concept（概念）

知识的最小单元。一个 Concept 是"关于某件事的一个可独立讨论的认知单元"。

**粒度标准**：一个 Concept 应该足够大以至于值得单独测试理解，足够小以至于可以用一个 `must_understand` 条目表达。如果某件事需要 3 个 `must_understand` 条目才能说清，它可能是 3 个 Concept。

**类型**：

| 类型 | 含义 | 示例 |
|------|------|------|
| `primary` | 核心概念，知识体系骨干 | "向量空间""闭包""递归" |
| `derived` | 从核心概念推导出的概念 | "子空间""柯里化""尾递归" |
| `auxiliary` | 支撑性概念（术语、工具） | "标量""语法糖""调用栈" |

### 2.2 Proposition（命题）

附属于 Concept 的陈述句。一个 Concept 可以有多个 Proposition（从不同角度描述它）。Proposition 是"知识"的载体。

```
Concept "向量空间"
  ├── Proposition: "向量空间是一个对加法和标量乘法封闭的集合"
  ├── Proposition: "向量空间必须满足八条公理"
  └── Proposition: "向量空间是线性代数的基本研究对象"
```

### 2.3 Procedure（程序）

附属于 Concept 的操作序列。Procedure 是"技能"的载体。**Phase 2 启用。**

```
Concept "变量声明"
  └── Procedure:
        steps: ["确定类型", "选择名称", "赋予初始值"]
        conditions: ["在函数体内", "名称未冲突"]
```

### 2.4 Relation（关系）

两个 Concept 之间的有类型连接。Relation 是知识结构的载体。

### 2.5 Misconception（误区）

**不是独立的实体类型。** Misconception 是 Agent 图与 Ground Truth 图之间的**差异**——Agent 的某条 Proposition 与 Ground Truth 矛盾，或者 Agent 的某条 Relation 指向了错误的目标。

这意味着检测 Misconception 的方法是**图对比**（Agent 图 vs Ground Truth 图），而不是维护一个独立的"误区列表"。

---

## 3. 实体关系

```
Concept ─── has_proposition ──→ Proposition
Concept ─── has_procedure ────→ Procedure          (Phase 2)
Concept ─── has_example ──────→ Example
Concept ─── has_test ─────────→ TestQuestion

Concept ─── depends_on ───────→ Concept            [strict | soft | pedagogical]
Concept ─── analogous_to ─────→ Concept
Concept ─── generalizes ──────→ Concept
Concept ─── specializes ──────→ Concept
Concept ─── contradicts ──────→ Concept            (Ground Truth 中标注已知矛盾)
Concept ─── exemplifies ──────→ Concept
Concept ─── composes ─────────→ Concept            (A 是 B 的组成部分)

Concept ─── process_state ────→ ProcessState       [enum]
Concept ─── understanding ────→ UnderstandingDepth  [enum]
```

### 关系类型详解

| 关系类型 | 含义 | 示例 | Phase |
|---------|------|------|-------|
| `depends_on (strict)` | 逻辑必须：不理解 A 则不可能理解 B | 特征向量 depends_on 向量空间 | 1 |
| `depends_on (soft)` | 推荐但不必须 | 泛型 depends_on 接口 | 2 |
| `depends_on (pedagogical)` | 教学顺序依赖，非逻辑依赖 | 数组 depends_on 变量 | 2 |
| `analogous_to` | 结构相似但领域不同 | 闭包 analogous_to 对象 | 2 |
| `generalizes` | A 是 B 的泛化 | 向量空间 generalizes 欧几里得空间 | 1 |
| `specializes` | A 是 B 的特化 | 对角矩阵 specializes 方阵 | 1 |
| `contradicts` | A 和 B 不能同时成立 | — | 1 |
| `exemplifies` | A 是 B 的实例/例子 | R² exemplifies 向量空间 | 1 |
| `composes` | A 是 B 的组成部分 | 公理 composes 向量空间定义 | 2 |

---

## 4. 状态模型

### 4.1 过程状态（Process State）

```
UNPROCESSED → EXTRACTED → QA_GENERATED → VALIDATED → INTEGRATED
                                                ↘ FLAGGED → INTEGRATED (低置信度)
```

| 状态 | 含义 | 进入条件 |
|------|------|---------|
| `UNPROCESSED` | 尚未被任何 Step 处理 | 初始状态 |
| `EXTRACTED` | Step 2 已提取命题 | Step 2 输出包含该概念 |
| `QA_GENERATED` | Step 3 已生成 Q&A，暂定深度已标记 | Step 3 完成 |
| `VALIDATED` | Step 4 理解测试通过 | Step 4 score ≥ 阈值 |
| `FLAGGED` | Step 4 重试 2 次仍未通过 | Step 4 score < 阈值且重试耗尽 |
| `INTEGRATED` | 已加入知识图 | Step 6 完成 |

**FLAGGED 的含义**：重试 2 次仍无法通过 Step 4 的概念。不阻塞 Pipeline，但标记为低置信度，入图时保留 `flagged: true`。这是"已知的未知"——比默默标记为 SUPERFICIAL 更诚实。

### 4.2 理解深度（Understanding Depth）

```
SUPERFICIAL → OPERATIONAL → CONNECTED → GENERATIVE
```

| 深度 | 标志 | Step 4 通过条件 |
|------|------|---------------|
| `SUPERFICIAL` | 能复述定义 | 事实性问题正确 |
| `OPERATIONAL` | 能用自己的话解释，能从定义推导 | + 展开问题正确 |
| `CONNECTED` | 能识别前置后置依赖，能做跨概念推理 | + 边界问题正确 + 迁移问题合理 |
| `GENERATIVE` | 能在未见过情境中应用，能预测反事实结果 | + 反事实问题正确 + Depth Challenge 全部通过 |

### 4.3 两个轴线的交互

| | SUPERFICIAL | OPERATIONAL | CONNECTED | GENERATIVE |
|---|---|---|---|---|
| **QA_GENERATED** | ✅ 常见 | ✅ 常见 | ⚠️ 暂定标注可能偏高 | ❌ 几乎不可能 |
| **VALIDATED** | ⚠️ 勉强通过 | ✅ 正常通过 | ✅ 良好通过 | ✅ 优秀通过 |

Step 3 产出的理解深度是**暂定**的（provisional）。Step 4 验证后才成为**确认**的。Step 4 通常会下调理解深度（Agent 自评容易偏高）。

### 4.4 为什么不是 "Unknown → Seen → Remembered → Understood"

原始的六级模型（Unknown → Seen → Remembered → Understood → Connected → Generative）混淆了过程状态和理解深度。"Seen" 和 "Remembered" 对人类学习者有意义，但对 LLM Agent 无意义——只要文本在 context window 里，Agent 就已经 "seen" 和 "remembered" 了。

修正后的双轴模型将这两个维度分离，状态数量从 6 个减少到 5+4=9 个组合，但维度清晰，各司其职。

---

## 5. Ground Truth Schema

### 5.1 顶层结构

```
GroundTruth
├── metadata: { domain, topic, version, author }
├── concepts: [Concept]
├── relations: [Relation]
└── learning_paths: [LearningPath]    (Phase 2)
```

### 5.2 Concept

```json
{
  "id": "var-env",
  "name": "Environment",
  "type": "primary",

  "content": {
    "short_def": "变量名到值的映射表，决定了变量查找的结果",
    "full_def": "Environment 是编程语言运行时中维护变量名到值映射的数据结构。每次函数调用创建新的 Environment，嵌套的 Environment 形成作用域链。"
  },

  "difficulty": 2,

  "dependencies": [
    {
      "concept_id": "var-name-binding",
      "type": "strict",
      "explanation": "理解 Environment 需要先理解变量名如何绑定到值"
    }
  ],

  "must_understand": [
    "Environment 决定了变量查找的结果",
    "同名变量在不同 Environment 中可以指向不同值",
    "嵌套 Environment 形成作用域链，内层可以遮蔽外层"
  ],

  "misconceptions": [
    {
      "id": "mis-env-001",
      "statement": "所有变量都存在同一个全局 Environment 中",
      "correction": "每次函数调用创建新的 Environment，局部变量存在各自的 Environment 中",
      "severity": "critical",
      "source": null
    }
  ],

  "understanding_tests": [
    {
      "id": "test-env-001",
      "type": "factual",
      "question": "什么是 Environment？它在程序执行中起什么作用？",
      "expected_answer": "Environment 是变量名到值的映射表，决定了变量查找的结果。",
      "answer_key_points": [
        "映射表",
        "变量名到值",
        "决定变量查找"
      ],
      "bloom_level": 1,
      "difficulty": 1,
      "tests_misconception": null
    },
    {
      "id": "test-env-002",
      "type": "boundary",
      "question": "如果一个函数内部定义了一个与外层同名的变量，内层的变量查找和外层的变量查找会怎样？这会导致什么问题？",
      "expected_answer": "内层 Environment 中的同名变量会遮蔽外层。变量查找从当前 Environment 开始，沿作用域链向外查找，找到第一个匹配即停止。这可能导致外层同名变量无法在内层被访问。",
      "answer_key_points": [
        "遮蔽",
        "从内向外查找",
        "找到第一个匹配即停止",
        "外层同名变量不可访问"
      ],
      "bloom_level": 4,
      "difficulty": 3,
      "tests_misconception": "mis-env-001"
    }
  ],

  "examples": [
    {
      "id": "ex-env-001",
      "type": "illustrative",
      "content": "在 Python 中，每次函数调用都创建一个新的局部命名空间（local namespace），这就是一个 Environment。全局变量存在 global namespace 中。",
      "demonstrates": [
        "Environment 决定变量查找",
        "同名变量在不同 Environment 中可以指向不同值"
      ]
    }
  ],

  "phase": 1
}
```

### 5.3 Relation

```json
{
  "from": "closure",
  "to": "lexical-scope",
  "type": "depends_on",
  "explanation": "闭包捕获的是词法作用域中的变量，不理解词法作用域就无法理解闭包捕获了什么"
}
```

### 5.4 最小标注

MVP 阶段不需要填满所有字段。一个概念的最小可接受标注：

```json
{
  "id": "var-env",
  "name": "Environment",
  "type": "primary",
  "content": { "short_def": "变量名到值的映射表" },
  "difficulty": 2,
  "dependencies": [],
  "must_understand": [
    "Environment 决定了变量查找的结果"
  ],
  "misconceptions": [],
  "understanding_tests": [],
  "examples": [],
  "phase": 1
}
```

这已经是合法的 Ground Truth 条目。随着项目推进逐步补充。

---

## 6. MVP 阶段保留内容

| 实体/字段 | 用途 | 优先级 |
|----------|------|-------|
| Concept.id, name, type, content | 核心标识 | P0 |
| Concept.difficulty | 未来自适应难度 | P1 |
| Concept.dependencies (type=strict) | 知识图核心结构 | P0 |
| Concept.must_understand[] | 理解验证基准 | P0 |
| Concept.misconceptions[] | 标注成本高，可先空 | P2 |
| Concept.understanding_tests[] | Step 4 测试生成参考 | P0 |
| Concept.examples[] | 图结构中的示例节点 | P1 |
| Concept.phase | 标识概念所属阶段 | P0 |
| Relation (depends_on, contradicts, exemplifies) | 知识图边 | P0 |
| ProcessState (全过程) | 驱动 Pipeline | P0 |
| UnderstandingDepth | 理解评估输出 | P0 |
| Proposition (附属于 Concept) | Step 2 提取产物 | P0 |

## 7. MVP 阶段删除/推迟内容

| 实体/字段 | 处理 | 理由 |
|----------|------|------|
| Procedure | 推迟到 Phase 2 | 技能层，Phase 1 不涉及 |
| LearningPath | 推迟到 Phase 2 | 需要多章节才能有意义 |
| Hyperedge | 推迟到 Phase 3 | 二元边覆盖 90% 需求 |
| dependencies (type=pedagogical) | 推迟到 Phase 2 | MVP 只做逻辑依赖 |
| Concept.understanding_history[] | 删除 | 无多版本回溯时不需要历史 |
| Forgetting Curve 数据 | 删除 | LLM 无遗忘曲线，此概念不适用 |
| User Model / Mastery State | 删除 | Phase 1 Agent 为自己学习，无用户概念 |
| Concept.iteration_count / version | 推迟到 Phase 1.5 | 单章无回溯更新，每个节点只有一个版本 |

---

## 8. Phase 2 / Phase 3 扩展能力分析

### 8.1 Phase 2 扩展（技能层）

```
Concept 增加:
  ├── has_procedure → Procedure
  │     ├── steps: [string]
  │     ├── conditions: [string]       // 什么情况下使用这个技能
  │     └── practice_tasks: [Task]
  │
  ├── dependencies 增加:
  │     └── type: "pedagogical"        // 教学顺序依赖
  │
  └── LearningPath 使用:
        ├── 根据 dependencies 生成推荐学习顺序
        └── 根据 UnderstandingDepth 动态调整路径
```

**不需要改动 Phase 1 的任何现有字段。** Procedure 是新挂载的 Relation 类型。

### 8.2 Phase 3 扩展（认知模型层）

```
Concept 增加:
  ├── has_analogy → Concept
  ├── has_causal_model → CausalModel
  │     ├── causes: [Concept]
  │     └── effects: [Concept]
  │
Relation 增加:
  └── hyperedge: {
        participants: [Concept],
        role: { concept_id: role_name }
      }
```

**同样不需要改动 Phase 1 的任何现有字段。**

### 8.3 扩展性验证

以下是一个概念从 Phase 1 到 Phase 3 的演化示意：

```
Phase 1:                    Phase 2:                    Phase 3:
"闭包"                      "闭包"                      "闭包"
  ├── Proposition: "..."      ├── Proposition: "..."      ├── Proposition: "..."
  ├── depends_on: Scope       ├── depends_on: Scope       ├── depends_on: Scope
  └── depth: CONNECTED        ├── Procedure: "创建..."    ├── Procedure: "创建..."
                              └── depth: CONNECTED        ├── analogy: "背包"
                                                          ├── causal: "封装状态"
                                                          └── depth: GENERATIVE
```

同一个 Concept，Phase 1/2/3 逐步挂载更多 Relation 类型。**数据向前兼容。**

---

## 9. 附录：关键设计决策

### 决策 1：Concept 是唯一原子

**问题**：Knowledge / Skill / Mental Model / Misconception 是不同对象还是同一对象的不同状态？

**决策**：它们不是不同对象，也不是不同状态。它们是同一核心对象（Concept）上的不同关系配置。

**理由**：
- 如果它们是不同对象，需要三套独立数据结构和同步逻辑
- 统一为 Concept + Relations 允许 Phase 间的无缝升级
- Misconception 是图差异（Agent 图 vs Ground Truth 图），不需要独立实体

### 决策 2：双轴状态模型

**问题**："Unknown → Seen → Remembered → Understood → Connected → Generative" 是否合理？

**决策**：不合理。改为双轴模型——过程状态（Pipeline 进度）和理解深度（理解质量）正交。

**理由**：
- "Seen" 和 "Remembered" 对人类有意义，对 LLM 无意义
- 过程状态驱动 Pipeline，理解深度是评估结果——职责不同
- 双轴允许更细粒度的状态追踪（如 VALIDATED + SUPERFICIAL）

### 决策 3：Property Graph 而非 Tree 或 Hypergraph

**问题**：知识结构应该是 Tree / Graph / Hypergraph？

**决策**：Phase 1 使用 Property Graph（节点 + 二元属性边），Phase 3 预留 Hypergraph 扩展。

**理由**：
- Tree 无法表示循环依赖和多父节点依赖
- 90% 的知识关系是二元的
- Property Graph 实现和调试简单
- Hypergraph 扩展可作为新的 Relation 类型加入，不破坏现有数据

### 决策 4：Ground Truth 不强制记录推导过程

**问题**：Ground Truth 是否应该记录理解过程（推导链）？

**决策**：不强制。`dependencies` 已隐含推导结构。可选的 `LearningPath` 留到 Phase 2。

**理由**：
- 标注推导链的成本远大于收益
- 推导路径可能不唯一
- `dependencies` 图已经是推导链的结构化表示

### 决策 5：渐进标注

**问题**：Ground Truth 是否需要从一开始就完整标注？

**决策**：不需要。支持最小标注（id + name + short_def + must_understand）。

**理由**：
- 允许 Ground Truth 和 Agent 一起演化
- 降低 MVP 启动成本
- 标注工作量可以逐步投入

---

> **相关文档**：
> - [STARTUP.md](STARTUP.md) — 项目启动文档
> - [RUNTIME_ARCHITECTURE.md](RUNTIME_ARCHITECTURE.md) — 运行时架构设计
>
> 本文档随项目进展持续更新。
