# Learning Agent

> **╔══════════════════════════════════════════╗**
> **║     🚧 开发阶段 · 功能未完善 · 持续迭代    ║**
> **╚══════════════════════════════════════════╝**

> 让 AI 不只是回答问题，而是能"理解、演化和生成知识"。

---

## 项目哲学

Learning Agent 关注的核心不是"给出答案"，而是理解**学习本身的过程**。

我们认为：

| 概念 | 含义 |
|------|------|
| **知识** | 知道事实、概念和关系 |
| **理解** | 知道为什么，是渐进式的（肤浅 → 操作 → 关联 → 生成） |
| **技能** | 能做什么，通过实践和反馈强化 |
| **认知模型** | 如何看世界，支持类比与迁移 |
| **困惑** | 知道自己不知道的边界，是元认知的核心 |
| **学习** | 可观测的认知状态变化，包括知识覆盖、理解深度、困惑发现和知识结构重组 |

**核心理念：学习是一种可观测的认知状态变化。** 真正的学习不仅是记忆或做题，而是理解、迭代和关联知识。

---

## 项目目标

构建一个 AI Agent，能够：

- **自主理解知识** — 通过自问自答生成问题，识别知识边界、困惑和潜在误区，迭代更新自己的理解
- **结构化表示知识** — 以带状态的知识图记录概念、依赖关系、理解状态和自测问题，每个节点包含迭代次数、困惑类型、前置/后置依赖
- **评估理解深度** — 使用 Bloom 层级和反事实/边界/迁移问题检测理解深度，对每个知识节点进行理解等级标记（superficial → generative）
- **可追踪的学习日志** — 记录每一步认知处理和自评，支持分析学习策略、发现瓶颈

---

## Pipeline 架构

```
Step 1: 教材预读 ──→ 领域分类 + 策略参数选择
Step 2: 命题提取 ──→ 从原文提取知识点节点
                        │
Step 3→4 逐节点循环 ──→ 每个节点：
    Step 3: 六类问题生成（factual, boundary, counterfactual, transfer, compression, elaboration）+ 自答
    Step 4: 理解验证（覆盖检查 + 深度挑战，≤2次重试）
        通过 → VALIDATED   失败 → FLAGGED（低置信度标记）
                        │
Step 5: 跨节点一致性检查
Step 6: 知识图构建 ──→ knowledge_graph.json
```

每个节点经历双轴状态跟踪：
- **过程状态**：EXTRACTED → QA_GENERATED → VALIDATED/FLAGGED → INTEGRATED
- **理解深度**：SUPERFICIAL → OPERATIONAL → CONNECTED → GENERATIVE

---

## 发展路线

| Phase | 层 | 目标 |
|-------|----|------|
| **Phase 1** | 知识层 | 让 Agent 形成理解 |
| **Phase 2** | 技能层 | 将理解转化为可操作技能 |
| **Phase 3** | 认知模型层 | 形成跨领域迁移能力和创新认知 |

### 长期方向

- **全方位认知引擎** — 多学科知识融合，支持跨领域迁移、类比推理
- **自适应学习路径** — 根据知识图与理解状态动态调整学习计划
- **多模态输入** — 将文本、代码、图像、实验数据整合到认知模型
- **学习科学研究平台** — 可量化理解深度和认知迁移效果，验证学习理论
- **AI+人类协作** — Agent 作为学习助手、导师、思维伙伴，与学习者共建知识图谱

---

## 快速开始

```bash
# 设置 DeepSeek API Key
export DEEPSEEK_API_KEY="your-key-here"

# 运行单章学习
python run.py --chapter data/chapter1.txt

# 输出位于 output/<timestamp>/
```

### 环境要求

- Python 3.12+
- `pip install openai>=1.0`

---

## 项目结构

```
learning-agent/
├── agent/                 # 核心代码
│   ├── runner.py          # Pipeline 主编排
│   ├── state.py           # 状态管理
│   ├── llm_client.py      # DeepSeek API 封装
│   ├── prompt_loader.py   # Prompt 加载与变量替换
│   └── steps/             # 各 Step 实现
├── prompts/               # Prompt 模板（与代码分离）
├── core/                  # 数据模型（Document, Chapter, Section）
├── readers/               # 文件读取器（EPUB等）
├── data/                  # 教材数据
├── output/                # 运行产出
├── docs/                  # 设计文档
└── run.py                 # CLI 入口
```

---

## License

MIT License — 详见 [LICENSE](LICENSE)
