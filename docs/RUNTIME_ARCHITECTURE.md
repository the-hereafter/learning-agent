# Runtime Architecture Specification v1.0

> 版本：v1.0
> 状态：Phase 1 生效
> 最后更新：2026-06-10
> 作者：Lead Engineer
> 依赖：STARTUP.md v1.1

---

## 目录

1. [设计目标](#1-设计目标)
2. [对启动文档的工程修正](#2-对启动文档的工程修正)
3. [Agent 最小运行单元](#3-agent-最小运行单元)
4. [Step 组织方式](#4-step-组织方式)
5. [Prompt 管理体系](#5-prompt-管理体系)
6. [状态管理](#6-状态管理)
7. [Agent Memory](#7-agent-memory)
8. [推荐项目结构](#8-推荐项目结构)
9. [开发路线图](#9-开发路线图)

---

## 1. 设计目标

**将 STARTUP.md 的概念架构转换为最小可运行 Agent。**

原则：
- 能跑 > 完整
- 简单 > 灵活
- 可调试 > 可扩展
- 不做未来三年后的架构设计

---

## 2. 对启动文档的工程修正

在进入运行时设计之前，三处 STARTUP.md 的设计在纸面上合理但在工程上需要修正：

### 修正 1：Step 4 和 Step 5 职责重叠

STARTUP.md 中 Step 4c（跨节点一致性检查）和 Step 5（逻辑矛盾检测）检测的是同一件事。

**修正**：Step 4 退化为**纯单节点验证**（只看每个节点自己的 Q&A 质量）。跨节点一致性全部交给 Step 5。Step 4 不再做 cross-node consistency。

### 修正 2：LLM 调用量优化

一个 5000 字章节约 15-25 个命题，每个节点 6 类问题 + 3 个 Step 4 挑战问题 = 每节点约 15 次独立 LLM 调用。总计 ~300 次调用。

**修正**：使用**批量调用**。一次 LLM 调用生成全部 6 个问题，再一次调用回答全部 6 个问题，将调用数从 ~300 降到 ~80。

### 修正 3：Step 4 内部轻量重试

即使 Phase 1 只有单章、Step 7 被禁用，Step 4 也会产生 `backtracking_recommended: true`。

**修正**：在 Step 4 内部增加轻量重试循环（最多 2 次）。节点未通过 → 直接回 Step 3 重新生成该节点的 Q&A。不等待 Step 7。Step 7 留到多章节时处理跨章回溯。

---

## 3. Agent 最小运行单元

### 3.1 模型选择

不采用"整章原子处理"模型。采用 **Node Batch Pipeline**：

```
Step 1 → Step 2 → [node-001] → Step3→Step4 ┐
                  → [node-002] → Step3→Step4 │
                  → [node-003] → Step3→Step4 ├→ Step5 → Step6 → 输出
                  →    ...                   │
                  → [node-N]   → Step3→Step4 ┘
```

**关键设计**：

| 层级 | 步骤 | 粒度 |
|------|------|------|
| 章节级 | Step 1, Step 2 | 一次性处理整章 |
| **节点级** | **Step 3, Step 4** | **每个节点独立通过循环，最多 2 次重试** |
| 章节级 | Step 5, Step 6 | 所有节点通过后汇总 |

### 3.2 为什么是节点级循环

1. 失败节点不会阻塞成功节点
2. Step 4 的重试循环（≤2 次）是 Phase 1 唯一需要的"回溯"
3. 开发者可以观察每个节点的处理日志，调试粒度更细
4. 单节点失败时只需重跑该节点，不浪费已完成的 LLM 调用

### 3.3 节点级运行伪代码

```
for each node in chapter_nodes:
    attempt = 0
    while attempt < 3:
        qa_result = step3_generate_qa(node)
        test_result = step4_understand_test(node, qa_result)
        if test_result.passed:
            node.qa_pairs = qa_result
            node.understanding = test_result.final_level
            node.process_state = VALIDATED
            break
        attempt += 1
        if attempt == 2:   // 最后一次重试
            node.qa_pairs = qa_result
            node.understanding = "superficial"
            node.process_state = FLAGGED
            node.flagged_for_review = True
```

---

## 4. Step 组织方式

### 4.1 方案对比

| 方案 | 实现复杂度 | Phase 1 适配度 | 最大风险 |
|------|----------|---------------|---------|
| **A. Pipeline** | 最低 | ✅ 章节级线性流 + 节点级循环 | 不支持复杂回溯（Phase 1 不需要） |
| **B. Graph Workflow** | 高 | ❌ 过度设计 | DAG 引擎 + 调度器 + 依赖解析——至少多 2 周 |
| **C. State Machine** | 中 | ⚠️ 有吸引力但不必要 | 状态转移矩阵的设计和调试成本高于纯 Pipeline |

### 4.2 推荐：Pipeline + 节点状态标记（A + 轻量 C）

不引入独立的 State Machine 框架。在 Pipeline 的每个步骤中，为每个节点维护一个简单的状态标签：

```
节点状态（ProcessState）：
  UNPROCESSED     → Step 2 之前
  EXTRACTED       → Step 2 完成
  QA_GENERATED    → Step 3 完成
  VALIDATED       → Step 4 通过
  FLAGGED         → Step 4 重试 2 次仍未通过
  INTEGRATED      → Step 6 完成
```

这就是一个状态机——但不需要框架，就是一个字符串字段。Pipeline 代码用 `if node.process_state == "QA_GENERATED"` 来决策。

### 4.3 为什么不是 Graph Workflow

Graph Workflow（如 LangGraph、Prefect）的核心价值：
- 条件分支（不同节点走不同路径）
- 动态并行（根据上游结果决定下游）
- 持久化检查点（中断后恢复）

Phase 1 MVP 不需要这些：
- 所有节点走相同的 Step 3→4 路径（无分支）
- 节点级并行可以用 for loop + 批量 API 调用实现（无 DAG）
- 单章处理 < 30 分钟，中断恢复不是必须功能

**如果 Phase 2 引入多章节回溯更新，再考虑 Graph Workflow。**

---

## 5. Prompt 管理体系

### 5.1 目录结构

```
prompts/
├── step1_classifier.md          # Step 1: 领域分类 + 教材质量评估
├── step2_extractor.md           # Step 2: 命题提取
├── step3/
│   ├── factual.md               #   事实性问题生成
│   ├── counterfactual.md        #   反事实问题生成
│   ├── boundary.md              #   边界问题生成
│   ├── transfer.md              #   迁移问题生成
│   ├── compression.md           #   压缩问题生成
│   ├── elaboration.md           #   展开问题生成
│   ├── filter.md                #   问题质量过滤器
│   └── answer.md                #   自答（六类共用）
├── step4/
│   ├── coverage_check.md        #   覆盖度检查
│   ├── depth_challenge.md       #   深度挑战（生成 + 评估合并）
│   └── score.md                 #   评分 + 层级判定
├── step5_consistency.md         # Step 5: 跨节点一致性检查
└── step6_graph.md               # Step 6: 图构建
```

### 5.2 命名约定

`step<N>_<purpose>.md`

### 5.3 为什么是 Markdown

- 支持 `## Section` 结构（system prompt / few-shot examples / output schema 分节）
- 支持 fenced code blocks 嵌入 JSON schema 示例
- 版本控制友好（纯文本）

### 5.4 每个 Prompt 文件的标准结构

```markdown
# Step 3 — Factual Question Generator

## Role
你是一个学习检测器。你的任务是基于给定的知识点，生成一个事实性问题...

## Input Schema
{ "node_id": "...", "statement": "...", "context": "..." }

## Output Schema
{ "question": "...", "bloom_level": 1, "answerable_from_text": true }

## Few-shot Examples
### Example 1
Input: { "statement": "向量空间封闭于加法和标量乘法" }
Output: { "question": "向量空间的两条封闭性公理分别是什么？", ... }

## Constraints
- 问题必须能从原文直接找到答案
- 不要生成需要推理的问题（这是其他类型问题的工作）
```

### 5.5 变量替换策略

Prompt 文件**不包含**变量插值语法（如 `{{node.statement}}`）。变量替换由 Python 代码在运行时完成（`prompt_template.replace("{{statement}}", node.statement)`），保持 prompt 文件纯文本可读。

---

## 6. 状态管理

### 6.1 Phase 1 必须存在的状态

| 状态 | 来源 | 存储位置 |
|------|------|---------|
| `node_id` | Step 2 生成 | 内存 + JSON |
| `content.statement` | Step 2 | 内存 + JSON |
| `content.source` | Step 2 | 内存 + JSON |
| `process_state` | 运行时更新 | 内存 |
| `qa_pairs[]` | Step 3 | 内存 + JSON |
| `understanding_test_result` | Step 4 | 内存 + JSON |
| `understanding_depth` | Step 4 判定 | 内存 + JSON |
| `confidence` | Step 3 | 内存 + JSON |
| `structure.prerequisites` | Step 6 | 内存 + JSON |
| `structure.consequences` | Step 6 | 内存 + JSON |
| `flagged_for_review` | Step 4 | 内存 + JSON |
| `step_timestamp` | 每步 | JSONL 日志 |

### 6.2 Phase 1 不应该提前加入的状态

| 状态 | 为什么推迟 |
|------|----------|
| `iteration_count` / `version` | Step 7 回溯启用后才需要版本管理 |
| `confusions[]` | 困惑建模需要额外 LLM 调用和分析，Phase 1.5 加入 |
| `updated_from` | 无回溯则无更新来源 |
| `skill_*` 任何字段 | Phase 2 |
| `cognitive_model_*` 任何字段 | Phase 3 |
| `user_profile` / `learner_state` | Agent 为自己学习，无用户 |
| `embedding` / `vector` | 无检索需求 |

### 6.3 存储方式

```
内存（运行时）：
  agent.state = {
    chapter: { raw_text, domain, strategy_params },
    nodes: [ { id, process_state, content, qa_pairs, understanding, ... }, ... ],
    graph: { edges: [...] },
    step_results: { step1: {...}, step2: {...}, ... }
  }

磁盘（持久化）：
  output/<timestamp>/
    knowledge_graph.json           ← agent.state 的最终快照
    learning_log.jsonl             ← 每步完整输入/输出（追加写入）
    understanding_test_report.json ← Step 4 汇总
```

**不引入数据库。** 一个 Python dict + JSON 序列化足够。JSONL 日志追加写入，断电不丢失。

---

## 7. Agent Memory

### 7.1 必须的记忆（Phase 1）

| 记忆类型 | 内容 | 生命周期 | 存储 |
|---------|------|---------|------|
| **工作记忆** | 当前章节全部节点 + Q&A + 测试结果 | 单次运行 | Python dict |
| **过程日志** | 每一步的 prompt / response / 自评 | 跨运行持久 | JSONL 文件 |
| **产出物** | knowledge_graph.json | 跨运行持久 | JSON 文件 |

### 7.2 可以等到 Phase 2 的记忆

| 记忆类型 | 为什么推迟 |
|---------|----------|
| 跨章节知识库 | 单章无跨章需求 |
| 向量索引 / 嵌入检索 | 无检索需求 |
| 学习历史（"之前学过什么"） | 无多章节 |
| 策略参数优化历史 | 纯研究阶段，手动分析日志即可 |
| 对话记忆 | Agent 不自言自语 |

### 7.3 最小实现（≤ 50 行）

```python
class AgentMemory:
    def __init__(self, output_dir):
        self.working = {}          # dict: 当前运行的全部状态
        self.log_path = f"{output_dir}/learning_log.jsonl"

    def log_step(self, step_name, input_data, output_data, self_eval):
        """追加一行到 JSONL"""
        ...

    def save_graph(self):
        """写入 knowledge_graph.json"""
        ...
```

---

## 8. 推荐项目结构

```
learning-agent/
├── docs/
│   ├── STARTUP.md
│   ├── RUNTIME_ARCHITECTURE.md      ← 本文档
│   └── KNOWLEDGE_REPRESENTATION.md
│
├── prompts/                         ← Prompt 模板
│   ├── step1_classifier.md
│   ├── step2_extractor.md
│   ├── step3/
│   │   ├── factual.md
│   │   ├── counterfactual.md
│   │   ├── boundary.md
│   │   ├── transfer.md
│   │   ├── compression.md
│   │   ├── elaboration.md
│   │   ├── filter.md
│   │   └── answer.md
│   ├── step4/
│   │   ├── coverage_check.md
│   │   ├── depth_challenge.md
│   │   └── score.md
│   ├── step5_consistency.md
│   └── step6_graph.md
│
├── agent/                           ← 核心代码
│   ├── __init__.py
│   ├── runner.py                    ← 主编排：执行循环
│   ├── state.py                     ← AgentState + AgentMemory（≤ 80 行）
│   ├── llm_client.py                ← DeepSeek API 封装（≤ 60 行）
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── step1_classifier.py
│   │   ├── step2_extractor.py
│   │   ├── step3_qa.py              ← 六类问题生成 + 过滤 + 自答
│   │   ├── step4_test.py            ← 覆盖检查 + 深度挑战 + 评分
│   │   ├── step5_consistency.py
│   │   └── step6_graph.py
│   └── prompt_loader.py             ← 加载 + 变量替换（≤ 40 行）
│
├── data/                            ← 教材数据
│   └── chapter1.txt
│
├── output/                           ← 运行产出（gitignore）
│   └── <timestamp>/
│       ├── knowledge_graph.json
│       ├── learning_log.jsonl
│       └── understanding_test_report.json
│
├── tests/
│   ├── test_step2_extractor.py
│   ├── test_step3_qa.py
│   └── fixtures/
│       └── sample_propositions.json  ← Ground Truth
│
├── requirements.txt                 ← openai（DeepSeek 兼容）+ 标准库
├── run.py                           ← 入口
└── README.md
```

### 设计理由

| 决定 | 理由 |
|------|------|
| 扁平 `agent/steps/` | 总共 6 个 step，不需要深层嵌套 |
| `prompts/` 与代码分离 | 调 prompt 不改代码，改代码不破坏 prompt |
| `output/<timestamp>/` 每次运行独立 | 不同运行产出不互相覆盖，方便对比 |
| 无 `config/` 目录 | Phase 1 只有一个 API key + 模型名，环境变量足够 |
| 无 `models/` 目录 | 不训练模型 |
| 无 `api/` / `web/` / `db/` | 纯本地 CLI 运行 |

---

## 9. 开发路线图

### 总体策略

- 每周围绕一个**可运行里程碑**
- 先让最简单的流程跑通（哪怕质量差），再逐步改进
- 先做 Step 2→3→4（核心认知处理），Step 1/5/6 是辅助
- 测试数据先行——第一周就写好 Ground Truth

### Week 1：骨架 + Step 2（命题提取）

```
Day 1-2: 项目初始化
  - 创建项目结构
  - pip install openai
  - 写 llm_client.py（DeepSeek API 封装，30 行）
  - 写 prompt_loader.py（读 .md + 变量替换）
  - 跑通 "Hello World"：发送 prompt，收到回复

Day 3-4: Step 2 — 命题提取
  - 写 prompts/step2_extractor.md
  - 写 agent/steps/step2_extractor.py
  - 在 data/chapter1.txt 上运行

Day 5: Ground Truth 标注
  - 手工标注 chapter1 的知识点列表
  - 写 tests/fixtures/sample_propositions.json
  - 对比 Step 2 输出 vs ground truth

Day 6-7: 调试
  - 调整 prompt、增加 few-shot examples
  - 目标：Proposition Recall > 70%
```

### Week 2：Step 3（六类问题生成 + 自答）

```
Day 1-3: 六类问题 prompt 编写
  - 写 prompts/step3/ 下 8 个 prompt 文件
  - 先写 2 类（factual + compression），跑通
  - 再补全其余 4 类

Day 4-5: Step 3 代码
  - 写 agent/steps/step3_qa.py
  - 批量生成（一次调用生成 6 个问题，再一次回答 6 个）
  - 集成 Question Quality Filter

Day 6: 与 Step 2 串联
  - Step 2 输出 → Step 3 输入
  - 端到端：chapter → propositions → Q&A pairs

Day 7: 调试
  - 检查：六类问题每类占比 > 10%
```

### Week 3：Step 4（Understanding Test）+ 节点级循环

```
Day 1-2: Step 4 prompt 编写
  - prompts/step4/coverage_check.md
  - prompts/step4/depth_challenge.md
  - prompts/step4/score.md

Day 3-4: Step 4 代码
  - 写 agent/steps/step4_test.py
  - 实现覆盖检查 → 深度挑战 → 评分

Day 5: 节点级重试循环
  - 在 runner.py 中实现：节点 Step 3→4 循环，最多 2 次重试
  - 状态标记：VALIDATED / FLAGGED

Day 6: 输出 understanding_test_report.json
  - 汇总：通过率、理解层级分布、回溯推荐列表

Day 7: 缓冲
```

### Week 4：Step 5 + Step 6 + Step 1 + Baseline

```
Day 1-2: Step 5（跨节点一致性）
  - 简化版：只检查显式矛盾

Day 3: Step 6（图构建）
  - 命题 → 节点，依赖 → 边
  - 输出 knowledge_graph.json

Day 4: Step 1（Pre-read Classifier）
  - 最简版：判断领域 + 识别显式前置依赖

Day 5: Baseline 对比脚本
  - 单独的 baseline.py
  - 同一个章节 → 单次摘要 prompt → JSON

Day 6-7: 端到端测试 + 修复
  - 完整流程：python run.py --chapter data/chapter1.txt
  - 产出全部输出文件
  - 对比 baseline，填写 H1 验证结果
```

### Week 5：缓冲 + 评估

```
Day 1-2: 换一个章节测试泛化性
Day 3-4: 修复 bug + 改进 prompt
Day 5: 人工评估标注
Day 6-7: 撰写 Phase 1 实验报告（H1 是否通过？）
```

---

## 附录：从启动文档到运行代码的关键简化

| 启动文档设计 | Phase 1 MVP 实现 | 简化原因 |
|------------|----------------|---------|
| Step 4c 跨节点一致性 + Step 5 矛盾检测 | Step 4 只做单节点，跨节点全在 Step 5 | 去重 |
| Step 7 Backtracking Engine | Step 4 内部轻量重试（≤2 次） | 单章无需完整回溯 |
| 完整困惑建模（confusions[]） | Phase 1.5 加入 | 需额外 LLM 调用 |
| 知识节点多版本 | 单版本 | 无回溯则无版本 |
| 评估金字塔（三层） | 内在评估 + 交叉评估 | 外部评估需人工 |

> **相关文档**：
> - [STARTUP.md](STARTUP.md) — 项目启动文档
> - [KNOWLEDGE_REPRESENTATION.md](KNOWLEDGE_REPRESENTATION.md) — 统一知识表示规范
